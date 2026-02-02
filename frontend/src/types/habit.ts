// frontend/src/types/habit.d.ts
export interface Habit {
  id: number;
  name: string;
  description: string | null;
  start_date: string | null; // FastAPI sends date as ISO string "YYYY-MM-DD"
  end_date: string | null;   // FastAPI sends date as ISO string "YYYY-MM-DD"
  strategy_type: string;
  strategy_params: { [key: string]: any }; // Flexible for strategy-specific parameters
  user_id: number;
}

export interface HabitLogStatus {
  [date: string]: boolean; // date string like "YYYY-MM-DD" maps to boolean status
}

// Used when fetching all habits with their logs
export interface HabitWithLogs {
  habit: Habit;
  logs: HabitLogStatus;
}
