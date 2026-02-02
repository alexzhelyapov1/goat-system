import { useState, useEffect } from 'react';
import axios from 'axios';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage'; // Import RegisterPage

interface User {
  id: number;
  username: string;
  is_admin: boolean;
  telegram_id: number | null;
  telegram_username: string | null;
}

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [authMessage, setAuthMessage] = useState<string | null>(null); // Use a single message for login/register errors/success
  const [loadingUser, setLoadingUser] = useState(false);
  const [showRegisterPage, setShowRegisterPage] = useState(false); // New state to toggle between Login and Register

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
          setAuthMessage(null); // Clear messages on successful user fetch
        } catch (err) {
          if (axios.isAxiosError(err) && err.response && err.response.status === 401) {
            setAuthMessage('Session expired. Please log in again.');
            setToken(null); // Clear invalid token
          } else if (axios.isAxiosError(err) && err.message) {
            setAuthMessage(`Failed to fetch user: ${err.message}`);
          } else {
            setAuthMessage('An unknown error occurred while fetching user data.');
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
    setAuthMessage(null);
    setShowRegisterPage(false); // Ensure login view is off
  };

  const handleLoginError = (error: string) => {
    setAuthMessage(error);
    setToken(null);
    setUser(null);
  };

  const handleRegisterSuccess = () => {
    setAuthMessage('Registration successful! Please log in.');
    setShowRegisterPage(false); // Switch to login page after successful registration
  };

  const handleRegisterError = (error: string) => {
    setAuthMessage(error);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setAuthMessage(null);
    setShowRegisterPage(false); // Default to login view
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
        // User is not logged in, show login or register page
        <>
          {authMessage && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded relative" role="alert">
              <span className="block sm:inline">{authMessage}</span>
            </div>
          )}
          {showRegisterPage ? (
            <RegisterPage
              onRegisterSuccess={handleRegisterSuccess}
              onRegisterError={handleRegisterError}
              onLoginClick={() => setShowRegisterPage(false)}
            />
          ) : (
            <LoginPage
              onLoginSuccess={handleLoginSuccess}
              onLoginError={handleLoginError}
              onRegisterClick={() => setShowRegisterPage(true)} // Pass new prop to LoginPage
            />
          )}
        </>
      )}
    </div>
  );
}

export default App;
