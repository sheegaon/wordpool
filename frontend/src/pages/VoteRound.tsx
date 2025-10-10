import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';
import { Timer } from '../components/Timer';
import { useTimer } from '../hooks/useTimer';
import type { VoteState, VoteResponse } from '../api/types';

export const VoteRound: React.FC = () => {
  const { activeRound, refreshCurrentRound, refreshBalance, refreshPendingResults } = useGame();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roundData, setRoundData] = useState<VoteState | null>(null);
  const [voteResult, setVoteResult] = useState<VoteResponse | null>(null);
  const hasInitialized = useRef(false);

  const { isExpired } = useTimer(roundData?.expires_at || null);

  useEffect(() => {
    // Prevent duplicate calls in React StrictMode
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const initRound = async () => {
      // Check if we have an active vote round
      if (activeRound?.round_type === 'vote' && activeRound.state) {
        const state = activeRound.state as VoteState;
        setRoundData(state);

        // If already submitted, redirect to dashboard
        if (state.status === 'submitted') {
          navigate('/dashboard');
        }
      } else {
        // No active round, start a new one
        try {
          const response = await apiClient.startVoteRound();
          await refreshCurrentRound();
          setRoundData({
            round_id: response.round_id,
            status: 'active',
            expires_at: response.expires_at,
            wordset_id: response.wordset_id,
            prompt_text: response.prompt_text,
            words: response.words,
          });
        } catch (err) {
          setError(extractErrorMessage(err) || 'Failed to start round');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      }
    };

    initRound();
  }, [activeRound, navigate, refreshCurrentRound]);

  const handleVote = async (word: string) => {
    if (!roundData || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setError(null);
      const result = await apiClient.submitVote(roundData.wordset_id, word);
      setVoteResult(result);
      await refreshCurrentRound();
      await refreshBalance();
      await refreshPendingResults();

      // Show result for 3 seconds, then redirect
      setTimeout(() => {
        navigate('/dashboard');
      }, 3000);
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to submit vote');
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

  // Show vote result
  if (voteResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8 text-center">
          <div className={`text-6xl mb-4 ${voteResult.correct ? 'text-green-500' : 'text-red-500'}`}>
            {voteResult.correct ? '✓' : '✗'}
          </div>
          <h2 className={`text-3xl font-bold mb-4 ${voteResult.correct ? 'text-green-600' : 'text-red-600'}`}>
            {voteResult.correct ? 'Correct!' : 'Incorrect'}
          </h2>
          <p className="text-xl text-gray-700 mb-2">
            The original word was: <strong>{voteResult.original_word}</strong>
          </p>
          <p className="text-xl text-gray-700 mb-4">
            You chose: <strong>{voteResult.your_choice}</strong>
          </p>
          {voteResult.correct && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-2xl font-bold text-green-600">
                +${voteResult.payout}
              </p>
              <p className="text-sm text-green-700">Nice job!</p>
            </div>
          )}
          <p className="text-sm text-gray-500 mt-6">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Vote Round</h1>
          <p className="text-gray-600">Identify the original word</p>
        </div>

        {/* Timer */}
        <div className="flex justify-center mb-6">
          <Timer expiresAt={roundData.expires_at} />
        </div>

        {/* Prompt */}
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-6">
          <p className="text-sm text-blue-700 mb-2 text-center">Prompt:</p>
          <p className="text-2xl text-center font-semibold text-blue-900">
            {roundData.prompt_text}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Word Choices */}
        <div className="space-y-4 mb-6">
          <p className="text-center text-gray-700 font-semibold mb-4">
            Which word is the original?
          </p>
          {roundData.words.map((word) => (
            <button
              key={word}
              onClick={() => handleVote(word)}
              disabled={isExpired || isSubmitting}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-4 px-6 rounded-lg transition-colors text-xl"
            >
              {word}
            </button>
          ))}
        </div>

        {isExpired && (
          <div className="text-center text-red-600 font-semibold">
            Time's up! You forfeited $1
          </div>
        )}

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
            <strong>Cost:</strong> $1 • <strong>Correct answer:</strong> +$5 (+$4 net)
          </p>
        </div>
      </div>
    </div>
  );
};
