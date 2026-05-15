from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Athlete(Base):
    __tablename__ = "athletes"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    sa_id_number = Column(String, nullable=True)
    temporary_id = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)
    date_of_birth = Column(String)
    address = Column(String)
    phone = Column(String)
    gender = Column(String)
    ethnicity = Column(String)
    disability = Column(String, default="No")
    disability_description = Column(String)
    club_id = Column(Integer)
    role = Column(String, default="athlete")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

class AssignedWorkout(Base):
    __tablename__ = "assigned_workouts"
    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"))
    description = Column(String)
    target_distance_m = Column(Integer)
    target_time_formatted = Column(String)
    due_date = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(String, default="assigned")
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"))
    date = Column(String)
    distance_m = Column(Integer)
    time_formatted = Column(String)
    session_type = Column(String)
    stroke_rate = Column(Integer)
    notes = Column(String)
    verification_status = Column(String, default="unverified")
    created_at = Column(DateTime, default=datetime.utcnow)