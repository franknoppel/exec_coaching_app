# backend/app.py
from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional, List
import shutil
import time
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, Base
from backend import models
from backend.seed_data import seed_data

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Executive Coaching App")

# ---- Folders ----
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
UPLOADS_DIR = BASE_DIR.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Session uploads directory
SESSION_UPLOADS_DIR = UPLOADS_DIR / "sessions"
SESSION_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ---- Static file serving ----
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ---- Database dependency ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- Startup: seed data ----
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    seed_data(db)
    db.close()

# ---- Health check ----
@app.get("/healthz")
def healthz():
    return {"ok": True, "status": "connected"}

# ---- Login endpoint ----
@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")
    
    # Check coaches
    coach = db.query(models.Coach).filter(models.Coach.coach_email == email).first()
    if coach and coach.coach_password == password:
        return JSONResponse({
            "role": "coach",
            "id": coach.coach_id,
            "name": f"{coach.coach_firstname} {coach.coach_lastname}",
            "email": coach.coach_email
        })
    
    # Check coachees
    coachee = db.query(models.Coachee).filter(models.Coachee.coachee_email == email).first()
    if coachee and coachee.coachee_password == password:
        return JSONResponse({
            "role": "coachee",
            "id": coachee.coachee_id,
            "name": f"{coachee.coachee_firstname} {coachee.coachee_lastname}",
            "email": coachee.coachee_email
        })
    
    # Check admins
    admin = db.query(models.Administrator).filter(models.Administrator.admin_email == email).first()
    if admin and admin.admin_password == password:
        return JSONResponse({
            "role": "admin",
            "id": admin.admin_id,
            "name": f"{admin.admin_firstname} {admin.admin_lastname}",
            "email": admin.admin_email
        })
    
    # Check coach orgs
    coach_org = db.query(models.CoachOrganization).filter(models.CoachOrganization.coorg_email == email).first()
    if coach_org and coach_org.coorg_password == password:
        return JSONResponse({
            "role": "coach_org",
            "id": coach_org.coorg_id,
            "name": coach_org.coorg_name,
            "email": coach_org.coorg_email
        })
    
    # Check coachee orgs
    coachee_org = db.query(models.CoacheeOrganization).filter(models.CoacheeOrganization.coe_email == email).first()
    if coachee_org and coachee_org.coe_password == password:
        return JSONResponse({
            "role": "coachee_org",
            "id": coachee_org.coe_id,
            "name": coachee_org.coe_name,
            "email": coachee_org.coe_email
        })
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ---- Coach profile ----
@app.get("/coach/{coach_id}")
def get_coach(coach_id: int, db: Session = Depends(get_db)):
    coach = db.query(models.Coach).filter(models.Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    return {
        "id": coach.coach_id,
        "firstname": coach.coach_firstname,
        "lastname": coach.coach_lastname,
        "email": coach.coach_email,
        "qualifications": coach.coach_qualifications,
        "profile": coach.coach_profile,
        "photo": coach.coach_photo,
        "status": coach.coach_status
    }

@app.get("/coach/{coach_id}/coachees")
def get_coach_coachees(coach_id: int, db: Session = Depends(get_db)):
    # Get all sessions for this coach and extract unique coachees
    sessions = db.query(models.CoachingSession).filter(
        models.CoachingSession.session_coach == coach_id
    ).all()
    
    coachee_ids = list(set([s.session_coachee for s in sessions]))
    coachees = db.query(models.Coachee).filter(
        models.Coachee.coachee_id.in_(coachee_ids)
    ).all()
    
    return [{
        "id": c.coachee_id,
        "firstname": c.coachee_firstname,
        "lastname": c.coachee_lastname,
        "email": c.coachee_email,
        "status": c.coachee_status,
        "photo": c.coachee_photo
    } for c in coachees]

# ---- Coachee management ----
@app.get("/coachee/{coachee_id}")
def get_coachee(coachee_id: int, db: Session = Depends(get_db)):
    coachee = db.query(models.Coachee).filter(models.Coachee.coachee_id == coachee_id).first()
    if not coachee:
        raise HTTPException(status_code=404, detail="Coachee not found")
    
    return {
        "id": coachee.coachee_id,
        "firstname": coachee.coachee_firstname,
        "lastname": coachee.coachee_lastname,
        "email": coachee.coachee_email,
        "background": coachee.coachee_background,
        "education": coachee.coachee_edu,
        "challenges": coachee.coachee_challenges,
        "goals": coachee.coachee_goals,
        "status": coachee.coachee_status,
        "photo": coachee.coachee_photo
    }

# ---- Session management ----
@app.get("/coachee/{coachee_id}/sessions")
def get_coachee_sessions(
    coachee_id: int,
    coach_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.CoachingSession).filter(
        models.CoachingSession.session_coachee == coachee_id
    )
    
    if coach_id:
        query = query.filter(models.CoachingSession.session_coach == coach_id)
    
    sessions = query.order_by(models.CoachingSession.session_date.desc()).all()
    
    return [{
        "id": s.session_id,
        "date": s.session_date,
        "topic": s.session_topic,
        "notes": s.session_coachnotes,
        "approach": s.session_coachapproach,
        "goals": s.session_goals,
        "nextsteps": s.session_nextsteps,
        "attachments": s.session_attachments
    } for s in sessions]

@app.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.CoachingSession).filter(
        models.CoachingSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.session_id,
        "date": session.session_date,
        "topic": session.session_topic,
        "notes": session.session_coachnotes,
        "approach": session.session_coachapproach,
        "goals": session.session_goals,
        "nextsteps": session.session_nextsteps,
        "attachments": session.session_attachments,
        "coach_id": session.session_coach,
        "coachee_id": session.session_coachee
    }

@app.post("/session")
async def create_session(
    coach_id: int = Query(...),
    coachee_id: int = Form(...),
    date: str = Form(...),
    topic: str = Form(""),
    notes: str = Form(""),
    approach: str = Form(""),
    goals: str = Form(""),
    nextsteps: str = Form(""),
    attachments: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    # Handle file uploads
    attachment_urls = []
    if attachments:
        for file in attachments:
            if file.filename:
                # Generate unique filename
                timestamp = int(time.time() * 1000)
                ext = Path(file.filename).suffix
                filename = f"{timestamp}_{file.filename}"
                filepath = SESSION_UPLOADS_DIR / filename
                
                # Save file
                with filepath.open("wb") as f:
                    shutil.copyfileobj(file.file, f)
                
                attachment_urls.append(f"/uploads/sessions/{filename}")
    
    attachment_str = ",".join(attachment_urls) if attachment_urls else ""
    
    # Create session
    session = models.CoachingSession(
        session_date=date,
        session_coach=coach_id,
        session_coachee=coachee_id,
        session_topic=topic,
        session_coachnotes=notes,
        session_coachapproach=approach,
        session_goals=goals,
        session_nextsteps=nextsteps,
        session_attachments=attachment_str
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "id": session.session_id,
        "date": session.session_date,
        "topic": session.session_topic,
        "attachments": session.session_attachments
    }

@app.put("/session/{session_id}")
async def update_session(
    session_id: int,
    coach_id: int = Query(...),
    date: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    approach: Optional[str] = Form(None),
    goals: Optional[str] = Form(None),
    nextsteps: Optional[str] = Form(None),
    existing_attachments: Optional[str] = Form(None),
    attachments: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    session = db.query(models.CoachingSession).filter(
        models.CoachingSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update fields if provided
    if date is not None:
        session.session_date = date
    if topic is not None:
        session.session_topic = topic
    if notes is not None:
        session.session_coachnotes = notes
    if approach is not None:
        session.session_coachapproach = approach
    if goals is not None:
        session.session_goals = goals
    if nextsteps is not None:
        session.session_nextsteps = nextsteps
    
    # Handle file uploads
    attachment_urls = []
    
    # Keep existing attachments if provided
    if existing_attachments:
        attachment_urls.extend([a.strip() for a in existing_attachments.split(",") if a.strip()])
    
    # Add new file uploads
    if attachments:
        for file in attachments:
            if file and hasattr(file, 'filename') and file.filename:
                # Generate unique filename
                timestamp = int(time.time() * 1000)
                ext = Path(file.filename).suffix
                filename = f"{timestamp}_{file.filename}"
                filepath = SESSION_UPLOADS_DIR / filename
                
                # Save file
                with filepath.open("wb") as f:
                    shutil.copyfileobj(file.file, f)
                
                attachment_urls.append(f"/uploads/sessions/{filename}")
    
    session.session_attachments = ",".join(attachment_urls) if attachment_urls else ""
    
    db.commit()
    db.refresh(session)
    
    return {
        "id": session.session_id,
        "date": session.session_date,
        "topic": session.session_topic,
        "attachments": session.session_attachments
    }

@app.delete("/session/{session_id}")
def delete_session(
    session_id: int,
    coach_id: int = Query(...),
    db: Session = Depends(get_db)
):
    session = db.query(models.CoachingSession).filter(
        models.CoachingSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    
    return {"status": "deleted", "id": session_id}

# Optional: allow `python backend/app.py` direct run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
