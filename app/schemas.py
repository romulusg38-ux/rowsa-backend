from pydantic import BaseModel
from typing import Optional

class AthleteCreate(BaseModel):
    email: str
    full_name: str
    password: str
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    club: Optional[str] = None
    province: Optional[str] = None
    rowing_side: Optional[str] = None
    ethnicity: Optional[str] = None
    disability: Optional[str] = None
    disability_description: Optional[str] = None

class TrainingSessionCreate(BaseModel):
    date: str
    distance_m: int
    time_formatted: str
    split_500m: Optional[str] = None
    stroke_rate: Optional[int] = None
    session_type: str
    notes: Optional[str] = None