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

class TaskCreate(TaskBase):
    @validator('deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at', pre=False, always=True)
    def normalize_datetimes_to_utc(cls, v):
        if v and v.tzinfo:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class TaskSchema(TaskBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class HabitBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    strategy_type: str
    strategy_params: dict

    @validator('start_date', 'end_date', pre=False, always=True)
    def normalize_datetimes_to_utc(cls, v):
        if v and v.tzinfo:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

class HabitCreate(HabitBase):
    pass

class HabitSchema(HabitBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class HabitLogBase(BaseModel):
    habit_id: int
    date: date
    is_done: bool
    index: int = 0

    @validator('date', pre=True)
    def parse_date_only(cls, v):
        if isinstance(v, datetime):
            return v.date()
        return v

class HabitLogCreate(HabitLogBase):
    pass

class HabitLogSchema(HabitLogBase):
    id: int

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
