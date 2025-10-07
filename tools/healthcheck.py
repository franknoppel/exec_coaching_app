import os, sys, json, importlib, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
TEMPLATES = BACKEND / "templates"
STATIC = BACKEND / "static"
APP_PY = BACKEND / "app.py"

report = {"exists":{}, "routes":[], "errors":[]}

def exists(p):
    report["exists"][str(p.relative_to(ROOT))] = p.exists()

try:
    exists(BACKEND); exists(TEMPLATES); exists(STATIC); exists(APP_PY)
    if not APP_PY.exists():
        raise FileNotFoundError("backend/app.py not found")

    # import app
    sys.path.insert(0, str(ROOT))
    app_mod = importlib.import_module("backend.app")
    app = getattr(app_mod, "app", None)
    if app is None:
        raise RuntimeError("No 'app' object in backend/app.py")

    # list routes
    report["routes"] = sorted([(r.path, sorted(list(getattr(r, "methods", [])))) for r in app.routes])

    # required bits for templated home (if you’re using it)
    from fastapi.templating import Jinja2Templates  # noqa
    report["exists"]["templates/index.html"] = (TEMPLATES / "index.html").exists()
    report["exists"]["static/app.css"] = (STATIC / "app.css").exists()

except Exception as e:
    report["errors"].append(str(e))
    report["errors"].append(traceback.format_exc())

print(json.dumps(report, indent=2))
