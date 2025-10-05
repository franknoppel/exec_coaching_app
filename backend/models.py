from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


# -----------------------
# Administrator
# -----------------------
class Administrator(Base):
    __tablename__ = "administrators"

    admin_id = Column(Integer, primary_key=True, index=True)
    admin_firstname = Column(String)
    admin_lastname = Column(String)
    admin_email = Column(String, unique=True, index=True)
    admin_password = Column(String)


# -----------------------
# Coach Organization
# -----------------------
class CoachOrganization(Base):
    __tablename__ = "coach_organizations"

    coorg_id = Column(Integer, primary_key=True, index=True)
    coorg_name = Column(String)
    coorg_email = Column(String, unique=True, index=True)
    coorg_password = Column(String)
    coorg_website = Column(String)
    coorg_logo = Column(String)
    coorg_status = Column(Boolean, default=True)
    coorg_description = Column(Text)

    coaches = relationship("Coach", back_populates="organization")


# -----------------------
# Coach
# -----------------------
class Coach(Base):
    __tablename__ = "coaches"

    coach_id = Column(Integer, primary_key=True, index=True)
    coach_firstname = Column(String)
    coach_lastname = Column(String)
    coach_email = Column(String, unique=True, index=True)
    coach_qualifications = Column(Text)
    coach_profile = Column(Text)
    coach_orgs = Column(Integer, ForeignKey("coach_organizations.coorg_id"))
    coach_password = Column(String)
    coach_status = Column(Boolean, default=True)
    coach_photo = Column(String)

    organization = relationship("CoachOrganization", back_populates="coaches")
    sessions = relationship("CoachingSession", back_populates="coach")


# -----------------------
# Coachee Organization
# -----------------------
class CoacheeOrganization(Base):
    __tablename__ = "coachee_organizations"

    coe_id = Column(Integer, primary_key=True, index=True)
    coe_name = Column(String)
    coe_email = Column(String, unique=True, index=True)
    coe_password = Column(String)
    coe_profile = Column(Text)
    coe_website = Column(String)
    coe_status = Column(Boolean, default=True)

    coachees = relationship("Coachee", back_populates="organization")


# -----------------------
# Coachee
# -----------------------
class Coachee(Base):
    __tablename__ = "coachees"

    coachee_id = Column(Integer, primary_key=True, index=True)
    coachee_firstname = Column(String)
    coachee_lastname = Column(String)
    coachee_email = Column(String, unique=True, index=True)
    coachee_org = Column(Integer, ForeignKey("coachee_organizations.coe_id"))
    coachee_background = Column(Text)
    coachee_edu = Column(Text)
    coachee_challenges = Column(Text)
    coachee_goals = Column(Text)
    coachee_password = Column(String)
    coachee_status = Column(Boolean, default=True)
    coachee_photo = Column(String)

    organization = relationship("CoacheeOrganization", back_populates="coachees")
    sessions = relationship("CoachingSession", back_populates="coachee")


# -----------------------
# Coaching Session
# -----------------------
class CoachingSession(Base):
    __tablename__ = "coaching_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    session_date = Column(String)
    session_coach = Column(Integer, ForeignKey("coaches.coach_id"))
    session_coachee = Column(Integer, ForeignKey("coachees.coachee_id"))
    session_coachnotes = Column(Text)
    session_topic = Column(String)
    session_coachapproach = Column(Text)
    session_goals = Column(Text)
    session_nextsteps = Column(Text)
    session_attachments = Column(String)

    coach = relationship("Coach", back_populates="sessions")
    coachee = relationship("Coachee", back_populates="sessions")
    assignments = relationship("Assignment", back_populates="session")


# -----------------------
# Assignment
# -----------------------
class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(Integer, primary_key=True, index=True)
    assignment_module = Column(String)
    assignment_description = Column(Text)
    assignment_resources = Column(String)
    assignment_duedate = Column(String)
    assignment_status = Column(String)
    assignment_coachee = Column(Integer, ForeignKey("coachees.coachee_id"))
    assignment_coach = Column(Integer, ForeignKey("coaches.coach_id"))
    assignment_session_ID_reference = Column(Integer, ForeignKey("coaching_sessions.session_id"))
    assignment_feedback = Column(Text)

    session = relationship("CoachingSession", back_populates="assignments")
