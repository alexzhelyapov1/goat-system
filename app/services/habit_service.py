from app.models import Habit, HabitLog
from app.schemas import HabitCreate
from app.services.habit_strategies import DailyStrategy, WeeklyStrategy
from datetime import date, timedelta
from sqlalchemy.orm import Session

class HabitService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_habits_by_user(self, user_id):
        return self.db_session.query(Habit).filter_by(user_id=user_id).all()

    def create_habit(self, habit_data: HabitCreate, user_id: int):
        habit = Habit(**habit_data.model_dump(), user_id=user_id)
        self.db_session.add(habit)
        self.db_session.commit()
        self.db_session.refresh(habit) # Refresh the habit to get its ID after commit
        return habit

    def get_habit(self, habit_id):
        return self.db_session.query(Habit).get(habit_id)

    def update_habit(self, habit_id, habit_data: HabitCreate):
        habit = self.db_session.query(Habit).get(habit_id)
        if not habit:
            return None
        for field, value in habit_data.model_dump().items():
            setattr(habit, field, value)
        self.db_session.commit()
        self.db_session.refresh(habit)
        return habit

    def delete_habit(self, habit_id):
        habit = self.db_session.query(Habit).get(habit_id)
        if habit:
            self.db_session.delete(habit)
            self.db_session.commit()
        return habit # Return the deleted habit or None

    def get_habit_logs(self, habit_id, start_date, end_date):
        return self.db_session.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date >= start_date,
            HabitLog.date <= end_date
        ).all()

    def get_strategy(self, habit: Habit):
        if habit.strategy_type == 'daily':
            return DailyStrategy()
        elif habit.strategy_type == 'weekly':
            return WeeklyStrategy(habit.strategy_params['day_of_week'])
        else:
            raise ValueError(f"Unknown strategy type: {habit.strategy_type}")

    def get_habit_dates_with_status(self, habit_id, start_date, end_date):
        habit = self.db_session.query(Habit).get(habit_id)
        if not habit:
            return {}
        logs = self.get_habit_logs(habit_id, start_date, end_date)
        log_dates = {(log.date, log.index): log.is_done for log in logs}
        dates_with_status = {}
        delta = end_date - start_date

        frequency = 1
        # Check if strategy_params exists and contains 'frequency' for daily strategy
        if habit.strategy_type == 'daily' and habit.strategy_params and 'frequency' in habit.strategy_params:
            frequency = habit.strategy_params['frequency']

        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if frequency > 1:
                dates_with_status[day] = [log_dates.get((day, j), False) for j in range(frequency)]
            else:
                dates_with_status[day] = log_dates.get((day, 0), False)
        return dates_with_status

    def log_habit(self, habit_id, log_date, is_done, index=0):
        log = self.db_session.query(HabitLog).filter_by(habit_id=habit_id, date=log_date, index=index).first()
        if log:
            log.is_done = is_done
        else:
            log = HabitLog(habit_id=habit_id, date=log_date, is_done=is_done, index=index)
            self.db_session.add(log)
        self.db_session.commit()
        self.db_session.refresh(log)
        return log

