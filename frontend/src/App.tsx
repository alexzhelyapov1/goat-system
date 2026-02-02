import { useState, useEffect } from 'react';
import axios from 'axios';
import LoginPage from './components/LoginPage';

interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  telegram_id: number | null;
  telegram_username: string | null;
}

function App() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(false);

  // Health Check Effect
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get('/api/health');
        if (response.data.status === 'ok') {
          setIsHealthy(true);
        } else {
          setIsHealthy(false);
          setHealthError('Unexpected health status');
        }
      } catch (err) {
        setIsHealthy(false);
        if (axios.isAxiosError(err) && err.message) {
          setHealthError(err.message);
        } else {
          setHealthError('An unknown error occurred during health check.');
        }
      }
    };

    checkHealth();
  }, []);

  // Fetch User Data Effect
  useEffect(() => {
    if (token) {
      setLoadingUser(true);
      const fetchUser = async () => {
        try {
          const response = await axios.get('/api/auth/me', {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          setUser(response.data);
          setLoginError(null); // Clear login error on successful user fetch
        } catch (err) {
          if (axios.isAxiosError(err) && err.response && err.response.status === 401) {
            setLoginError('Session expired. Please log in again.');
            setToken(null); // Clear invalid token
          } else if (axios.isAxiosError(err) && err.message) {
            setLoginError(`Failed to fetch user: ${err.message}`);
          } else {
            setLoginError('An unknown error occurred while fetching user data.');
          }
          setUser(null);
        } finally {
          setLoadingUser(false);
        }
      };
      fetchUser();
    } else {
      setUser(null); // Clear user if no token
    }
  }, [token]);

  const handleLoginSuccess = (newToken: string) => {
    setToken(newToken);
    setLoginError(null);
  };

  const handleLoginError = (error: string) => {
    setLoginError(error);
    setToken(null);
    setUser(null);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setLoginError(null);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
      {token && user ? (
        // User is logged in
        <div className="p-8 bg-white shadow-md rounded-lg text-center">
          <h2 className="text-2xl font-bold mb-4">Welcome, {user.username}!</h2>
          {loadingUser && <p className="text-blue-500">Loading user data...</p>}
          {!loadingUser && (
            <>
              <p>Email: {user.email}</p>
              <p>Admin: {user.is_admin ? 'Yes' : 'No'}</p>
              {user.telegram_username && <p>Telegram: @{user.telegram_username}</p>}
            </>
          )}
          <button
            onClick={handleLogout}
            className="mt-6 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            Logout
          </button>
        </div>
      ) : (
        // User is not logged in, show login page
        <>
          {loginError && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded relative" role="alert">
              <span className="block sm:inline">{loginError}</span>
            </div>
          )}
          <LoginPage onLoginSuccess={handleLoginSuccess} onLoginError={handleLoginError} />
        </>
      )}
    </div>
  );
}

export default App;
