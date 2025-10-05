from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import SessionLocal, Base, engine
from backend.models import (
    Administrator,
    CoachOrganization,
    Coach,
    CoacheeOrganization,
    Coachee,
    CoachingSession,
    Assignment,
)
from backend.seed import seed_dummy_data
import shutil
import os

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------
app = FastAPI(title="Coach APP Backend")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
seed_dummy_data(SessionLocal)

# ---------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------
# Basic routes
# ---------------------------------------------------------------------
@app.get("/ping")
def ping():
    return {"status": "ok"}

# ---------------------------------------------------------------------
# Login route
# ---------------------------------------------------------------------
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user_models = [
        (Administrator, "admin_email"),
        (CoachOrganization, "coorg_email"),
        (Coach, "coach_email"),
        (CoacheeOrganization, "coe_email"),
        (Coachee, "coachee_email"),
    ]

    for model, email_field in user_models:
        try:
            user = db.query(model).filter_by(**{email_field: email}).first()
            if not user:
                continue
            pw_field = f"{email_field.split('_')[0]}_password"
            if getattr(user, pw_field, None) == password:
                role = model.__name__.lower()
                return {"id": getattr(user, f"{role}_id"), "role": role}
        except Exception as e:
            print(f"Login error for {model.__name__}: {e}")
            continue

    raise HTTPException(status_code=401, detail="Invalid email or password")

# ---------------------------------------------------------------------
# File upload/download
# ---------------------------------------------------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "uploaded"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

# ---------------------------------------------------------------------
# Coach-related endpoints
# ---------------------------------------------------------------------
@app.get("/coach/{coach_id}")
def get_coach_profile(coach_id: int, db: Session = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return {
        "id": coach.coach_id,
        "firstname": coach.coach_firstname,
        "lastname": coach.coach_lastname,
        "email": coach.coach_email,
        "qualifications": coach.coach_qualifications,
        "profile": coach.coach_profile,
        "status": coach.coach_status,
        "photo": coach.coach_photo,
    }

@app.put("/coach/{coach_id}")
def update_coach_profile(
    coach_id: int,
    coach_firstname: str = Form(...),
    coach_lastname: str = Form(...),
    coach_email: str = Form(...),
    coach_qualifications: str = Form(...),
    coach_profile: str = Form(...),
    coach_status: bool = Form(...),
    coach_photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")

    coach.coach_firstname = coach_firstname
    coach.coach_lastname = coach_lastname
    coach.coach_email = coach_email
    coach.coach_qualifications = coach_qualifications
    coach.coach_profile = coach_profile
    coach.coach_status = coach_status

    if coach_photo:
        file_path = os.path.join(UPLOAD_DIR, coach_photo.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(coach_photo.file, buffer)
        coach.coach_photo = file_path

    db.commit()
    db.refresh(coach)
    return {"status": "updated", "coach": coach.coach_firstname}

@app.get("/coach/{coach_id}/coachees")
def get_coachees_for_coach(coach_id: int, db: Session = Depends(get_db)):
    sessions = db.query(CoachingSession).filter(CoachingSession.session_coach == coach_id).all()
    coachee_ids = {s.session_coachee for s in sessions}
    coachees = db.query(Coachee).filter(Coachee.coachee_id.in_(coachee_ids)).all()
    return [
        {
            "id": c.coachee_id,
            "firstname": c.coachee_firstname,
            "lastname": c.coachee_lastname,
            "email": c.coachee_email,
            "status": c.coachee_status,
        }
        for c in coachees
    ]

@app.get("/coach/{coach_id}/sessions")
def get_pending_sessions(coach_id: int, db: Session = Depends(get_db)):
    sessions = (
        db.query(CoachingSession)
        .filter(CoachingSession.session_coach == coach_id)
        .order_by(CoachingSession.session_date.desc())
        .all()
    )
    return [
        {
            "id": s.session_id,
            "date": s.session_date,
            "topic": s.session_topic,
            "status": "completed" if s.session_nextsteps else "pending",
        }
        for s in sessions
    ]

# ---------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("🌱 Seeding database with dummy data...")
    try:
        seed_dummy_data(SessionLocal)
        print("✅ Dummy data seeded successfully!")
    except Exception as e:
        print(f"⚠️ Seeding failed: {e}")
