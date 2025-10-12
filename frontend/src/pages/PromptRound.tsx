import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';
import { Timer } from '../components/Timer';
import { useTimer } from '../hooks/useTimer';
import type { PromptState } from '../api/types';

export const PromptRound: React.FC = () => {
  const { activeRound, refreshCurrentRound, refreshBalance } = useGame();
  const navigate = useNavigate();
  const [phrase, setPhrase] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roundData, setRoundData] = useState<PromptState | null>(null);
  const [feedbackType, setFeedbackType] = useState<'like' | 'dislike' | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const hasInitialized = useRef(false);

  const { isExpired } = useTimer(roundData?.expires_at || null);

  useEffect(() => {
    // Prevent duplicate calls in React StrictMode
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const initRound = async () => {
      // Check if we have an active prompt round
      if (activeRound?.round_type === 'prompt' && activeRound.state) {
        const promptState = activeRound.state as PromptState;
        setRoundData(promptState);

        // Load existing feedback
        try {
          const feedbackResponse = await apiClient.getPromptFeedback(promptState.round_id);
          setFeedbackType(feedbackResponse.feedback_type);
        } catch (err) {
          // Feedback not found is ok, just leave as null
          console.log('No existing feedback found');
        }

        // If already submitted, redirect to dashboard
        if (promptState.status === 'submitted') {
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
          setError(extractErrorMessage(err) || 'Failed to start round');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      }
    };

    initRound();
  }, [activeRound, navigate, refreshCurrentRound]);

  const handleFeedback = async (type: 'like' | 'dislike') => {
    if (!roundData || isSubmittingFeedback) return;

    // Toggle off if clicking the same feedback type
    const newFeedbackType = feedbackType === type ? null : type;

    try {
      setIsSubmittingFeedback(true);

      if (newFeedbackType === null) {
        // For now, we just keep the last feedback since backend doesn't support deletion
        // In a future version, we could add a DELETE endpoint
        return;
      }

      await apiClient.submitPromptFeedback(roundData.round_id, newFeedbackType);
      setFeedbackType(newFeedbackType);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      // Don't show error to user, feedback is optional
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

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
    <div className="min-h-screen bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Prompt Round</h1>
          <p className="text-gray-600">Submit a phrase for the prompt</p>
        </div>

        {/* Timer */}
        <div className="flex justify-center mb-6">
          <Timer expiresAt={roundData.expires_at} />
        </div>

        {/* Prompt */}
        <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-6 mb-6 relative">
          <p className="text-2xl text-center font-semibold text-purple-900">
            {roundData.prompt_text}
          </p>

          {/* Feedback Icons */}
          <div className="absolute top-4 right-4 flex gap-2">
            <button
              onClick={() => handleFeedback('like')}
              disabled={isSubmittingFeedback || roundData.status === 'submitted'}
              className={`text-2xl transition-all ${
                feedbackType === 'like'
                  ? 'opacity-100 scale-110'
                  : 'opacity-40 hover:opacity-70 hover:scale-105'
              } disabled:opacity-30 disabled:cursor-not-allowed`}
              title="I like this prompt"
              aria-label="Like this prompt"
            >
              👍
            </button>
            <button
              onClick={() => handleFeedback('dislike')}
              disabled={isSubmittingFeedback || roundData.status === 'submitted'}
              className={`text-2xl transition-all ${
                feedbackType === 'dislike'
                  ? 'opacity-100 scale-110'
                  : 'opacity-40 hover:opacity-70 hover:scale-105'
              } disabled:opacity-30 disabled:cursor-not-allowed`}
              title="I dislike this prompt"
              aria-label="Dislike this prompt"
            >
              👎
            </button>
          </div>
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
              className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isExpired || isSubmitting}
              maxLength={100}
            />
            <p className="text-sm text-gray-600 mt-1">
              1-5 words (2-100 characters), A-Z and spaces only
            </p>
          </div>

          <button
            type="submit"
            disabled={isExpired || isSubmitting || !phrase.trim()}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
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
            <strong>Cost:</strong> ${roundData.cost} ($95 refunded if you don't submit in time)
          </p>
        </div>
      </div>
    </div>
  );
};
