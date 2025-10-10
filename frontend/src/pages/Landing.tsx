import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';

export const Landing: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingKey, setExistingKey] = useState('');
  const { setApiKey } = useGame();
  const navigate = useNavigate();

  const handleCreatePlayer = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.createPlayer();
      setApiKey(response.api_key);
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to create player');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExistingPlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!existingKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    // Store original key for restoration if test fails
    const originalKey = localStorage.getItem('wordpool_api_key');

    try {
      setIsLoading(true);
      setError(null);
      
      // Set the new key to test it
      localStorage.setItem('wordpool_api_key', existingKey.trim());
      
      // Test the API key by fetching balance
      await apiClient.getBalance();
      
      // If we get here, the API key is valid
      setApiKey(existingKey.trim());
      navigate('/dashboard');
      
    } catch (err) {
      // API key test failed - restore original key and show error
      if (originalKey && originalKey !== existingKey.trim()) {
        localStorage.setItem('wordpool_api_key', originalKey);
      } else {
        localStorage.removeItem('wordpool_api_key');
      }
      
      setError(extractErrorMessage(err) || 'Invalid API key');
      // Don't call setApiKey here since the key is invalid
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        <h1 className="text-4xl font-bold text-center mb-2 text-gray-800">
          WordPool
        </h1>
        <p className="text-center text-gray-600 mb-8">
          A multiplayer word association game
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
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors"
            >
              {isLoading ? 'Creating Account...' : 'Create New Account'}
            </button>
            <p className="text-sm text-gray-600 mt-2">
              Start with $1,000 balance
            </p>
          </div>

          {/* Returning Player */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Returning Player</h2>
            <form onSubmit={handleExistingPlayer}>
              <input
                type="text"
                value={existingKey}
                onChange={(e) => setExistingKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors"
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </button>
            </form>
            <p className="text-sm text-gray-600 mt-2">
              Enter your saved API key to continue
            </p>
          </div>
        </div>

        <div className="mt-8 text-center text-sm text-gray-600">
          <p className="font-semibold mb-2">How to Play:</p>
          <p>1. Submit words for prompts ($100)</p>
          <p>2. Copy others' words without seeing the prompt ($100)</p>
          <p>3. Vote to identify the original word ($1)</p>
        </div>
      </div>
    </div>
  );
};
