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
        file_path = os.path.join("frontend", "uploads", coach_photo.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(coach_photo.file, buffer)
        coach.coach_photo = f"/frontend/uploads/{coach_photo.filename}"

    db.commit()
    db.refresh(coach)

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
# Coachee endpoints
# ---------------------------------------------------------------------

@app.get("/coachee/{coachee_id}")
def get_coachee_detail(coachee_id: int, db: Session = Depends(get_db)):
    coachee = db.query(Coachee).filter(Coachee.coachee_id == coachee_id).first()
    if not coachee:
        raise HTTPException(status_code=404, detail="Coachee not found")
    return {
        "id": coachee.coachee_id,
        "firstname": coachee.coachee_firstname,
        "lastname": coachee.coachee_lastname,
        "email": coachee.coachee_email,
        "org": coachee.coachee_org,
        "background": coachee.coachee_background,
        "education": coachee.coachee_edu,
        "challenges": coachee.coachee_challenges,
        "goals": coachee.coachee_goals,
        "status": coachee.coachee_status,
    }


@app.get("/coachee/{coachee_id}/sessions")
def get_coachee_sessions(coachee_id: int, db: Session = Depends(get_db)):
    sessions = db.query(CoachingSession).filter(CoachingSession.session_coachee == coachee_id).all()
    return [
        {
            "id": s.session_id,
            "date": s.session_date,
            "topic": s.session_topic,
            "coach_id": s.session_coach,
            "status": "completed" if s.session_nextsteps else "pending",
        }
        for s in sessions
    ]


@app.get("/coachee/{coachee_id}/assignments")
def get_coachee_assignments(coachee_id: int, db: Session = Depends(get_db)):
    assignments = db.query(Assignment).filter(Assignment.assignment_coachee == coachee_id).all()
    return [
        {
            "id": a.assignment_id,
            "description": a.assignment_description,
            "duedate": a.assignment_duedate,
            "status": a.assignment_status,
            "coach": a.assignment_coach,
        }
        for a in assignments
    ]

# ---------------------------------------------------------------------
# Coach - add/remove coachee (simple placeholder logic)
# ---------------------------------------------------------------------

@app.post("/coach/{coach_id}/add_coachee")
def add_coachee(coach_id: int, email: str = Form(...), db: Session = Depends(get_db)):
    coachee = db.query(Coachee).filter(Coachee.coachee_email == email).first()
    if not coachee:
        raise HTTPException(status_code=404, detail="Coachee not found")

    # Example: link via a dummy CoachingSession if not already linked
    existing = (
        db.query(CoachingSession)
        .filter(
            CoachingSession.session_coach == coach_id,
            CoachingSession.session_coachee == coachee.coachee_id,
        )
        .first()
    )
    if existing:
        return {"status": "already_assigned"}

    new_session = CoachingSession(
        session_coach=coach_id,
        session_coachee=coachee.coachee_id,
        session_topic="Initial Coaching Link",
        session_date="2025-10-05 12:00",
        session_goals="Initial assignment to coach",
    )
    db.add(new_session)
    db.commit()
    return {"status": "added", "coachee_id": coachee.coachee_id}


@app.delete("/coach/{coach_id}/remove_coachee/{coachee_id}")
def remove_coachee(coach_id: int, coachee_id: int, db: Session = Depends(get_db)):
    sessions = (
        db.query(CoachingSession)
        .filter(
            CoachingSession.session_coach == coach_id,
            CoachingSession.session_coachee == coachee_id,
        )
        .all()
    )
    for s in sessions:
        db.delete(s)
    db.commit()
    return {"status": "removed", "coachee_id": coachee_id}


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
