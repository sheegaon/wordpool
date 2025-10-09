import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';

export const Dashboard: React.FC = () => {
  const {
    player,
    activeRound,
    pendingResults,
    roundAvailability,
    claimBonus,
    logout,
  } = useGame();
  const navigate = useNavigate();

  useEffect(() => {
    // If there's an active round, navigate to it
    if (activeRound?.round_id && activeRound.round_type) {
      const route = `/${activeRound.round_type}`;
      navigate(route);
    }
  }, [activeRound, navigate]);

  const handleClaimBonus = async () => {
    try {
      await claimBonus();
    } catch (err) {
      // Error is already handled in context
    }
  };

  const handleStartPrompt = () => {
    navigate('/prompt');
  };

  const handleStartCopy = () => {
    navigate('/copy');
  };

  const handleStartVote = () => {
    navigate('/vote');
  };

  const handleViewResults = () => {
    navigate('/results');
  };

  if (!player) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">WordPool</h1>
          <button
            onClick={logout}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Balance Card */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="text-center">
            <p className="text-gray-600 mb-2">Your Balance</p>
            <p className="text-5xl font-bold text-green-600">${player.balance}</p>
          </div>
        </div>

        {/* Daily Bonus */}
        {player.daily_bonus_available && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-yellow-800">Daily Bonus Available!</p>
                <p className="text-sm text-yellow-700">Claim your ${player.daily_bonus_amount} bonus</p>
              </div>
              <button
                onClick={handleClaimBonus}
                className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-6 rounded-lg"
              >
                Claim
              </button>
            </div>
          </div>
        )}

        {/* Pending Results Notification */}
        {pendingResults.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-blue-800">Results Ready!</p>
                <p className="text-sm text-blue-700">
                  {pendingResults.length} wordset{pendingResults.length > 1 ? 's' : ''} finalized
                </p>
              </div>
              <button
                onClick={handleViewResults}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-lg"
              >
                View Results
              </button>
            </div>
          </div>
        )}

        {/* Round Selection */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-800">Start a Round</h2>

          <div className="space-y-4">
            {/* Prompt Round */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold text-lg">Prompt Round</h3>
                <span className="text-red-600 font-bold">-$100</span>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Submit a word for a creative prompt
              </p>
              <button
                onClick={handleStartPrompt}
                disabled={!roundAvailability?.can_prompt}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-colors"
              >
                {roundAvailability?.can_prompt ? 'Start Prompt Round' :
                  player.balance < 100 ? 'Insufficient Balance' :
                  player.outstanding_prompts >= 10 ? 'Too Many Outstanding Prompts' :
                  'Not Available'}
              </button>
            </div>

            {/* Copy Round */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold text-lg">Copy Round</h3>
                <span className="text-red-600 font-bold">
                  -${roundAvailability?.copy_cost || 100}
                  {roundAvailability?.copy_discount_active && (
                    <span className="text-green-600 text-sm ml-1">(discount!)</span>
                  )}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-1">
                Submit a similar word without seeing the prompt
              </p>
              {roundAvailability && roundAvailability.prompts_waiting > 0 && (
                <p className="text-xs text-blue-600 mb-3">
                  {roundAvailability.prompts_waiting} prompt{roundAvailability.prompts_waiting > 1 ? 's' : ''} waiting
                </p>
              )}
              <button
                onClick={handleStartCopy}
                disabled={!roundAvailability?.can_copy}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-colors"
              >
                {roundAvailability?.can_copy ? 'Start Copy Round' :
                  roundAvailability?.prompts_waiting === 0 ? 'No Prompts Available' :
                  player.balance < (roundAvailability?.copy_cost || 100) ? 'Insufficient Balance' :
                  'Start Copy Round'}
              </button>
            </div>

            {/* Vote Round */}
            <div className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold text-lg">Vote Round</h3>
                <span className="text-red-600 font-bold">-$1</span>
              </div>
              <p className="text-sm text-gray-600 mb-1">
                Identify the original word from three options
              </p>
              {roundAvailability && roundAvailability.wordsets_waiting > 0 && (
                <p className="text-xs text-blue-600 mb-3">
                  {roundAvailability.wordsets_waiting} wordset{roundAvailability.wordsets_waiting > 1 ? 's' : ''} waiting
                </p>
              )}
              <button
                onClick={handleStartVote}
                disabled={!roundAvailability?.can_vote}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-colors"
              >
                {roundAvailability?.can_vote ? 'Start Vote Round' :
                  roundAvailability?.wordsets_waiting === 0 ? 'No Wordsets Available' :
                  player.balance < 1 ? 'Insufficient Balance' :
                  'Not Available'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
