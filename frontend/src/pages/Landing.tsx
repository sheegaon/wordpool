import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';

export const Landing: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [returningUsername, setReturningUsername] = useState(
    () => localStorage.getItem('quipflip_username') ?? ''
  );
  const { setApiKey } = useGame();
  const navigate = useNavigate();

  const handleCreatePlayer = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.createPlayer();
      setApiKey(response.api_key, response.username);
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to create player');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExistingPlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returningUsername.trim()) {
      setError('Please enter your username');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.loginWithUsername(returningUsername.trim());
      setApiKey(response.api_key, response.username);
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err) || 'We could not find that username');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-quip-orange to-quip-turquoise flex items-center justify-center p-4 bg-pattern">
      <div className="max-w-md w-full tile-card p-8 animate-slide-up">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img
            src="/quipflip_logo_horizontal_transparent.png"
            alt="Quipflip"
            className="h-24 w-auto"
          />
        </div>

        <p className="text-center text-quip-teal mb-8 text-sm">
          A multiplayer phrase association game
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* New Player */}
          <div className="border-b pb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">New Player</h2>
            <button
              onClick={handleCreatePlayer}
              disabled={isLoading}
              className="w-full bg-quip-turquoise hover:bg-quip-teal disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-tile transition-all hover:shadow-tile-sm transform hover:-translate-y-0.5"
            >
              {isLoading ? 'Creating Account...' : 'Create New Account'}
            </button>
            <p className="text-sm text-quip-teal mt-2">
              Start with 1,000 Flipcoins
            </p>
          </div>

          {/* Returning Player */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Returning Player</h2>
            <form onSubmit={handleExistingPlayer}>
              <input
                type="text"
                value={returningUsername}
                onChange={(e) => setReturningUsername(e.target.value)}
                placeholder="Enter your username"
                className="w-full px-4 py-2 border border-gray-300 rounded-tile mb-3 focus:outline-none focus:ring-2 focus:ring-quip-turquoise"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-quip-orange hover:bg-quip-orange-deep disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-tile transition-all hover:shadow-tile-sm transform hover:-translate-y-0.5"
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </button>
            </form>
            <p className="text-sm text-gray-600 mt-2">
              Enter the username shown on your dashboard to continue
            </p>
          </div>
        </div>

        <div className="mt-8 text-center text-sm text-quip-navy">
          <p className="font-display font-semibold mb-2">How to Play:</p>
          <p className="text-quip-teal">1. Submit phrases for prompts</p>
          <p className="text-quip-teal">2. Copy others' phrases without seeing the prompt</p>
          <p className="text-quip-teal">3. Vote to identify the original phrase</p>
        </div>
      </div>
    </div>
  );
};
