from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='author', lazy='dynamic')
    habits = db.relationship('Habit', backref='author', lazy='dynamic')
    movies = db.relationship('Movie', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    details = db.Column(db.Text)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.OPEN)
    type = db.Column(db.Enum(TaskType), default=TaskType.INBOX)
    deadline = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    planned_start = db.Column(db.DateTime)
    planned_end = db.Column(db.DateTime)
    suspend_due = db.Column(db.DateTime)
    notify_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Task {self.title}>'

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(140))
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    strategy_type = db.Column(db.String(50))
    strategy_params = db.Column(db.JSON)
    habit_logs = db.relationship('HabitLog', backref='habit', lazy='dynamic')

    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    is_done = db.Column(db.Boolean, default=False)
    index = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<HabitLog {self.id}>'

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    genre = db.Column(db.String(50))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)

    def __repr__(self):
        return f'<Movie {self.title}>'

