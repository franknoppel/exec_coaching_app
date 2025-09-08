from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from datetime import datetime, timedelta, date
from .base import SessionLocal, engine
from .models import Base, User, Organization, Membership, CoachProfile, CoacheeProfile,     CoachingSession, TrainingModule, ModuleAssignment, FeedbackForm, FeedbackTemplate, CoachCoachee

FIRSTN = ["Alex","Taylor","Jordan","Casey","Riley","Morgan","Jamie","Avery","Sam","Drew","Dana","Cameron"]
LASTN = ["Smith","Johnson","Lee","Brown","Garcia","Davis","Martinez","Miller","Wilson","Moore"]

def seed():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db: Session = SessionLocal()
    try:
        # 2 super admins
        for i in range(2):
            db.add(User(
                email=f"admin{i+1}@example.com",
                password_hash=bcrypt.hash("admin123"),
                role="admin",
                first_name="Super",
                last_name=f"Admin{i+1}",
                status="active"
            ))
        db.flush()

        # 2 coach orgs
        coach_orgs = []
        for i in range(2):
            o = Organization(
                name=f"CoachOrg {i+1}",
                org_type="coach",
                email=f"coachorg{i+1}@example.com",
                website="https://example.com",
                status="active",
                description="Coaching org"
            )
            db.add(o); coach_orgs.append(o)
        db.flush()

        # 2 coachee orgs
        coachee_orgs = []
        for i in range(2):
            o = Organization(
                name=f"ClientOrg {i+1}",
                org_type="coachee",
                email=f"clientorg{i+1}@example.com",
                website="https://clients.example.com",
                status="active",
                description="Client org"
            )
            db.add(o); coachee_orgs.append(o)
        db.flush()

        # 4 coaches
        coaches = []
        for i in range(4):
            u = User(
                email=f"coach{i+1}@example.com",
                password_hash=bcrypt.hash("coach123"),
                role="coach",
                first_name=FIRSTN[i],
                last_name=LASTN[i],
                status="active"
            )
            db.add(u); coaches.append(u)
        db.flush()

        # Coach memberships + profiles
        for i, c in enumerate(coaches):
            db.add(Membership(user_id=c.user_id, org_id=coach_orgs[i % 2].org_id, role_in_org="coach"))
            db.add(CoachProfile(user_id=c.user_id, qualifications="ICF PCC", profile="Experienced executive coach."))

        # 6 coachees
        coachees = []
        for i in range(6):
            u = User(
                email=f"coachee{i+1}@example.com",
                password_hash=bcrypt.hash("coachee123"),
                role="coachee",
                first_name=FIRSTN[(i+5)%len(FIRSTN)],
                last_name=LASTN[(i+3)%len(LASTN)],
                status="active"
            )
            db.add(u); coachees.append(u)
        db.flush()

        # Coachee profiles
        for i, ce in enumerate(coachees):
            db.add(CoacheeProfile(
                user_id=ce.user_id,
                org_id=coachee_orgs[i % 2].org_id,
                background="5+ years in product.",
                education="MBA",
                challenges="Stakeholder alignment.",
                goals="Improve executive presence."
            ))

        # Coach <-> Coachee links
        for i, ce in enumerate(coachees):
            coach = coaches[i % len(coaches)]
            db.add(CoachCoachee(coach_user_id=coach.user_id, coachee_user_id=ce.user_id))

        # 5 training modules
        modules = []
        for i in range(5):
            m = TrainingModule(name=f"Module {i+1}", description=f"Description for Module {i+1}")
            db.add(m); modules.append(m)
        db.flush()

        # 5 feedback templates
        templates = []
        for i in range(5):
            t = FeedbackTemplate(name=f"Template {i+1}", description=f"Feedback template {i+1}")
            db.add(t); templates.append(t)
        db.flush()

        # Sessions: 5 per coachee (3 past completed, 2 future open)
        now = datetime.utcnow()
        for ce in coachees:
            coach_id = db.query(CoachCoachee).filter(CoachCoachee.coachee_user_id==ce.user_id).first().coach_user_id
            for j in range(3):
                db.add(CoachingSession(
                    session_date=now - timedelta(days=21 - j*4),
                    coach_user_id=coach_id, coachee_user_id=ce.user_id,
                    topic=f"Past session {j+1}", coach_notes="Reflections", status="completed",
                    approach="GROW", forward_goals="Continue habits", next_steps="Follow up"
                ))
            for j in range(2):
                db.add(CoachingSession(
                    session_date=now + timedelta(days=7 + j*7),
                    coach_user_id=coach_id, coachee_user_id=ce.user_id,
                    topic=f"Upcoming session {j+1}", coach_notes="Planned", status="ongoing" if j==0 else "not_started"
                ))

        # 3 module assignments total
        for i in range(3):
            ce = coachees[i]
            coach_id = db.query(CoachCoachee).filter(CoachCoachee.coachee_user_id==ce.user_id).first().coach_user_id
            db.add(ModuleAssignment(
                module_id=modules[i % len(modules)].id,
                coachee_user_id=ce.user_id,
                coach_user_id=coach_id,
                due_date=date.today() + timedelta(days=7*(i+1)),
                status="ongoing" if i==0 else "not_started"
            ))

        # 4 feedback requests/submissions per coachee
        for ce in coachees:
            coach_id = db.query(CoachCoachee).filter(CoachCoachee.coachee_user_id==ce.user_id).first().coach_user_id
            for k in range(4):
                db.add(FeedbackForm(
                    template_id=templates[k % len(templates)].id,
                    coachee_user_id=ce.user_id, coach_user_id=coach_id,
                    due_date=date.today() + timedelta(days=3*k),
                    status="completed" if k % 2 else "ongoing",
                    content=f"Feedback content {k+1} for {ce.email}"
                ))

        db.commit()
        print("Seed complete. Coaches: coach1@example.com..coach4@example.com / coach123")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
