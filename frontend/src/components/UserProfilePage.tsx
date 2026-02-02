import React from 'react';

interface User {
  id: number;
  username: string;
  is_admin: boolean;
  telegram_id: number | null;
  telegram_username: string | null;
}

interface UserProfilePageProps {
  user: User;
  onLogout: () => void;
}

const UserProfilePage: React.FC<UserProfilePageProps> = ({ user, onLogout }) => {
  return (
    <div className="p-8 bg-white shadow-md rounded-lg text-center">
      <h2 className="text-2xl font-bold mb-4">Welcome, {user.username}!</h2>
      <p>Admin: {user.is_admin ? 'Yes' : 'No'}</p>
      {user.telegram_username && <p>Telegram: @{user.telegram_username}</p>}
      <button
        onClick={onLogout}
        className="mt-6 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
      >
        Logout
      </button>
    </div>
  );
};

export default UserProfilePage;
