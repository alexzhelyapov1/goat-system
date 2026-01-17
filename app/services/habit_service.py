from app import db
from app.models import Habit, HabitLog
from app.schemas import HabitCreate
from flask_login import current_user
from app.services.habit_strategies import DailyStrategy, WeeklyStrategy
from datetime import date, timedelta

class HabitService:
    @staticmethod
    def get_habits_by_user(user_id):
        return Habit.query.filter_by(user_id=user_id).all()

    @staticmethod
    def create_habit(habit_data: HabitCreate):
        habit = Habit(**habit_data.model_dump(), user_id=current_user.id)
        db.session.add(habit)
        db.session.commit()
        return habit

    @staticmethod
    def get_habit(habit_id):
        return Habit.query.get(habit_id)

    @staticmethod
    def update_habit(habit_id, habit_data: HabitCreate):
        habit = Habit.query.get(habit_id)
        for field, value in habit_data.model_dump().items():
            setattr(habit, field, value)
        db.session.commit()
        return habit

    @staticmethod
    def delete_habit(habit_id):
        habit = Habit.query.get(habit_id)
        db.session.delete(habit)
        db.session.commit()

    @staticmethod
    def get_habit_logs(habit_id, start_date, end_date):
        return HabitLog.query.filter(
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
    def get_habit_dates_with_status(habit_id, start_date, end_date):
        habit = Habit.query.get(habit_id)
        logs = HabitService.get_habit_logs(habit_id, start_date, end_date)
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
    def log_habit(habit_id, log_date, is_done, index=0):
        log = HabitLog.query.filter_by(habit_id=habit_id, date=log_date, index=index).first()
        if log:
            log.is_done = is_done
        else:
            log = HabitLog(habit_id=habit_id, date=log_date, is_done=is_done, index=index)
            db.session.add(log)
        db.session.commit()
        return log

