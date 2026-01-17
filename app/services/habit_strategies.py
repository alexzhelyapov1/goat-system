from abc import ABC, abstractmethod
from datetime import date, timedelta

class HabitStrategy(ABC):
    @abstractmethod
    def get_required_dates(self, start_date: date, end_date: date) -> list[date]:
        pass

class DailyStrategy(HabitStrategy):
    def get_required_dates(self, start_date: date, end_date: date) -> list[date]:
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates

class WeeklyStrategy(HabitStrategy):
    def __init__(self, day_of_week: int):
        self.day_of_week = day_of_week

    def get_required_dates(self, start_date: date, end_date: date) -> list[date]:
        dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() == self.day_of_week:
                dates.append(current_date)
            current_date += timedelta(days=1)
        return dates
