import React, { useState, useEffect } from 'react';
import { Habit } from '../types/habit'; // Import Habit interface

interface HabitFormProps {
  initialHabit?: Habit; // Optional, for editing existing habits
  onSubmit: (habitData: Omit<Habit, 'id' | 'user_id'>) => void;
  onCancel: () => void;
  loading: boolean;
  error: string | null;
}

const HabitForm: React.FC<HabitFormProps> = ({ initialHabit, onSubmit, onCancel, loading, error }) => {
  const [name, setName] = useState(initialHabit?.name || '');
  const [description, setDescription] = useState(initialHabit?.description || '');
  const [startDate, setStartDate] = useState(initialHabit?.start_date || '');
  const [endDate, setEndDate] = useState(initialHabit?.end_date || '');
  const [strategyType, setStrategyType] = useState(initialHabit?.strategy_type || 'daily');
  const [strategyParams, setStrategyParams] = useState(
    initialHabit?.strategy_params ? JSON.stringify(initialHabit.strategy_params, null, 2) : '{}'
  );
  const [formErrors, setFormErrors] = useState<string[]>([]);

  useEffect(() => {
    if (initialHabit) {
      setName(initialHabit.name);
      setDescription(initialHabit.description || '');
      setStartDate(initialHabit.start_date || '');
      setEndDate(initialHabit.end_date || '');
      setStrategyType(initialHabit.strategy_type);
      setStrategyParams(JSON.stringify(initialHabit.strategy_params, null, 2));
    }
  }, [initialHabit]);

  const validateForm = () => {
    const errors: string[] = [];
    if (!name.trim()) {
      errors.push('Name is required.');
    }
    try {
      JSON.parse(strategyParams);
    } catch (e) {
      errors.push('Strategy Parameters must be valid JSON.');
    }
    setFormErrors(errors);
    return errors.length === 0;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }

    const habitData: Omit<Habit, 'id' | 'user_id'> = {
      name,
      description: description || null,
      start_date: startDate || null,
      end_date: endDate || null,
      strategy_type: strategyType,
      strategy_params: JSON.parse(strategyParams),
    };
    onSubmit(habitData);
  };

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4 text-center">
        {initialHabit ? 'Edit Habit' : 'Create New Habit'}
      </h2>
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}
        {formErrors.length > 0 && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            <ul>
              {formErrors.map((err, index) => (
                <li key={index}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mb-4">
          <label htmlFor="name" className="block text-gray-700 text-sm font-bold mb-2">
            Name
          </label>
          <input
            type="text"
            id="name"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div className="mb-4">
          <label htmlFor="description" className="block text-gray-700 text-sm font-bold mb-2">
            Description
          </label>
          <textarea
            id="description"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          ></textarea>
        </div>

        <div className="mb-4">
          <label htmlFor="start_date" className="block text-gray-700 text-sm font-bold mb-2">
            Start Date
          </label>
          <input
            type="date"
            id="start_date"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <label htmlFor="end_date" className="block text-gray-700 text-sm font-bold mb-2">
            End Date
          </label>
          <input
            type="date"
            id="end_date"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <label htmlFor="strategy_type" className="block text-gray-700 text-sm font-bold mb-2">
            Strategy Type
          </label>
          <select
            id="strategy_type"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={strategyType}
            onChange={(e) => setStrategyType(e.target.value)}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>

        <div className="mb-6">
          <label htmlFor="strategy_params" className="block text-gray-700 text-sm font-bold mb-2">
            Strategy Parameters (JSON)
          </label>
          <textarea
            id="strategy_params"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            value={strategyParams}
            onChange={(e) => setStrategyParams(e.target.value)}
            rows={5}
          ></textarea>
        </div>

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            disabled={loading}
          >
            {loading ? (initialHabit ? 'Saving...' : 'Creating...') : 'Save Habit'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default HabitForm;
