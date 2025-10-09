import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient from '../api/client';
import { Timer } from '../components/Timer';
import { useTimer } from '../hooks/useTimer';
import type { PromptState } from '../api/types';

export const PromptRound: React.FC = () => {
  const { activeRound, refreshCurrentRound, refreshBalance } = useGame();
  const navigate = useNavigate();
  const [word, setWord] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roundData, setRoundData] = useState<PromptState | null>(null);

  const { isExpired } = useTimer(roundData?.expires_at || null);

  useEffect(() => {
    const initRound = async () => {
      // Check if we have an active prompt round
      if (activeRound?.round_type === 'prompt' && activeRound.state) {
        setRoundData(activeRound.state as PromptState);

        // If already submitted, redirect to dashboard
        if ((activeRound.state as PromptState).status === 'submitted') {
          navigate('/dashboard');
        }
      } else {
        // No active round, start a new one
        try {
          const response = await apiClient.startPromptRound();
          await refreshCurrentRound();
          setRoundData({
            round_id: response.round_id,
            status: 'active',
            expires_at: response.expires_at,
            cost: response.cost,
            prompt_text: response.prompt_text,
          });
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to start round');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      }
    };

    initRound();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!word.trim() || !roundData) return;

    try {
      setIsSubmitting(true);
      setError(null);
      await apiClient.submitWord(roundData.round_id, word.trim());
      await refreshCurrentRound();
      await refreshBalance();
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit word');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!roundData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading round...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Prompt Round</h1>
          <p className="text-gray-600">Submit a word for the prompt</p>
        </div>

        {/* Timer */}
        <div className="flex justify-center mb-6">
          <Timer expiresAt={roundData.expires_at} />
        </div>

        {/* Prompt */}
        <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-6 mb-6">
          <p className="text-2xl text-center font-semibold text-purple-900">
            {roundData.prompt_text}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              value={word}
              onChange={(e) => setWord(e.target.value)}
              placeholder="Enter your word"
              className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isExpired || isSubmitting}
              maxLength={15}
            />
            <p className="text-sm text-gray-600 mt-1">
              2-15 letters, A-Z only
            </p>
          </div>

          <button
            type="submit"
            disabled={isExpired || isSubmitting || !word.trim()}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
          >
            {isExpired ? "Time's Up" : isSubmitting ? 'Submitting...' : 'Submit Word'}
          </button>
        </form>

        {/* Cancel Button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="w-full mt-4 text-gray-600 hover:text-gray-800 py-2"
        >
          Back to Dashboard
        </button>

        {/* Info */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Cost:</strong> ${roundData.cost} (deducted immediately, $90 refunded if you don't submit)
          </p>
        </div>
      </div>
    </div>
  );
};
