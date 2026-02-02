from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Boolean,
    JSON,
    Date
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TaskStatus(enum.Enum):
    OPEN = 'OPEN'
    DONE = 'DONE'
    ARCHIVED = 'ARCHIVED'

class TaskType(enum.Enum):
    INBOX = 'INBOX'
    CURRENT = 'CURRENT'
    SOMEDAY = 'SOMEDAY'
    CALENDAR = 'CALENDAR'
    REST = 'REST'
    ROUTINE = 'ROUTINE'

class UserRole(enum.Enum):
    USER = 'USER'
    ADMIN = 'ADMIN'
    TRUSTED = 'TRUSTED'

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), index=True, unique=True)
    password_hash = Column(String(128))
    telegram_chat_id = Column(String(64), unique=True, nullable=True)
    telegram_username = Column(String(64), nullable=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False)

    tasks = relationship('Task', back_populates='author')
    habits = relationship('Habit', back_populates='author')
    movies = relationship('Movie', back_populates='author')

    # Properties for Flask-Login compatibility
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(String(140))
    details = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.OPEN, nullable=False)
    type = Column(SQLAlchemyEnum(TaskType), default=TaskType.INBOX, nullable=False)
    deadline = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    suspend_due = Column(DateTime, nullable=True)
    notify_at = Column(DateTime, nullable=True)
    planned_start_notified = Column(Boolean, default=False, nullable=True)

    author = relationship('User', back_populates='tasks')

    def __repr__(self):
        return f'<Task {self.title}>'

class Habit(Base):
    __tablename__ = 'habit'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    name = Column(String(140))
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    strategy_type = Column(String(50), nullable=True)
    strategy_params = Column(JSON, nullable=True)

    author = relationship('User', back_populates='habits')
    habit_logs = relationship('HabitLog', back_populates='habit')

    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitLog(Base):
    __tablename__ = 'habit_log'
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey('habit.id'))
    date = Column(Date, default=datetime.utcnow)
    is_done = Column(Boolean, default=False)
    index = Column(Integer, default=0)

    habit = relationship('Habit', back_populates='habit_logs')

    def __repr__(self):
        return f'<HabitLog {self.id}>'

class Movie(Base):
    __tablename__ = 'movie'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(String(140))
    genre = Column(String(50), nullable=True)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)

    author = relationship('User', back_populates='movies')

    def __repr__(self):
        return f'<Movie {self.title}>'

