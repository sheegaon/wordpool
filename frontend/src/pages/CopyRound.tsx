import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';
import { Timer } from '../components/Timer';
import { useTimer } from '../hooks/useTimer';
import type { CopyState } from '../api/types';

export const CopyRound: React.FC = () => {
  const { activeRound, refreshCurrentRound, refreshBalance } = useGame();
  const navigate = useNavigate();
  const [phrase, setPhrase] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roundData, setRoundData] = useState<CopyState | null>(null);
  const hasInitialized = useRef(false);

  const { isExpired } = useTimer(roundData?.expires_at || null);

  useEffect(() => {
    // Prevent duplicate calls in React StrictMode
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const initRound = async () => {
      // Check if we have an active copy round
      if (activeRound?.round_type === 'copy' && activeRound.state) {
        setRoundData(activeRound.state as CopyState);

        // If already submitted, redirect to dashboard
        if ((activeRound.state as CopyState).status === 'submitted') {
          navigate('/dashboard');
        }
      } else {
        // No active round, start a new one
        try {
          const response = await apiClient.startCopyRound();
          await refreshCurrentRound();
          setRoundData({
            round_id: response.round_id,
            status: 'active',
            expires_at: response.expires_at,
            cost: response.cost,
            original_phrase: response.original_phrase,
            discount_active: response.discount_active,
          });
        } catch (err) {
          setError(extractErrorMessage(err) || 'Failed to start round');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      }
    };

    initRound();
  }, [activeRound, navigate, refreshCurrentRound]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phrase.trim() || !roundData) return;

    try {
      setIsSubmitting(true);
      setError(null);
      await apiClient.submitPhrase(roundData.round_id, phrase.trim());
      await refreshCurrentRound();
      await refreshBalance();
      navigate('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to submit phrase');
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
    <div className="min-h-screen bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Copy Round</h1>
          <p className="text-gray-600">Submit a similar phrase</p>
        </div>

        {/* Timer */}
        <div className="flex justify-center mb-6">
          <Timer expiresAt={roundData.expires_at} />
        </div>

        {/* Original Phrase */}
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 mb-6">
          <p className="text-sm text-green-700 mb-2 text-center">Original Phrase:</p>
          <p className="text-3xl text-center font-bold text-green-900">
            {roundData.original_phrase}
          </p>
        </div>

        {/* Instructions */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-yellow-800">
            <strong>⚠️ Important:</strong> You don't know the prompt! Submit a phrase that could be similar or related to the original phrase.
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
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              placeholder="Enter your phrase"
              className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              disabled={isExpired || isSubmitting}
              maxLength={100}
            />
            <p className="text-sm text-gray-600 mt-1">
              1-5 words (2-100 characters), A-Z and spaces only, must be different from the original
            </p>
          </div>

          <button
            type="submit"
            disabled={isExpired || isSubmitting || !phrase.trim()}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
          >
            {isExpired ? "Time's Up" : isSubmitting ? 'Submitting...' : 'Submit Phrase'}
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
            <strong>Cost:</strong> ${roundData.cost}
            {roundData.discount_active && (
              <span className="text-green-600 font-semibold"> (10% discount!)</span>
            )}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            If you don't submit, ${roundData.discount_active ? 81 : 90} will be refunded (${roundData.discount_active ? 9 : 10} penalty)
          </p>
        </div>
      </div>
    </div>
  );
};
