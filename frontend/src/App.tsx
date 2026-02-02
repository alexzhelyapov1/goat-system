import { useState, useEffect } from 'react';
import axios from 'axios';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import HabitsListPage from './components/HabitsListPage';
import CreateHabitPage from './components/CreateHabitPage'; // Import CreateHabitPage

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
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(false);
  const [showRegisterPage, setShowRegisterPage] = useState(false);
  const [showCreateHabitPage, setShowCreateHabitPage] = useState(false); // New state for creating habit

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
          setAuthMessage(null);
        } catch (err) {
          if (axios.isAxiosError(err) && err.response && err.response.status === 401) {
            setAuthMessage('Session expired. Please log in again.');
            setToken(null);
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
      setUser(null);
    }
  }, [token]);

  const handleLoginSuccess = (newToken: string) => {
    setToken(newToken);
    setAuthMessage(null);
    setShowRegisterPage(false);
    setShowCreateHabitPage(false); // Reset habit creation view
  };

  const handleLoginError = (error: string) => {
    setAuthMessage(error);
    setToken(null);
    setUser(null);
  };

  const handleRegisterSuccess = () => {
    setAuthMessage('Registration successful! Please log in.');
    setShowRegisterPage(false);
  };

  const handleRegisterError = (error: string) => {
    setAuthMessage(error);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setAuthMessage(null);
    setShowRegisterPage(false);
    setShowCreateHabitPage(false); // Reset habit creation view
  };

  const handleHabitCreated = () => {
    setShowCreateHabitPage(false); // Go back to list after creation
    // Optionally, trigger a refresh of habits list if it were using a global state or context
  };

  const handleCancelCreateHabit = () => {
    setShowCreateHabitPage(false); // Go back to list
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
      {token && user ? (
        // User is logged in
        <>
          {authMessage && ( // Display messages like "Habit created successfully!"
            <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded relative" role="alert">
              <span className="block sm:inline">{authMessage}</span>
            </div>
          )}
          {loadingUser && <p className="text-blue-500">Loading user data...</p>}
          {!loadingUser && (
            showCreateHabitPage ? (
              <CreateHabitPage
                token={token}
                onHabitCreated={() => {
                  handleHabitCreated();
                  setAuthMessage('Habit created successfully!'); // Set success message
                }}
                onCancel={handleCancelCreateHabit}
              />
            ) : (
              <HabitsListPage token={token} onCreateHabit={() => setShowCreateHabitPage(true)} />
            )
          )}
        </>
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
              onRegisterClick={() => setShowRegisterPage(true)}
            />
          )}
        </>
      )}
    </div>
  );
}

export default App;
