from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import jwt
import bcrypt
from typing import Optional
import os

app = FastAPI(title="RowSA Athlete Interface")

# ==================== CORS - IMPORTANT FOR NETLIFY ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://rowsa.netlify.app",           # ← Your frontend
        "https://frolicking-mandazi-ddcc21.netlify.app",
        "*"  # ← Temporary for beta (remove later for security)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./rowsa_athletes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class AssignedWorkoutCreate(BaseModel):
    athlete_id: int
    description: str
    target_distance_m: int
    target_time_formatted: str
    due_date: Optional[str] = None
    notes: Optional[str] = None

class CompleteAssignment(BaseModel):
    actual_time_formatted: str

class TrainingSessionCreate(BaseModel):
    date: str
    distance_m: int
    time_formatted: str
    session_type: str
    stroke_rate: int
    notes: Optional[str] = None

# ====================== AUTH ======================
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Athlete).filter(Athlete.email == form_data.username).first()
    if not user or not bcrypt.checkpw(form_data.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = jwt.encode({"sub": user.email}, "supersecretkey1234567890abcdef1234567890", algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/register")
def register(data: dict, db: Session = Depends(get_db)):
    hashed = bcrypt.hashpw(data.get("password","").encode(), bcrypt.gensalt())
    
    sa_id = data.get("sa_id_number")
    passport = data.get("passport_number")
    dob = data.get("date_of_birth")
    
    temporary_id = None
    if not sa_id and passport and dob:
        base = dob.replace("-", "")[:6]  # yymmdd
        count = db.query(Athlete).filter(Athlete.temporary_id.like(f"{base}%")).count()
        temporary_id = f"{base}{str(count+1).zfill(2)}"
    
    athlete = Athlete(
        full_name=data.get("full_name"),
        email=data.get("email"),
        password_hash=hashed.decode(),
        sa_id_number=sa_id,
        temporary_id=temporary_id,
        passport_number=passport,
        date_of_birth=dob,
        club_id=data.get("club_id"),
        role="athlete",
        status="pending"
    )
    db.add(athlete)
    db.commit()
    return {"message": "Registered successfully. Awaiting club approval."}

@app.get("/profile")
def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        if not user:
            raise HTTPException(404, detail="User not found")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.put("/profile")
def update_profile(data: dict, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        if not user:
            raise HTTPException(404)
        for key, value in data.items():
            if hasattr(user, key) and key not in ["id", "password_hash"]:
                setattr(user, key, value)
        db.commit()
        return {"message": "Profile updated"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/clubs")
def get_clubs():
    return {"clubs": [
        {"id": 1, "name": "University of Pretoria"},
        {"id": 2, "name": "University of Johannesburg"},
        {"id": 3, "name": "Wits University Boat Club"}
    ]}

# ====================== VERIFY ATHLETES ======================
@app.get("/admin/pending-athletes")
def get_club_athletes(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        admin = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        if not admin or admin.role != "club_admin":
            raise HTTPException(403, detail="Not a club admin")
        athletes = db.query(Athlete).filter(Athlete.club_id == admin.club_id).all()
        return {"athletes": athletes}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ====================== SUPER ADMIN (Temporary for Beta) ======================
@app.post("/super/promote-to-admin/{user_id}")
def promote_to_admin(user_id: int, secret_key: str = "rowsa-beta-2026", db: Session = Depends(get_db)):
    """Temporary super admin endpoint - use with care"""
    if secret_key != "rowsa-beta-2026":   # Change this secret later
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    user = db.query(Athlete).filter(Athlete.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = "club_admin"
    db.commit()
    
    return {
        "message": f"User {user.full_name} ({user.email}) promoted from '{old_role}' to 'club_admin'",
        "user_id": user.id,
        "email": user.email
    }

@app.post("/admin/approve-athlete/{athlete_id}")
def approve_athlete(athlete_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        admin = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
        if not athlete or athlete.club_id != admin.club_id:
            raise HTTPException(404, detail="Athlete not found")
        athlete.status = "approved"
        athlete.approved_at = datetime.utcnow()
        db.commit()
        return {"message": "Athlete approved"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/admin/remove-from-club/{athlete_id}")
def remove_from_club(athlete_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        admin = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
        if not athlete or athlete.club_id != admin.club_id:
            raise HTTPException(404, detail="Athlete not found")
        athlete.club_id = None
        athlete.status = "unaffiliated"
        db.commit()
        return {"message": "Athlete removed from club"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ====================== TRAINING ======================
@app.post("/training")
def log_training(session: TrainingSessionCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        new_session = TrainingSession(athlete_id=user.id, **session.dict())
        db.add(new_session)
        db.commit()
        return {"message": "Session logged", "session_id": new_session.id}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/training")
def get_training(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        sessions = db.query(TrainingSession).filter(TrainingSession.athlete_id == user.id).all()
        return {"sessions": sessions}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/training/{session_id}/send-for-verification")
def send_for_verification(session_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id, TrainingSession.athlete_id == user.id).first()
        if not session:
            raise HTTPException(404, detail="Session not found")
        session.verification_status = "pending_verification"
        db.commit()
        return {"message": "Session sent for verification"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/training/pending-verification")
def get_pending_verification(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        admin = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        if not admin or admin.role != "club_admin":
            raise HTTPException(403, detail="Not a club admin")
        sessions = db.query(TrainingSession).join(Athlete).filter(
            Athlete.club_id == admin.club_id,
            TrainingSession.verification_status == "pending_verification"
        ).all()
        return {"sessions": sessions}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/training/{session_id}/approve")
def approve_training(session_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        admin = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        if not admin or admin.role != "club_admin":
            raise HTTPException(403, detail="Not a club admin")
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if not session:
            raise HTTPException(404, detail="Session not found")
        session.verification_status = "approved"
        db.commit()
        return {"message": "Training approved"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/training/{session_id}/reject")
def reject_training(session_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        admin = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        if not admin or admin.role != "club_admin":
            raise HTTPException(403, detail="Not a club admin")
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if not session:
            raise HTTPException(404, detail="Session not found")
        session.verification_status = "rejected"
        db.commit()
        return {"message": "Training rejected"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ====================== ASSIGNED TRAINING ======================
@app.post("/coach/assign-workout")
def assign_workout(workout: AssignedWorkoutCreate, db: Session = Depends(get_db)):
    new_w = AssignedWorkout(**workout.dict())
    db.add(new_w)
    db.commit()
    return {"message": "Assigned successfully"}

@app.get("/athlete/assigned-workouts")
def get_assigned_workouts(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        workouts = db.query(AssignedWorkout).filter(AssignedWorkout.athlete_id == user.id).all()
        return {"workouts": workouts}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/athlete/complete-assignment/{assignment_id}")
def complete_assignment(assignment_id: int, data: CompleteAssignment, db: Session = Depends(get_db)):
    workout = db.query(AssignedWorkout).filter(AssignedWorkout.id == assignment_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Assignment not found")
    workout.status = "completed"
    db.commit()
    return {"message": "Completed successfully"}

@app.post("/athlete/request-club-transfer")
def request_club_transfer(data: dict, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "supersecretkey1234567890abcdef1234567890", algorithms=["HS256"])
        user = db.query(Athlete).filter(Athlete.email == payload.get("sub")).first()
        user.club_id = data.get("new_club_id")
        user.status = "pending"
        db.commit()
        return {"message": "Transfer request processed - club updated"}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ====================== UPDATED START COMMAND ======================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)