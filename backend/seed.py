from backend.models import Administrator, CoachOrganization, Coach, CoacheeOrganization, Coachee, CoachingSession, Assignment
from datetime import datetime, timedelta
import random


def seed_dummy_data(SessionLocal):
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Coach).first():
            db.close()
            return

        # --------------------
        # Admins
        # --------------------
        admins = [
            Administrator(admin_firstname="Alice", admin_lastname="Admin", admin_email="admin1@coachapp.com", admin_password="adminpass"),
            Administrator(admin_firstname="Bob", admin_lastname="Boss", admin_email="admin2@coachapp.com", admin_password="adminpass"),
        ]
        db.add_all(admins)
        db.commit()

        # --------------------
        # Coach Organizations
        # --------------------
        orgs = []
        for i in range(2):
            org = CoachOrganization(
                coorg_name=f"CoachOrg {i+1}",
                coorg_email=f"coachorg{i+1}@coachapp.com",
                coorg_password="orgpass",
                coorg_website=f"https://coachorg{i+1}.com",
                coorg_logo="",
                coorg_status=True,
                coorg_description="Leading coaching organization."
            )
            db.add(org)
            orgs.append(org)
        db.commit()

        # --------------------
        # Coaches
        # --------------------
        coaches = []
        for i in range(4):
            org = orgs[i % 2]
            coach = Coach(
                coach_firstname=f"Coach{i+1}",
                coach_lastname="Smith",
                coach_email=f"coach{i+1}@coachapp.com",
                coach_qualifications="ICF Certified Coach",
                coach_profile="Experienced leadership coach.",
                coach_orgs=org.coorg_id,
                coach_password="coachpass",
                coach_status=True,
                coach_photo=""
            )
            db.add(coach)
            coaches.append(coach)
        db.commit()

        # --------------------
        # Coachee Organizations
        # --------------------
        coe_orgs = []
        for i in range(2):
            coe_org = CoacheeOrganization(
                coe_name=f"ClientOrg {i+1}",
                coe_email=f"clientorg{i+1}@coachapp.com",
                coe_password="clientorgpass",
                coe_profile="Corporate client organization.",
                coe_website=f"https://clientorg{i+1}.com",
                coe_status=True,
            )
            db.add(coe_org)
            coe_orgs.append(coe_org)
        db.commit()

        # --------------------
        # Coachees
        # --------------------
        coachees = []
        for i in range(12):
            org = coe_orgs[i % 2]
            coachee = Coachee(
                coachee_firstname=f"Coachee{i+1}",
                coachee_lastname="Jones",
                coachee_email=f"coachee{i+1}@coachapp.com",
                coachee_org=org.coe_id,
                coachee_background="Professional background info.",
                coachee_edu="MBA",
                coachee_challenges="Improving communication.",
                coachee_goals="Become a better leader.",
                coachee_password="coacheepass",
                coachee_status=True,
                coachee_photo=""
            )
            db.add(coachee)
            coachees.append(coachee)
        db.commit()

        # --------------------
        # Coaching Sessions & Assignments
        # --------------------
        for coach in coaches:
            for coachee in coachees:
                # Create 5 sessions per coachee
                for s in range(5):
                    date = datetime.now() - timedelta(days=(5 - s) * 7)
                    completed = s < 3  # 3 completed, 2 upcoming
                    session = CoachingSession(
                        session_date=date.strftime("%m/%d/%Y %H:%M"),
                        session_coach=coach.coach_id,
                        session_coachee=coachee.coachee_id,
                        session_coachnotes="Discussed progress and goals.",
                        session_topic=f"Session {s+1}",
                        session_coachapproach="Active listening and feedback.",
                        session_goals="Improve leadership presence.",
                        session_nextsteps="Practice reflection." if completed else "",
                        session_attachments=""
                    )
                    db.add(session)
                    db.commit()

                    # 3 assignments per coachee (2 completed, 1 not started)
                    for a in range(3):
                        status = ["completed", "completed", "not started"][a]
                        assignment = Assignment(
                            assignment_module=f"Module {a+1}",
                            assignment_description="Assignment description and tasks.",
                            assignment_resources="resources.pdf",
                            assignment_duedate=(datetime.now() + timedelta(days=14)).strftime("%m/%d/%Y"),
                            assignment_status=status,
                            assignment_coachee=coachee.coachee_id,
                            assignment_coach=coach.coach_id,
                            assignment_session_ID_reference=session.session_id,
                            assignment_feedback="Good job." if status == "completed" else ""
                        )
                        db.add(assignment)
            db.commit()

        db.close()
        print("✅ Dummy data seeded successfully.")

    except Exception as e:
        print("❌ Seeding error:", e)
        db.rollback()
        db.close()
