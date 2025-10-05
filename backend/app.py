# backend/app.py
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
import shutil

app = FastAPI(title="Executive Coaching App")

# ---- Folders ----
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ---- Static & templates ----
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ---- Demo in-memory state (swap to your DB when ready) ----
COACHEES = []          # [{id, name}]
SESSIONS = {}          # {coachee_id: [{id, title, date, notes}]}
_next_id = 1
def next_id():
    global _next_id
    i = _next_id
    _next_id += 1
    return i

# ---- Web page ----
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Executive Coaching Dashboard"}
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}

# ---- API: coachees ----
@app.get("/api/coachees")
def list_coachees():
    return {"items": COACHEES}

@app.post("/api/coachees")
def add_coachee(name: str):
    cid = next_id()
    COACHEES.append({"id": cid, "name": name})
    SESSIONS.setdefault(cid, [])
    return {"status": "added", "id": cid, "name": name}

@app.delete("/api/coachees/{coachee_id}")
def remove_coachee(coachee_id: int):
    global COACHEES
    COACHEES = [c for c in COACHEES if c["id"] != coachee_id]
    SESSIONS.pop(coachee_id, None)
    return {"status": "removed", "id": coachee_id}

# ---- API: sessions (filtered per coachee) ----
@app.get("/api/coachees/{coachee_id}/sessions")
def list_sessions(coachee_id: int):
    return {"items": SESSIONS.get(coachee_id, [])}

@app.get("/api/sessions/{session_id}")
def get_session(session_id: int):
    for lst in SESSIONS.values():
        for s in lst:
            if s.get("id") == session_id:
                return s
    return {"error": "not found"}

# ---- API: coach profile + photo upload ----
@app.post("/api/coach/profile")
async def update_profile(
    name: str = Form(...),
    bio: str = Form(""),
    photo: Optional[UploadFile] = File(None),
):
    photo_url = None
    if photo:
        suffix = Path(photo.filename).suffix
        dest = UPLOADS_DIR / f"coach_photo{suffix or ''}"
        with dest.open("wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_url = f"/static/uploads/{dest.name}"
    # TODO: persist name/bio/photo_url to DB
    return {"status": "saved", "name": name, "bio": bio, "photo_url": photo_url}

# Optional: allow `python backend/app.py` direct run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
