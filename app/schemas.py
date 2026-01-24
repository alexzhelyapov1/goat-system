from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from app.models import TaskStatus, TaskType

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserSchema(UserBase):
    id: int

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    details: Optional[str] = None
    status: TaskStatus = TaskStatus.OPEN
    type: TaskType = TaskType.INBOX
    deadline: Optional[datetime] = None
    duration: Optional[int] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    suspend_due: Optional[datetime] = None
    notify_at: Optional[datetime] = None

    @validator('notify_at', pre=True, always=True)
    def convert_notify_at_to_utc(cls, v):
        if v is None:
            return v

        moscow_tz = ZoneInfo("Europe/Moscow")

        if isinstance(v, str):
            # Attempt to parse common datetime formats
            try:
                dt_obj = datetime.fromisoformat(v)
            except ValueError:
                # Fallback for other formats, e.g., 'YYYY-MM-DD HH:MM:SS'
                try:
                    dt_obj = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError("Invalid datetime format for notify_at")
        elif isinstance(v, datetime):
            dt_obj = v
        else:
            raise TypeError("notify_at must be a datetime object or a string")

        # If naive, assume it's in Moscow timezone
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=moscow_tz)
        else:
            # If already timezone-aware, convert it to Moscow timezone first to ensure consistency
            dt_obj = dt_obj.astimezone(moscow_tz)

        # Convert to UTC for storage
        return dt_obj.astimezone(timezone.utc)



class TaskCreate(TaskBase):
    pass

class TaskSchema(TaskBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class HabitBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    strategy_type: str
    strategy_params: dict

    @validator('start_date', 'end_date', pre=True)
    def parse_date(cls, v):
        if not v:
            return None
        if isinstance(v, str):
            return datetime.strptime(v, '%Y-%m-%d').date()
        if isinstance(v, datetime):
            return v.date()
        return v

class HabitCreate(HabitBase):
    pass

class HabitSchema(HabitBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class MovieBase(BaseModel):
    title: str
    genre: Optional[str] = None
    rating: Optional[int] = None
    comment: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class MovieSchema(MovieBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class PersonBase(BaseModel):
    firstname: str
    lastname: Optional[str] = None
    sphere: Optional[str] = None
    notes: Optional[str] = None

class PersonCreate(PersonBase):
    pass

class PersonSchema(PersonBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
