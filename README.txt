=====================================================
           COACH APP – LOCAL SETUP GUIDE
=====================================================

🧭 1️⃣  NAVIGATE TO BACKEND FOLDER
Open Terminal and run:
    cd ~/documents/github/exec_coaching_app/backend

*(If your folder is named "Documents" instead of "documents", adjust the path.)*

-----------------------------------------------------
⚙️ 2️⃣  INSTALL DEPENDENCIES
Make sure Python 3.9+ is installed.

Then install FastAPI and required libraries:
    pip3 install fastapi uvicorn sqlalchemy python-multipart

If pip doesn’t work, try:
    python3 -m pip install fastapi uvicorn sqlalchemy python-multipart

-----------------------------------------------------
🧱 3️⃣  RUN THE BACKEND SERVER
Start FastAPI with:
    cd ~/Documents/GitHub/exec_coaching_app
    python3 -m uvicorn backend.app:app --reload


You should see output like:
    INFO:     Uvicorn running on http://127.0.0.1:8000
    🌱 Seeding database with dummy data...
    ✅ Dummy data seeded successfully!

Once it says "Application startup complete",
your backend is live and ready.

-----------------------------------------------------
🌐 4️⃣  OPEN THE FRONTEND
In your web browser, go to:
    http://127.0.0.1:8000/frontend/index.html

You’ll see the Bootstrap login page with a
✅ "Server Connected" message if everything works.

-----------------------------------------------------
👤 5️⃣  TEST LOGIN
Use any of these demo accounts:

Role          | Email                  | Password
-----------------------------------------------------
Admin         | alice@coachapp.com     | admin123
Admin         | bob@coachapp.com       | admin456
Coach Org     | org1@coachapp.com      | orgpass
Coach Org     | org2@coachapp.com      | orgpass
Coach         | coach11@coachapp.com   | coachpass
Coachee Org   | coeorg1@coachapp.com   | coeorgpass
Coachee Org   | coeorg2@coachapp.com   | coeorgpass
Coachee       | coachee11@coachapp.com | coacheepass

(Coaches are redirected to their dashboard automatically.)

-----------------------------------------------------
📁 6️⃣  PROJECT STRUCTURE
documents/github/exec_coaching_app/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── seed_data.py
│   └── uploads/
│       ├── admins/sample_logo.png
│       ├── coaches/coach1_photo.jpg
│       ├── coachees/coachee1_photo.jpg
│       ├── sessions/sample_notes.pdf
│       └── assignments/sample_assignment.pdf
│
├── frontend/
│   ├── index.html
│   ├── coach_dashboard.html
│   ├── js/
│   │   ├── login.js
│   │   └── coach_dashboard.js
│   └── css/style.css
│
└── app.db  (auto-created on first run)

-----------------------------------------------------
✅ 7️⃣  TIPS
• The database auto-seeds with dummy users and data.
• Uploaded files are stored under backend/uploads/.
• To restart fresh, delete app.db and rerun the server.

-----------------------------------------------------
💡 8️⃣  FIX "pip" OR "uvicorn" NOT FOUND ON MACOS
If you get:
    zsh: /usr/local/bin/pip: bad interpreter: /usr/bin/python: no such file or directory
or
    zsh: command not found: uvicorn

Run the following:

1️⃣  Check Python version:
    python3 --version

2️⃣  Install using python3 directly:
    python3 -m pip install --user fastapi uvicorn sqlalchemy python-multipart

3️⃣  Find where Python stores scripts:
    python3 -m site --user-base

   It will output something like:
    /Users/<yourusername>/Library/Python/3.9
   Inside that folder is a "bin" directory. Add it to your PATH.

4️⃣  Add this line to ~/.zshrc:
    export PATH="$PATH:/Users/$(whoami)/Library/Python/3.9/bin"

5️⃣  Reload your shell:
    source ~/.zshrc

6️⃣  Verify:
    uvicorn --version
   (It should show your installed version.)

If it still fails:
    python3 -m ensurepip --upgrade
    python3 -m pip install --user fastapi uvicorn sqlalchemy python-multipart

----------------------
