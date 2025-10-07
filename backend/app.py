from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends, Query
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
from datetime import datetime
import shutil
import os
import io

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

# Image compression target (KB). Tune as needed.
IMAGE_TARGET_KB = 10
# Summary length (characters). Increased to ~3x the previous ~140 to satisfy request.
SUMMARY_MAX_CHARS = 210


def compress_image_file(file_path: str, target_kb: int = IMAGE_TARGET_KB):
    """Try to compress an image file in-place to approximately target_kb using Pillow.
    If Pillow is not installed or an error occurs, leave the file as-is.
    """
    try:
        from PIL import Image
    except Exception:
        return False

    try:
        target_bytes = target_kb * 1024
        with Image.open(file_path) as im:
            # flatten alpha to white for JPEG
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            if has_alpha:
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im2 = bg
            else:
                im2 = im.convert("RGB")

            # Try decreasing quality and scaling until small enough
            quality = 85
            min_quality = 25
            scale = 1.0
            for _ in range(20):
                # prepare resized candidate
                if scale < 0.999:
                    new_w = max(1, int(im2.width * scale))
                    new_h = max(1, int(im2.height * scale))
                    candidate = im2.resize((new_w, new_h), Image.LANCZOS)
                else:
                    candidate = im2

                buf = io.BytesIO()
                candidate.save(buf, format="JPEG", quality=quality, optimize=True)
                size = buf.tell()
                if size <= target_bytes or quality <= min_quality:
                    # write back
                    with open(file_path, "wb") as f:
                        f.write(buf.getvalue())
                    return True

                # reduce quality first, then scale
                if quality > min_quality:
                    quality = max(min_quality, int(quality * 0.8))
                else:
                    scale *= 0.85
    except Exception as e:
        print(f"Image compression failed for {file_path}: {e}")
        return False

    return False


def generate_summary_for(c):
    parts = []
    if getattr(c, 'coachee_background', None):
        parts.append(c.coachee_background.strip())
    if getattr(c, 'coachee_goals', None):
        parts.append(c.coachee_goals.strip())
    if getattr(c, 'coachee_challenges', None):
        parts.append(c.coachee_challenges.strip())
    text = ' — '.join([p.replace('\n', ' ') for p in parts if p])
    if not text:
        return None
    if len(text) <= SUMMARY_MAX_CHARS:
        return text
    trunc = text[:SUMMARY_MAX_CHARS]
    for sep in ('.', '!', '?'):
        pos = trunc.rfind(sep)
        if pos > 40:
            return trunc[:pos+1]
    pos = trunc.rfind(' ')
    return (trunc[:pos] + '...') if pos > 20 else (trunc + '...')

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
@app.post("/coach")
def create_coach(
    coach_title: str = Form(...),
    coach_firstname: str = Form(...),
    coach_lastname: str = Form(...),
    coach_email: str = Form(...),
    coach_qualifications: str = Form(...),
    coach_profile: str = Form(...),
    coach_orgs: int = Form(...),
    coach_password: str = Form(...),
    coach_status: bool = Form(True),
    coach_photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    # Check if email already exists
    existing = db.query(Coach).filter(Coach.coach_email == coach_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Coach with this email already exists")

    photo_path = None
    if coach_photo:
        file_path = os.path.join("frontend", "uploads", coach_photo.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(coach_photo.file, buffer)
        # attempt to compress the saved image to keep files small
        try:
            compress_image_file(file_path)
        except Exception:
            pass
        photo_path = f"/frontend/uploads/{coach_photo.filename}"

    coach = Coach(
        coach_title=coach_title,
        coach_firstname=coach_firstname,
        coach_lastname=coach_lastname,
        coach_email=coach_email,
        coach_qualifications=coach_qualifications,
        coach_profile=coach_profile,
        coach_orgs=coach_orgs,
        coach_password=coach_password,
        coach_status=coach_status,
        coach_photo=photo_path,
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return {
        "id": coach.coach_id,
        "title": coach.coach_title,
        "firstname": coach.coach_firstname,
        "lastname": coach.coach_lastname,
        "email": coach.coach_email,
        "qualifications": coach.coach_qualifications,
        "profile": coach.coach_profile,
        "status": coach.coach_status,
        "photo": coach.coach_photo,
    }
@app.get("/coach/{coach_id}")
def get_coach_profile(coach_id: int, db: Session = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return {
        "id": coach.coach_id,
        "title": coach.coach_title,
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
    coach_title: str = Form(...),
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

    coach.coach_title = coach_title
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
        try:
            compress_image_file(file_path)
        except Exception:
            pass
        coach.coach_photo = f"/frontend/uploads/{coach_photo.filename}"

    db.commit()
    db.refresh(coach)

    return {
        "id": coach.coach_id,
        "title": coach.coach_title,
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
    # use shared generate_summary_for to keep summaries consistent and longer
    results = []
    now = datetime.now()
    for c in coachees:
        s_rows = (
            db.query(CoachingSession)
            .filter(CoachingSession.session_coachee == c.coachee_id, CoachingSession.session_coach == coach_id)
            .all()
        )
        last_s = None
        next_s = None
        previous_s = None  # Always define
        parsed = []
        for s in s_rows:
            dt = None
            if isinstance(s.session_date, str):
                # Try both common formats
                try:
                    if '-' in s.session_date:
                        dt = datetime.strptime(s.session_date, '%Y-%m-%d %H:%M')
                    elif '/' in s.session_date:
                        dt = datetime.strptime(s.session_date, '%m/%d/%Y %H:%M')
                    else:
                        dt = datetime.fromisoformat(s.session_date)
                except Exception:
                    try:
                        dt = datetime.fromisoformat(s.session_date)
                    except Exception:
                        continue
            else:
                try:
                    dt = datetime.fromisoformat(s.session_date)
                except Exception:
                    continue
            if dt:
                parsed.append((dt, s))
        if parsed:
            parsed.sort(key=lambda x: x[0])
            past = [p for p in parsed if p[0] <= now]
            future = [p for p in parsed if p[0] > now]
            if past:
                last_dt, last_row = past[-1]
                last_s = {"id": last_row.session_id, "date": last_dt.strftime('%Y-%m-%d %H:%M'), "topic": last_row.session_topic}
                if len(past) >= 2:
                    prev_dt, prev_row = past[-2]
                    previous_s = {"id": prev_row.session_id, "date": prev_dt.strftime('%Y-%m-%d %H:%M'), "topic": prev_row.session_topic}
        # next_s only if future exists
            if future:
                next_dt, next_row = future[0]
                next_s = {"id": next_row.session_id, "date": next_dt.strftime('%Y-%m-%d %H:%M'), "topic": next_row.session_topic}

        results.append(
            {
                "id": c.coachee_id,
                "firstname": c.coachee_firstname,
                "lastname": c.coachee_lastname,
                "email": c.coachee_email,
                "status": c.coachee_status,
                "photo": c.coachee_photo,
                "org_id": c.coachee_org,
                "org_name": c.organization.coe_name if c.organization else None,
                "summary": generate_summary_for(c),
                "last_session": last_s,
                "previous_session": previous_s,
                "next_session": next_s,
            }
        )
    return results

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
        "org_name": coachee.organization.coe_name if coachee.organization else None,
        "photo": coachee.coachee_photo,
        "background": coachee.coachee_background,
        "education": coachee.coachee_edu,
        "challenges": coachee.coachee_challenges,
        "summary": generate_summary_for(coachee),
        "goals": coachee.coachee_goals,
        "status": coachee.coachee_status,
    }

@app.post("/coachee/{coachee_id}/regenerate_summary")
def regenerate_coachee_summary(coachee_id: int, db: Session = Depends(get_db)):
    coachee = db.query(Coachee).filter(Coachee.coachee_id == coachee_id).first()
    if not coachee:
        raise HTTPException(status_code=404, detail="Coachee not found")

    summary = generate_summary_for(coachee)
    return {"summary": summary}


@app.get("/coachee/{coachee_id}/sessions")
def get_coachee_sessions(coachee_id: int, coach_id: int = Query(None), db: Session = Depends(get_db)):
    q = db.query(CoachingSession).filter(CoachingSession.session_coachee == coachee_id)
    if coach_id is not None:
        # show only sessions assigned to this coach
        q = q.filter(CoachingSession.session_coach == coach_id)
    sessions = q.order_by(CoachingSession.session_date.desc()).all()
    return [
        {
            "id": s.session_id,
            "date": s.session_date,
            "topic": s.session_topic,
            "coach_id": s.session_coach,
            "status": s.session_status or "open",
            "summary": (s.session_coachnotes or s.session_goals or s.session_topic or "")[:200],
            "editable": (coach_id is not None and s.session_coach == coach_id and (s.session_status != "completed")),
        }
        for s in sessions
    ]


@app.put("/session/{session_id}")
def update_session_detail(
    session_id: int,
    session_date: str = Form(None),
    session_topic: str = Form(None),
    session_coachnotes: str = Form(None),
    session_coachapproach: str = Form(None),
    session_goals: str = Form(None),
    session_nextsteps: str = Form(None),
    session_status: str = Form(None),
    session_attachments: str = Form(None),
    coach_id: int = Query(None),
    db: Session = Depends(get_db),
    new_attachments: list = File(None),
):
    s = db.query(CoachingSession).filter(CoachingSession.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    # authorize by coach_id: only the assigned coach may update
    if coach_id is None or s.session_coach != coach_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this session")

    if session_date is not None:
        s.session_date = session_date
    if session_topic is not None:
        s.session_topic = session_topic
    if session_coachnotes is not None:
        s.session_coachnotes = session_coachnotes
    if session_coachapproach is not None:
        s.session_coachapproach = session_coachapproach
    if session_goals is not None:
        s.session_goals = session_goals

    if session_nextsteps is not None:
        s.session_nextsteps = session_nextsteps
    if session_status is not None:
        s.session_status = session_status

    # Handle new file uploads
    try:
        if new_attachments:
            # Normalize to list of UploadFile
            files = new_attachments
            if not isinstance(files, list):
                files = [files]
            upload_paths = []
            for file in files:
                # FastAPI may pass bytes if only one file, or UploadFile for multiple
                if hasattr(file, 'filename') and hasattr(file, 'file'):
                    if not file.filename:
                        continue
                    file_path = os.path.join("frontend", "uploads", "sessions", file.filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    upload_paths.append(f"/frontend/uploads/sessions/{file.filename}")
                # Defensive: skip bytes or other types
            # Append to existing attachments if any
            if upload_paths:
                if s.session_attachments:
                    s.session_attachments += "," + ",".join(upload_paths)
                else:
                    s.session_attachments = ",".join(upload_paths)
    except Exception as e:
        print(f"[SESSION FILE UPLOAD ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Attachment upload failed: {e}")

    # Allow removing attachments via session_attachments field (comma-separated paths)
    if session_attachments is not None:
        # Only overwrite if not empty string; if empty, preserve existing attachments
        if session_attachments.strip() != '':
            s.session_attachments = session_attachments

    db.commit()
    db.refresh(s)
    return {
        "id": s.session_id,
        "date": s.session_date,
        "topic": s.session_topic,
        "coach_notes": s.session_coachnotes,
        "coach_approach": s.session_coachapproach,
        "goals": s.session_goals,
        "next_steps": s.session_nextsteps,
        "attachments": s.session_attachments,
        "status": s.session_status,
    }


@app.get("/session/{session_id}")
def get_session_detail(session_id: int, db: Session = Depends(get_db)):
    s = db.query(CoachingSession).filter(CoachingSession.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": s.session_id,
        "date": s.session_date,
        "topic": s.session_topic,
        "coach_id": s.session_coach,
        "coachee_id": s.session_coachee,
        "coach_notes": s.session_coachnotes,
        "coach_approach": s.session_coachapproach,
        "goals": s.session_goals,
        "next_steps": s.session_nextsteps,
        "attachments": s.session_attachments,
        "status": s.session_status,
    }


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


@app.put("/coachee/{coachee_id}")
def update_coachee(
    coachee_id: int,
    coachee_firstname: str = Form(...),
    coachee_lastname: str = Form(...),
    coachee_email: str = Form(...),
    coachee_org: int = Form(None),
    coachee_background: str = Form(...),
    coachee_edu: str = Form(...),
    coachee_challenges: str = Form(...),
    coachee_goals: str = Form(...),
    coachee_status: bool = Form(...),
    coachee_photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    coachee = db.query(Coachee).filter(Coachee.coachee_id == coachee_id).first()
    if not coachee:
        raise HTTPException(status_code=404, detail="Coachee not found")

    coachee.coachee_firstname = coachee_firstname
    coachee.coachee_lastname = coachee_lastname
    coachee.coachee_email = coachee_email
    coachee.coachee_background = coachee_background
    coachee.coachee_edu = coachee_edu
    coachee.coachee_challenges = coachee_challenges
    coachee.coachee_goals = coachee_goals
    coachee.coachee_status = coachee_status
    if coachee_org is not None:
        coachee.coachee_org = coachee_org

    if coachee_photo:
        file_path = os.path.join("frontend", "uploads", coachee_photo.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(coachee_photo.file, buffer)
        try:
            compress_image_file(file_path)
        except Exception:
            pass
        coachee.coachee_photo = f"/frontend/uploads/{coachee_photo.filename}"

    db.commit()
    db.refresh(coachee)

    return {
        "id": coachee.coachee_id,
        "firstname": coachee.coachee_firstname,
        "lastname": coachee.coachee_lastname,
        "email": coachee.coachee_email,
        "org": coachee.coachee_org,
        "org_name": coachee.organization.coe_name if coachee.organization else None,
        "background": coachee.coachee_background,
        "education": coachee.coachee_edu,
        "challenges": coachee.coachee_challenges,
        "goals": coachee.coachee_goals,
        "status": coachee.coachee_status,
        "photo": coachee.coachee_photo,
    }


@app.get("/coachee_organizations")
def list_coachee_organizations(db: Session = Depends(get_db)):
    orgs = db.query(CoacheeOrganization).all()
    return [{"id": o.coe_id, "name": o.coe_name} for o in orgs]


@app.post("/coachee_organizations")
def create_coachee_organization(name: str = Form(...), email: str = Form(None), profile: str = Form(None), website: str = Form(None), db: Session = Depends(get_db)):
    # simple create endpoint for adding organizations inline
    if db.query(CoacheeOrganization).filter(CoacheeOrganization.coe_name == name).first():
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    org = CoacheeOrganization(
        coe_name=name,
        coe_email=email or None,
        coe_profile=profile or None,
        coe_website=website or None,
        coe_status=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"id": org.coe_id, "name": org.coe_name}


@app.get("/coach_organizations")
def list_coach_organizations(db: Session = Depends(get_db)):
    orgs = db.query(CoachOrganization).all()
    return [{"id": o.coorg_id, "name": o.coorg_name} for o in orgs]


@app.post("/coachee")
def create_coachee(
    coachee_firstname: str = Form(...),
    coachee_lastname: str = Form(...),
    coachee_email: str = Form(...),
    coachee_org: int = Form(None),
    coachee_background: str = Form(""),
    coachee_edu: str = Form(""),
    coachee_challenges: str = Form(""),
    coachee_goals: str = Form(""),
    coachee_status: bool = Form(True),
    coachee_photo: UploadFile = File(None),
    coachee_password: str = Form(None),
    db: Session = Depends(get_db),
):
    # check existing
    if db.query(Coachee).filter(Coachee.coachee_email == coachee_email).first():
        raise HTTPException(status_code=400, detail="Coachee with this email already exists")

    photo_path = None
    if coachee_photo:
        file_path = os.path.join("frontend", "uploads", coachee_photo.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(coachee_photo.file, buffer)
        photo_path = f"/frontend/uploads/{coachee_photo.filename}"

    coachee = Coachee(
        coachee_firstname=coachee_firstname,
        coachee_lastname=coachee_lastname,
        coachee_email=coachee_email,
        coachee_org=coachee_org,
        coachee_background=coachee_background,
        coachee_edu=coachee_edu,
        coachee_challenges=coachee_challenges,
        coachee_goals=coachee_goals,
        coachee_status=coachee_status,
        coachee_photo=photo_path,
        coachee_password=coachee_password or "",
    )
    db.add(coachee)
    db.commit()
    db.refresh(coachee)

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
        "photo": coachee.coachee_photo,
    }


@app.get("/coach/{coach_id}/assignments")
def get_coach_assignments(coach_id: int, db: Session = Depends(get_db)):
    assignments = db.query(Assignment).filter(Assignment.assignment_coach == coach_id).all()
    return [
        {
            "id": a.assignment_id,
            "description": a.assignment_description,
            "duedate": a.assignment_duedate,
            "status": a.assignment_status,
            "coachee": a.assignment_coachee,
        }
        for a in assignments
    ]


@app.get("/debug/coach_dashboard")
def debug_coach_dashboard(coach_id: int = Query(...), db: Session = Depends(get_db)):
    """Return aggregated data the frontend would load for a coach to help debugging.
    Temporary endpoint for troubleshooting.
    """
    coach = db.query(Coach).filter(Coach.coach_id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")

    coachees = get_coachees_for_coach(coach_id, db)
    sessions = get_pending_sessions(coach_id, db)
    assignments = get_coach_assignments(coach_id, db)
    return {
        "coach": {
            "id": coach.coach_id,
            "firstname": coach.coach_firstname,
            "lastname": coach.coach_lastname,
            "email": coach.coach_email,
            "title": coach.coach_title,
            "profile": coach.coach_profile,
            "photo": coach.coach_photo,
        },
        "coachees": coachees,
        "sessions": sessions,
        "assignments": assignments,
    }

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
