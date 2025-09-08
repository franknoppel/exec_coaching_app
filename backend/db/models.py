from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Enum, String, Integer, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): ...
RoleEnum = Enum("admin","org_admin","coach","coachee", name="role_enum", native_enum=False)
OrgTypeEnum = Enum("coach","coachee", name="org_type_enum", native_enum=False)
ActiveEnum = Enum("active","inactive", name="active_enum", native_enum=False)
ProgressEnum = Enum("not_started","ongoing","completed", name="progress_enum", native_enum=False)

class IDMixin: id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
class SoftDeleteMixin: deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="user"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(RoleEnum, nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(ActiveEnum, default="active", nullable=False, index=True)
    photo_path: Mapped[Optional[str]] = mapped_column(String(500))

class Organization(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="organization"
    org_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    org_type: Mapped[str] = mapped_column(OrgTypeEnum, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    logo_path: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(ActiveEnum, default="active", nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

class Membership(TimestampMixin, Base):
    __tablename__="membership"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organization.org_id", ondelete="CASCADE"), primary_key=True)
    role_in_org: Mapped[Optional[str]] = mapped_column(String(50), index=True)
Index("ix_membership_user_org", Membership.user_id, Membership.org_id)

class CoachProfile(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="coach_profile"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    qualifications: Mapped[Optional[str]] = mapped_column(Text)
    profile: Mapped[Optional[str]] = mapped_column(Text)

class CoacheeProfile(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="coachee_profile"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organization.org_id", ondelete="RESTRICT"), nullable=False, index=True)
    background: Mapped[Optional[str]] = mapped_column(Text)
    education: Mapped[Optional[str]] = mapped_column(Text)
    challenges: Mapped[Optional[str]] = mapped_column(Text)
    goals: Mapped[Optional[str]] = mapped_column(Text)

class CoachingSession(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="coaching_session"
    session_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    coach_user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    coachee_user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255))
    coach_notes: Mapped[Optional[str]] = mapped_column(Text)
    approach: Mapped[Optional[str]] = mapped_column(Text)
    forward_goals: Mapped[Optional[str]] = mapped_column(Text)
    next_steps: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(ProgressEnum, default="not_started", nullable=False, index=True)

class TrainingModule(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="training_module"
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

class ModuleAssignment(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="module_assignment"
    module_id: Mapped[int] = mapped_column(ForeignKey("training_module.id", ondelete="RESTRICT"), nullable=False, index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(ProgressEnum, default="not_started", nullable=False, index=True)
    coachee_user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True)
    coach_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.user_id", ondelete="SET NULL"), index=True)

class FeedbackTemplate(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="feedback_template"
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

class FeedbackForm(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__="feedback_form"
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(ProgressEnum, default="not_started", nullable=False, index=True)
    coachee_user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True)
    coach_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.user_id", ondelete="SET NULL"), index=True)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("feedback_template.id", ondelete="SET NULL"), index=True)
    content: Mapped[Optional[str]] = mapped_column(Text)

class CoachCoachee(TimestampMixin, Base):
    __tablename__="coach_coachee"
    coach_user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
    coachee_user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), primary_key=True)
Index("ix_coach_coachee_pair", CoachCoachee.coach_user_id, CoachCoachee.coachee_user_id)
