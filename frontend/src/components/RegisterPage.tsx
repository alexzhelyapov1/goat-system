import React, { useState } from 'react';
import axios from 'axios';

interface RegisterPageProps {
  onRegisterSuccess: () => void;
  onRegisterError: (error: string) => void;
  onLoginClick: () => void; // Callback to switch to login view
}

const RegisterPage: React.FC<RegisterPageProps> = ({ onRegisterSuccess, onRegisterError, onLoginClick }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    onRegisterError(''); // Clear previous errors

    if (password !== confirmPassword) {
      onRegisterError('Passwords do not match.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post('/api/auth/register', {
        username,
        password,
      });

      if (response.status === 201) {
        onRegisterSuccess(); // Inform parent component
      } else {
        onRegisterError('Registration failed: Unexpected status.');
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        onRegisterError(err.response.data.detail || 'Registration failed. Please try again.');
      } else {
        onRegisterError('An unexpected error occurred during registration.');
      }
    }
    finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="p-8 bg-white shadow-md rounded-lg w-96">
        <h2 className="text-2xl font-bold mb-4 text-center">Register</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block text-gray-700 text-sm font-bold mb-2">
              Username
            </label>
            <input
              type="text"
              id="username"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="password" className="block text-gray-700 text-sm font-bold mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="mb-6">
            <label htmlFor="confirmPassword" className="block text-gray-700 text-sm font-bold mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <div className="flex items-center justify-between">
            <button
              type="submit"
              className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
              disabled={loading}
            >
              {loading ? 'Registering...' : 'Register'}
            </button>
          </div>
        </form>
        <p className="mt-4 text-center text-sm">
          Already have an account?{' '}
          <button
            onClick={onLoginClick}
            className="text-blue-500 hover:text-blue-800 font-bold focus:outline-none"
          >
            Login
          </button>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
