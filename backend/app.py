from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from db.base import engine, SessionLocal
from db.models import Base, User, Organization, Membership, CoachProfile, CoacheeProfile,     CoachingSession, TrainingModule, ModuleAssignment, FeedbackForm, FeedbackTemplate, CoachCoachee
from datetime import datetime, date

app = FastAPI(title="Exec Coaching App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"ok": True, "db_ok": True}
    except Exception:
        return {"ok": True, "db_ok": False}

class LoginPayload(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email==payload.email, User.deleted_at.is_(None)).first()
    if not user or not bcrypt.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"user_id": user.user_id, "role": user.role, "first_name": user.first_name, "last_name": user.last_name, "email": user.email}

def get_current_user(db: Session = Depends(get_db), x_user_id: Optional[int] = Header(default=None, alias="X-User-Id")) -> User:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    user = db.get(User, x_user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

# Dev helper: create coach user
class CreateCoachPayload(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@app.post("/dev/create-coach")
def dev_create_coach(payload: CreateCoachPayload, db: Session = Depends(get_db)):
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    exists = db.query(User).filter(User.email==payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(email=payload.email, password_hash=bcrypt.hash(payload.password), role="coach",
                first_name=payload.first_name, last_name=payload.last_name, status="active")
    db.add(user); db.commit()
    return {"ok": True, "user_id": user.user_id}

# Coach profile
class CoachProfileDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    qualifications: Optional[str] = None
    profile: Optional[str] = None

@app.get("/coaches/me")
def get_me(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "coach":
        raise HTTPException(status_code=403, detail="Not a coach")
    cp = db.query(CoachProfile).filter(CoachProfile.user_id == current.user_id).first()
    return {
        "user": {"user_id": current.user_id, "email": current.email, "first_name": current.first_name, "last_name": current.last_name},
        "profile": {"qualifications": cp.qualifications if cp else None, "profile": cp.profile if cp else None},
        "profile_exists": cp is not None
    }

@app.put("/coaches/me/profile")
def upsert_profile(payload: CoachProfileDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "coach":
        raise HTTPException(status_code=403, detail="Not a coach")
    cp = db.query(CoachProfile).filter(CoachProfile.user_id == current.user_id).first()
    if not cp:
        cp = CoachProfile(user_id=current.user_id)
        db.add(cp)
    if payload.first_name is not None: current.first_name = payload.first_name
    if payload.last_name is not None: current.last_name = payload.last_name
    if payload.qualifications is not None: cp.qualifications = payload.qualifications
    if payload.profile is not None: cp.profile = payload.profile
    db.commit()
    return {"ok": True}

# Coachees for coach
@app.get("/coachees/assigned")
def coachees_assigned(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "coach":
        raise HTTPException(status_code=403, detail="Not a coach")
    rows = db.query(CoachCoachee, User, CoacheeProfile)         .join(User, User.user_id == CoachCoachee.coachee_user_id)         .join(CoacheeProfile, CoacheeProfile.user_id == User.user_id)         .filter(CoachCoachee.coach_user_id == current.user_id).all()
    items = []
    for _, u, cp in rows:
        items.append({
            "user_id": u.user_id, "first_name": u.first_name, "last_name": u.last_name, "email": u.email,
            "org_id": cp.org_id, "background": cp.background, "education": cp.education, "challenges": cp.challenges, "goals": cp.goals
        })
    return {"coachees": items}

# Sessions
class SessionDTO(BaseModel):
    session_date: datetime
    coachee_user_id: int
    topic: Optional[str] = None
    coach_notes: Optional[str] = None
    approach: Optional[str] = None
    forward_goals: Optional[str] = None
    next_steps: Optional[str] = None
    status: Optional[str] = "not_started"

@app.get("/sessions")
def list_sessions(status: Optional[str] = None, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "coach":
        raise HTTPException(status_code=403, detail="Not a coach")
    q = db.query(CoachingSession).filter(CoachingSession.coach_user_id == current.user_id)
    if status: q = q.filter(CoachingSession.status == status)
    q = q.order_by(CoachingSession.session_date.asc())
    sessions = [{
        "id": s.id, "session_date": s.session_date.isoformat(), "coachee_user_id": s.coachee_user_id, "topic": s.topic, "status": s.status
    } for s in q.all()]
    return {"sessions": sessions}

@app.post("/sessions")
def create_session(payload: SessionDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "coach":
        raise HTTPException(status_code=403, detail="Not a coach")
    s = CoachingSession(session_date=payload.session_date, coach_user_id=current.user_id, coachee_user_id=payload.coachee_user_id,
                        topic=payload.topic, coach_notes=payload.coach_notes, approach=payload.approach,
                        forward_goals=payload.forward_goals, next_steps=payload.next_steps, status=payload.status or "not_started")
    db.add(s); db.commit()
    return {"id": s.id}

@app.get("/sessions/{sid}")
def get_session(sid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(CoachingSession, sid)
    if not s or s.coach_user_id != current.user_id: raise HTTPException(status_code=404, detail="Not found")
    return {"id": s.id, "session_date": s.session_date.isoformat(), "coachee_user_id": s.coachee_user_id, "topic": s.topic,
            "coach_notes": s.coach_notes, "approach": s.approach, "forward_goals": s.forward_goals, "next_steps": s.next_steps, "status": s.status}

@app.put("/sessions/{sid}")
def update_session(sid: int, payload: SessionDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(CoachingSession, sid)
    if not s or s.coach_user_id != current.user_id: raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); return {"ok": True}

@app.delete("/sessions/{sid}")
def delete_session(sid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(CoachingSession, sid)
    if not s or s.coach_user_id != current.user_id: raise HTTPException(status_code=404, detail="Not found")
    db.delete(s); db.commit(); return {"ok": True}

# Modules & assignments
class ModuleDTO(BaseModel): name: Optional[str] = None; description: Optional[str] = None

@app.get("/modules")
def list_modules(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = db.query(TrainingModule).filter(TrainingModule.deleted_at.is_(None)).order_by(TrainingModule.name.asc()).all()
    return {"modules": [{"id": r.id, "name": r.name, "description": r.description} for r in rows]}

@app.get("/modules/{mid}")
def get_module(mid: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    m = db.get(TrainingModule, mid)
    if not m or m.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    return {"id": m.id, "name": m.name, "description": m.description}

@app.put("/modules/{mid}")
def update_module(mid: int, payload: ModuleDTO, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    m = db.get(TrainingModule, mid)
    if not m or m.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(m, k, v)
    db.commit(); return {"ok": True}

class AssignmentDTO(BaseModel):
    module_id: int; coachee_user_id: int
    coach_user_id: Optional[int] = None; due_date: Optional[date] = None
    status: Optional[str] = "not_started"

@app.get("/assignments/by-coachee/{uid}")
def list_assignments(uid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ModuleAssignment).filter(ModuleAssignment.coachee_user_id==uid, ModuleAssignment.deleted_at.is_(None)).all()
    return {"assignments": [{"id": r.id, "module_id": r.module_id, "coachee_user_id": r.coachee_user_id,
            "coach_user_id": r.coach_user_id, "due_date": r.due_date.isoformat() if r.due_date else None, "status": r.status} for r in rows]}

@app.post("/assignments")
def create_assignment(payload: AssignmentDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = ModuleAssignment(module_id=payload.module_id, coachee_user_id=payload.coachee_user_id,
                         coach_user_id=payload.coach_user_id or current.user_id, due_date=payload.due_date, status=payload.status or "not_started")
    db.add(a); db.commit(); return {"id": a.id}

@app.put("/assignments/{aid}")
def update_assignment(aid: int, payload: AssignmentDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(ModuleAssignment, aid)
    if not a or a.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(a, k, v)
    db.commit(); return {"ok": True}

@app.delete("/assignments/{aid}")
def delete_assignment(aid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(ModuleAssignment, aid)
    if not a or a.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    db.delete(a); db.commit(); return {"ok": True}

# Feedback templates & forms
class FeedbackTemplateDTO(BaseModel): name: Optional[str] = None; description: Optional[str] = None

@app.get("/feedback-templates")
def list_feedback_templates(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = db.query(FeedbackTemplate).filter(FeedbackTemplate.deleted_at.is_(None)).order_by(FeedbackTemplate.name.asc()).all()
    return {"templates": [{"id": r.id, "name": r.name, "description": r.description} for r in rows]}

@app.get("/feedback-templates/{tid}")
def get_feedback_template(tid: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    t = db.get(FeedbackTemplate, tid)
    if not t or t.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    return {"id": t.id, "name": t.name, "description": t.description}

@app.put("/feedback-templates/{tid}")
def update_feedback_template(tid: int, payload: FeedbackTemplateDTO, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    t = db.get(FeedbackTemplate, tid)
    if not t or t.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(t, k, v)
    db.commit(); return {"ok": True}

class FeedbackFormDTO(BaseModel):
    template_id: Optional[int] = None; coachee_user_id: int
    coach_user_id: Optional[int] = None; due_date: Optional[date] = None
    status: Optional[str] = "not_started"; content: Optional[str] = None

@app.get("/feedback/by-coachee/{uid}")
def list_feedback(uid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(FeedbackForm).filter(FeedbackForm.coachee_user_id==uid, FeedbackForm.deleted_at.is_(None)).all()
    return {"feedback": [{"id": r.id, "template_id": r.template_id, "status": r.status,
                          "due_date": r.due_date.isoformat() if r.due_date else None, "content": r.content} for r in rows]}

@app.post("/feedback")
def create_feedback(payload: FeedbackFormDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = FeedbackForm(template_id=payload.template_id, coachee_user_id=payload.coachee_user_id,
                     coach_user_id=payload.coach_user_id or current.user_id, due_date=payload.due_date,
                     status=payload.status or "not_started", content=payload.content)
    db.add(f); db.commit(); return {"id": f.id}

@app.put("/feedback/{fid}")
def update_feedback(fid: int, payload: FeedbackFormDTO, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = db.get(FeedbackForm, fid)
    if not f or f.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(f, k, v)
    db.commit(); return {"ok": True}

@app.delete("/feedback/{fid}")
def delete_feedback(fid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = db.get(FeedbackForm, fid)
    if not f or f.deleted_at is not None: raise HTTPException(status_code=404, detail="Not found")
    db.delete(f); db.commit(); return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
