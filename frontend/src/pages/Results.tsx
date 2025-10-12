import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGame } from '../contexts/GameContext';
import apiClient, { extractErrorMessage } from '../api/client';
import type { PhrasesetResults } from '../api/types';

export const Results: React.FC = () => {
  const { pendingResults, refreshPendingResults, refreshBalance } = useGame();
  const navigate = useNavigate();
  const [selectedPhrasesetId, setSelectedPhrasesetId] = useState<string | null>(null);
  const [results, setResults] = useState<PhrasesetResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Auto-select first pending result if available
    if (pendingResults.length > 0 && !selectedPhrasesetId) {
      setSelectedPhrasesetId(pendingResults[0].phraseset_id);
    }
  }, [pendingResults, selectedPhrasesetId]);

  useEffect(() => {
    const fetchResults = async () => {
      if (!selectedPhrasesetId) return;

      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getPhrasesetResults(selectedPhrasesetId);
        setResults(data);
        // Refresh pending results and balance (in case payout was collected)
        await refreshPendingResults();
        await refreshBalance();
      } catch (err) {
        setError(extractErrorMessage(err) || 'Failed to fetch results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [selectedPhrasesetId]);

  const handleSelectPhraseset = (phrasesetId: string) => {
    setSelectedPhrasesetId(phrasesetId);
  };

  if (pendingResults.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h1 className="text-2xl font-bold text-gray-800 mb-4">No Results Available</h1>
            <p className="text-gray-600 mb-6">
              You don't have any finalized phrasesets yet. Complete some rounds and check back!
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">Results</h1>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-600 hover:text-gray-800"
          >
            Back to Dashboard
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pending Results List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-4">
              <h2 className="font-bold text-lg mb-4">Pending Results</h2>
              <div className="space-y-2">
                {pendingResults.map((result) => (
                  <button
                    key={result.phraseset_id}
                    onClick={() => handleSelectPhraseset(result.phraseset_id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedPhrasesetId === result.phraseset_id
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <p className="text-sm font-semibold text-gray-800 truncate">
                      {result.prompt_text}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      Role: {result.role} • {result.payout_collected ? 'Collected' : 'New!'}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results Details */}
          <div className="lg:col-span-2">
            {loading && (
              <div className="bg-white rounded-lg shadow-lg p-8 text-center">
                <p className="text-xl">Loading results...</p>
              </div>
            )}

            {error && (
              <div className="bg-white rounded-lg shadow-lg p-8">
                <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                  {error}
                </div>
              </div>
            )}

            {results && !loading && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                {/* Prompt */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-blue-700 mb-1">Prompt:</p>
                  <p className="text-xl font-semibold text-blue-900">{results.prompt_text}</p>
                </div>

                {/* Your Performance */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <h3 className="font-bold text-lg text-green-900 mb-3">Your Performance</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-green-700">Your Phrase:</p>
                      <p className="text-xl font-bold text-green-900">{results.your_phrase}</p>
                    </div>
                    <div>
                      <p className="text-sm text-green-700">Your Role:</p>
                      <p className="text-xl font-bold text-green-900 capitalize">{results.your_role}</p>
                    </div>
                    <div>
                      <p className="text-sm text-green-700">Points Earned:</p>
                      <p className="text-xl font-bold text-green-900">{results.your_points}</p>
                    </div>
                    <div>
                      <p className="text-sm text-green-700">Payout:</p>
                      <p className="text-2xl font-bold text-green-600">${results.your_payout}</p>
                    </div>
                  </div>
                  {results.already_collected && (
                    <p className="text-sm text-green-700 mt-3 italic">
                      ✓ Payout already collected
                    </p>
                  )}
                </div>

                {/* Vote Results */}
                <div className="mb-6">
                  <h3 className="font-bold text-lg text-gray-800 mb-3">Vote Results</h3>
                  <div className="space-y-2">
                    {results.votes
                      .sort((a, b) => b.vote_count - a.vote_count)
                      .map((vote, index) => (
                        <div
                          key={vote.phrase}
                          className={`p-4 rounded-lg border-2 ${
                            vote.is_original
                              ? 'bg-purple-50 border-purple-500'
                              : 'bg-gray-50 border-gray-300'
                          }`}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <span className="text-2xl font-bold text-gray-400">
                                #{index + 1}
                              </span>
                              <div>
                                <p className="text-xl font-bold text-gray-800">
                                  {vote.phrase}
                                  {vote.is_original && (
                                    <span className="ml-2 text-sm bg-purple-500 text-white px-2 py-1 rounded">
                                      ORIGINAL
                                    </span>
                                  )}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold text-blue-600">
                                {vote.vote_count}
                              </p>
                              <p className="text-sm text-gray-600">votes</p>
                            </div>
                          </div>
                          {/* Vote bar */}
                          <div className="mt-2 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                vote.is_original ? 'bg-purple-500' : 'bg-blue-500'
                              }`}
                              style={{
                                width: `${(vote.vote_count / results.total_votes) * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Total Votes:</p>
                      <p className="font-bold text-gray-800">{results.total_votes}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Prize Pool:</p>
                      <p className="font-bold text-gray-800">${results.total_pool}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-gray-600">Finalized At:</p>
                      <p className="font-bold text-gray-800">
                        {new Date(results.finalized_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
