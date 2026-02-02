import React, { useState, useEffect } from 'react';
import axios from 'axios';
import type { Habit, HabitLogStatus, HabitWithLogs } from '../types/habit.ts';
import dayjs from 'dayjs'; // Using dayjs for date manipulation
import weekday from 'dayjs/plugin/weekday';
import weekOfYear from 'dayjs/plugin/weekOfYear';

dayjs.extend(weekday);
dayjs.extend(weekOfYear);

interface HabitsListPageProps {
  token: string;
}

const HabitsListPage: React.FC<HabitsListPageProps> = ({ token }) => {
  const [habitsWithLogs, setHabitsWithLogs] = useState<HabitWithLogs[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const today = dayjs();
  const dates = Array.from({ length: 7 }).map((_, i) => today.subtract(3, 'day').add(i, 'day')); // -3 to +3 days from today

  useEffect(() => {
    const fetchHabits = async () => {
      try {
        const headers = {
          Authorization: `Bearer ${token}`,
        };

        // Fetch all habits
        const habitsResponse = await axios.get<Habit[]>('/api/habits/', { headers });
        const fetchedHabits = habitsResponse.data;

        // Fetch logs for each habit concurrently
        const habitsWithLogsPromises = fetchedHabits.map(async (habit) => {
          const startDate = today.subtract(3, 'day').format('YYYY-MM-DD');
          const endDate = today.add(3, 'day').format('YYYY-MM-DD');
          const logResponse = await axios.get<HabitLogStatus>(
            `/api/habits/${habit.id}/dates-with-status?start_date=${startDate}&end_date=${endDate}`,
            { headers }
          );
          return { habit, logs: logResponse.data };
        });

        const results = await Promise.all(habitsWithLogsPromises);
        setHabitsWithLogs(results);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response) {
          setError(err.response.data.detail || 'Failed to fetch habits.');
        } else {
          setError('An unexpected error occurred.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchHabits();
  }, [token, today]); // today as dependency for useEffect to ensure recalculation if the day changes

  if (loading) {
    return <div className="text-center p-4">Loading habits...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">My Habits</h1>
      {habitsWithLogs.length === 0 ? (
        <p className="text-center text-gray-600">No habits found. Time to create some!</p>
      ) : (
        <div className="overflow-x-auto bg-white shadow-md rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Habit Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                {dates.map((dateItem) => (
                  <th
                    key={dateItem.format('YYYY-MM-DD')}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {dateItem.format('ddd DD')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {habitsWithLogs.map(({ habit, logs }) => (
                <tr key={habit.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {habit.name}
                    {habit.description && (
                      <p className="text-xs text-gray-500">{habit.description}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {habit.strategy_type}
                  </td>
                  {dates.map((dateItem) => {
                    const dateKey = dateItem.format('YYYY-MM-DD');
                    const isDone = logs[dateKey];
                    return (
                      <td key={dateKey} className="px-4 py-4 whitespace-nowrap text-center text-sm">
                        {isDone === true && <span className="text-green-500">✓</span>}
                        {isDone === false && <span className="text-red-500">✗</span>}
                        {isDone === undefined && <span className="text-gray-400">-</span>}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default HabitsListPage;
