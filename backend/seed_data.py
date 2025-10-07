from sqlalchemy.orm import Session
from backend import models
import random
import datetime


def seed_data(db: Session):
    """Populate the database with dummy data if empty."""

    # Check if already seeded
    if db.query(models.Administrator).first():
        print("✅ Database already seeded.")
        return

    print("🌱 Seeding database with dummy data...")

    # -----------------------------
    # Administrators
    # -----------------------------
    admins = [
        models.Administrator(
            admin_firstname="Alice",
            admin_lastname="Admin",
            admin_email="alice@coachapp.com",
            admin_password="admin123"
        ),
        models.Administrator(
            admin_firstname="Bob",
            admin_lastname="Boss",
            admin_email="bob@coachapp.com",
            admin_password="admin456"
        ),
    ]
    db.add_all(admins)
    db.commit()

    # -----------------------------
    # Coach Organizations
    # -----------------------------
    coorgs = []
    for i in range(2):
        coorg = models.CoachOrganization(
            coorg_name=f"CoachOrg{i+1}",
            coorg_email=f"org{i+1}@coachapp.com",
            coorg_password="orgpass",
            coorg_website=f"https://org{i+1}.com",
            coorg_logo=f"/uploads/org{i+1}_logo.png",
            coorg_description=f"This is the description for Coach Organization {i+1}.",
        )
        coorgs.append(coorg)
    db.add_all(coorgs)
    db.commit()

    # -----------------------------
    # Coaches
    # -----------------------------
    coaches = []
    for org_index, coorg in enumerate(coorgs, start=1):
        for j in range(4):
            coach = models.Coach(
                coach_firstname=f"Coach{org_index}{j+1}",
                coach_lastname="Lastname",
                coach_email=f"coach{org_index}{j+1}@coachapp.com",
                coach_qualifications="ICF Certified, 10 years experience",
                coach_profile="Helping professionals unlock their potential.",
                coach_password="coachpass",
                coach_status=True,
                coach_photo=f"/uploads/coach{org_index}{j+1}.jpg",
                coach_orgs=coorg.coorg_id,
            )
            coaches.append(coach)
    db.add_all(coaches)
    db.commit()

    # -----------------------------
    # Coachee Organizations
    # -----------------------------
    coe_orgs = []
    for i in range(2):
        coe_org = models.CoacheeOrganization(
            coe_name=f"CoacheeOrg{i+1}",
            coe_email=f"coeorg{i+1}@coachapp.com",
            coe_password="coeorgpass",
            coe_profile=f"Coachee organization {i+1} profile",
            coe_website=f"https://coacheeorg{i+1}.com",
        )
        coe_orgs.append(coe_org)
    db.add_all(coe_orgs)
    db.commit()

    # -----------------------------
    # Coachees
    # -----------------------------
    coachees = []
    for org_index, coe_org in enumerate(coe_orgs, start=1):
        for j in range(6):
            coachee = models.Coachee(
                coachee_firstname=f"Coachee{org_index}{j+1}",
                coachee_lastname="Lastname",
                coachee_email=f"coachee{org_index}{j+1}@coachapp.com",
                coachee_org=coe_org.coe_id,
                coachee_background="5 years in management.",
                coachee_edu="MBA",
                coachee_challenges="Time management, communication.",
                coachee_goals="Become a more effective leader.",
                coachee_password="coacheepass",
                coachee_status=True,
                coachee_photo=f"/uploads/coachee{org_index}{j+1}.jpg",
            )
            coachees.append(coachee)
    db.add_all(coachees)
    db.commit()

    # -----------------------------
    # Coaching Sessions
    # -----------------------------
    sessions = []
    for coachee in coachees:
        coach = random.choice(coaches)
        for s in range(5):
            date = datetime.datetime.now() + datetime.timedelta(days=s - 3)
            completed = s < 3
            session = models.CoachingSession(
                session_date=date.strftime("%m/%d/%Y %H:%M"),
                session_coach=coach.coach_id,
                session_coachee=coachee.coachee_id,
                session_coachnotes="Session notes and reflections.",
                session_topic="Leadership development",
                session_coachapproach="Reflective coaching and goal setting.",
                session_goals="Improve communication by 20%",
                session_nextsteps="Practice active listening.",
                session_attachments="/uploads/sample_notes.pdf" if completed else "",
            )
            sessions.append(session)
    db.add_all(sessions)
    db.commit()

    # -----------------------------
    # Assignments
    # -----------------------------
    assignments = []
    for coachee in coachees:
        coach = random.choice(coaches)
        for a in range(3):
            status = ["not started", "ongoing", "completed"][a % 3]
            assignment = models.Assignment(
                assignment_module=f"Module {a+1}",
                assignment_description=f"Assignment {a+1} for {coachee.coachee_firstname}",
                assignment_resources="/uploads/sample_assignment.pdf",
                assignment_duedate=(datetime.datetime.now() + datetime.timedelta(days=10)).strftime("%m/%d/%Y"),
                assignment_status=status,
                assignment_coachee=coachee.coachee_id,
                assignment_coach=coach.coach_id,
                assignment_session_ID_reference=random.choice(sessions).session_id,
                assignment_feedback="Great progress!" if status == "completed" else "",
            )
            assignments.append(assignment)
    db.add_all(assignments)
    db.commit()

    print("✅ Dummy data seeded successfully!")
