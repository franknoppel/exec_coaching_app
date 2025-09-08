How to run:
1) Backend
   cd exec_coaching_app/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python -m db.init_db       # creates app.db and seeds data
   uvicorn app:app --reload --port 8000

2) Frontend
   Open exec_coaching_app/frontend/index.html in your browser.
   Try logging in as: coach1@example.com / coach123
   Or click "Create a new coach profile" to add one via the dev helper endpoint.
