import React, { useState } from 'react';
import axios from 'axios';
import HabitForm from './HabitForm';
import type { Habit } from '../types/habit'; // Import type for Habit

interface CreateHabitPageProps {
  token: string;
  onHabitCreated: () => void;
  onCancel: () => void;
}

const CreateHabitPage: React.FC<CreateHabitPageProps> = ({ token, onHabitCreated, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (habitData: Omit<Habit, 'id' | 'user_id'>) => {
    setLoading(true);
    setError(null);

    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
      await axios.post('/api/habits/', habitData, { headers });
      onHabitCreated(); // Notify parent that habit was created
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        setError(err.response.data.detail || 'Failed to create habit. Please check your input.');
      } else {
        setError('An unexpected error occurred during habit creation.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <HabitForm onSubmit={handleSubmit} onCancel={onCancel} loading={loading} error={error} />
    </div>
  );
};

export default CreateHabitPage;
