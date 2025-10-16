import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';

export const Landing: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [registerUsername, setRegisterUsername] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [loginUsername, setLoginUsername] = useState(() => apiClient.getStoredUsername() ?? '');
  const [loginPassword, setLoginPassword] = useState('');

  const { startSession } = useGame();
  const navigate = useNavigate();

  const handleCreatePlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!registerUsername.trim() || !registerEmail.trim() || !registerPassword.trim()) {
      setError('Please provide a username, email, and password to create an account.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.createPlayer({
        username: registerUsername.trim(),
        email: registerEmail.trim(),
        password: registerPassword,
      });
      startSession(response.username, response);
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to create player');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExistingPlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginUsername.trim() || !loginPassword.trim()) {
      setError('Please enter your username and password.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.login({
        username: loginUsername.trim(),
        password: loginPassword,
      });
      startSession(response.username, response);
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err) || 'Invalid username or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-xl p-8 grid gap-8 md:grid-cols-2">
        <div>
          <h1 className="text-4xl font-bold mb-4 text-gray-800">Quipflip</h1>
          <p className="text-gray-600 mb-6">A multiplayer phrase association game</p>

          {error && (
            <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Create an Account</h2>
              <form onSubmit={handleCreatePlayer} className="space-y-3">
                <input
                  type="text"
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
                  placeholder="Choose a username"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <input
                  type="email"
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  placeholder="Your email"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <input
                  type="password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  placeholder="Create a password"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                >
                  {isLoading ? 'Creating Account...' : 'Sign Up'}
                </button>
              </form>
              <p className="text-sm text-gray-600 mt-2">Start with a $1,000 balance and earn more by playing rounds.</p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Returning Players</h2>
              <form onSubmit={handleExistingPlayer} className="space-y-3">
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  placeholder="Username"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  disabled={isLoading}
                />
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                >
                  {isLoading ? 'Signing In...' : 'Login'}
                </button>
              </form>
              <p className="text-sm text-gray-600 mt-2">Forgot your password? Email support@quipflip.gg for assistance.</p>
            </div>
          </div>
        </div>

        <div className="space-y-6 text-gray-700">
          <div>
            <h3 className="text-xl font-semibold mb-2">How to Play</h3>
            <ol className="list-decimal list-inside space-y-1">
              <li>Submit clever phrases for prompts.</li>
              <li>Copy phrases without seeing the prompt.</li>
              <li>Vote to identify the original phrase and earn rewards.</li>
            </ol>
          </div>

          <div>
            <h3 className="text-xl font-semibold mb-2">Why Create an Account?</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>Secure login with your username and password.</li>
              <li>Automatic token refresh keeps you playing.</li>
              <li>Email-based account recovery coming soon.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
