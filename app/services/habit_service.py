from sqlalchemy.orm import Session
from app.models import Habit, HabitLog
from app.schemas import HabitCreate
from app.services.habit_strategies import DailyStrategy, WeeklyStrategy
from datetime import date, timedelta

class HabitService:
    @staticmethod
    def get_habits_by_user(db: Session, user_id: int):
        return db.query(Habit).filter_by(user_id=user_id).all()

    @staticmethod
    def create_habit(db: Session, habit_data: HabitCreate, user_id: int):
        habit = Habit(**habit_data.model_dump(), user_id=user_id)
        db.add(habit)
        db.commit()
        db.refresh(habit)
        return habit

    @staticmethod
    def get_habit(db: Session, habit_id: int):
        return db.query(Habit).get(habit_id)

    @staticmethod
    def update_habit(db: Session, habit_id: int, habit_data: HabitCreate):
        habit = db.query(Habit).get(habit_id)
        if not habit:
            return None
        for field, value in habit_data.model_dump(exclude_unset=True).items():
            setattr(habit, field, value)
        db.commit()
        db.refresh(habit)
        return habit

    @staticmethod
    def delete_habit(db: Session, habit_id: int):
        habit = db.query(Habit).get(habit_id)
        if habit:
            db.delete(habit)
            db.commit()

    @staticmethod
    def get_habit_logs(db: Session, habit_id: int, start_date: date, end_date: date):
        return db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date >= start_date,
            HabitLog.date <= end_date
        ).all()

    @staticmethod
    def get_strategy(habit: Habit):
        if habit.strategy_type == 'daily':
            return DailyStrategy()
        elif habit.strategy_type == 'weekly':
            return WeeklyStrategy(habit.strategy_params['day_of_week'])
        else:
            raise ValueError(f"Unknown strategy type: {habit.strategy_type}")

    @staticmethod
    def get_habit_dates_with_status(db: Session, habit_id: int, start_date: date, end_date: date):
        habit = db.query(Habit).get(habit_id)
        if not habit:
            return {}
        logs = HabitService.get_habit_logs(db, habit_id, start_date, end_date)
        log_dates = {(log.date, log.index): log.is_done for log in logs}
        dates_with_status = {}
        delta = end_date - start_date

        frequency = 1
        if habit.strategy_type == 'daily' and habit.strategy_params and 'frequency' in habit.strategy_params:
            frequency = habit.strategy_params['frequency']

        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if frequency > 1:
                dates_with_status[day] = [log_dates.get((day, j), False) for j in range(frequency)]
            else:
                dates_with_status[day] = log_dates.get((day, 0), False)
        return dates_with_status

    @staticmethod
    def log_habit(db: Session, habit_id: int, log_date: date, is_done: bool, index: int = 0):
        log = db.query(HabitLog).filter_by(habit_id=habit_id, date=log_date, index=index).first()
        if log:
            log.is_done = is_done
        else:
            log = HabitLog(habit_id=habit_id, date=log_date, is_done=is_done, index=index)
            db.add(log)
        db.commit()
        db.refresh(log)
        return log

