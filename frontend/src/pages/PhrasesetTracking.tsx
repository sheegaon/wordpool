import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient, { extractErrorMessage } from '../api/client';
import type {
  PhrasesetSummary,
  PhrasesetDetails as PhrasesetDetailsType,
} from '../api/types';
import { useGame } from '../contexts/GameContext';
import { PhrasesetList } from '../components/PhrasesetList';
import { PhrasesetDetails } from '../components/PhrasesetDetails';

type RoleFilter = 'all' | 'prompt' | 'copy';
type StatusFilter = 'all' | 'in_progress' | 'voting' | 'finalized' | 'abandoned';

const roleOptions: { value: RoleFilter; label: string }[] = [
  { value: 'all', label: 'All Roles' },
  { value: 'prompt', label: 'Prompts' },
  { value: 'copy', label: 'Copies' },
];

const statusOptions: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'voting', label: 'Voting' },
  { value: 'finalized', label: 'Finalized' },
  { value: 'abandoned', label: 'Abandoned' },
];

export const PhrasesetTracking: React.FC = () => {
  const navigate = useNavigate();
  const {
    refreshBalance,
    refreshPhrasesetSummary,
    refreshUnclaimedResults,
    phrasesetSummary,
  } = useGame();

  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [phrasesets, setPhrasesets] = useState<PhrasesetSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<PhrasesetSummary | null>(null);
  const [details, setDetails] = useState<PhrasesetDetailsType | null>(null);
  const [listLoading, setListLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPhrasesets = useCallback(async () => {
    setListLoading(true);
    try {
      const data = await apiClient.getPlayerPhrasesets({
        role: roleFilter,
        status: statusFilter,
        limit: 100,
        offset: 0,
      });
      setPhrasesets(data.phrasesets);
      if (data.phrasesets.length > 0) {
        const first = data.phrasesets.find((item) =>
          item.phraseset_id ? item.phraseset_id === selectedId : item.prompt_round_id === selectedId
        ) ?? data.phrasesets[0];
        const id = first.phraseset_id ?? first.prompt_round_id;
        setSelectedId(id);
        setSelectedSummary(first);
      } else {
        setSelectedId(null);
        setSelectedSummary(null);
        setDetails(null);
      }
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err) || 'Unable to load phrasesets');
    } finally {
      setListLoading(false);
    }
  }, [roleFilter, statusFilter, selectedId]);

  const fetchDetails = useCallback(async (phraseset: PhrasesetSummary | null) => {
    if (!phraseset || !phraseset.phraseset_id) {
      setDetails(null);
      return;
    }
    setDetailsLoading(true);
    try {
      const data = await apiClient.getPhrasesetDetails(phraseset.phraseset_id);
      setDetails(data);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err) || 'Unable to load phraseset details');
    } finally {
      setDetailsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPhrasesets();
  }, [fetchPhrasesets]);

  useEffect(() => {
    if (selectedSummary) {
      fetchDetails(selectedSummary);
    }
  }, [selectedSummary, fetchDetails]);

  // Poll details every 10 seconds when phraseset is active
  useEffect(() => {
    if (!selectedSummary?.phraseset_id) return;
    if (details?.status === 'finalized') return;

    const interval = setInterval(() => {
      fetchDetails(selectedSummary);
    }, 10000);

    return () => clearInterval(interval);
  }, [selectedSummary, details?.status, fetchDetails]);

  const handleSelect = (summary: PhrasesetSummary) => {
    const id = summary.phraseset_id ?? summary.prompt_round_id;
    setSelectedId(id);
    setSelectedSummary(summary);
  };

  const handleClaim = async (phrasesetId: string) => {
    setClaiming(true);
    try {
      await apiClient.claimPhrasesetPrize(phrasesetId);
      await Promise.all([
        fetchDetails(selectedSummary),
        fetchPhrasesets(),
        refreshBalance(),
        refreshPhrasesetSummary(),
        refreshUnclaimedResults(),
      ]);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to claim prize');
    } finally {
      setClaiming(false);
    }
  };

  const totalTracked = useMemo(() => phrasesets.length, [phrasesets.length]);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Phraseset Tracking</h1>
            <p className="text-sm text-gray-600">
              Monitor your prompts and copies throughout the game lifecycle.
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-600 hover:text-gray-800 text-sm"
          >
            Back to Dashboard
          </button>
        </div>

        {phrasesetSummary && (
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs uppercase text-gray-500">In Progress</p>
              <p className="text-lg font-semibold text-gray-800">
                {phrasesetSummary.in_progress.prompts} prompt
                {phrasesetSummary.in_progress.prompts === 1 ? '' : 's'} &nbsp;•&nbsp;
                {phrasesetSummary.in_progress.copies} copy
                {phrasesetSummary.in_progress.copies === 1 ? '' : 'ies'}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs uppercase text-gray-500">Finalized</p>
              <p className="text-lg font-semibold text-gray-800">
                {phrasesetSummary.finalized.prompts} prompt
                {phrasesetSummary.finalized.prompts === 1 ? '' : 's'} &nbsp;•&nbsp;
                {phrasesetSummary.finalized.copies} copy
                {phrasesetSummary.finalized.copies === 1 ? '' : 'ies'}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs uppercase text-gray-500">Unclaimed</p>
              <p className="text-lg font-semibold text-green-700">
                ${phrasesetSummary.total_unclaimed_amount}
              </p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap gap-3">
              <label className="text-sm text-gray-700 flex items-center gap-2">
                Role
                <select
                  value={roleFilter}
                  onChange={(event) => setRoleFilter(event.target.value as RoleFilter)}
                  className="border border-gray-300 rounded-md px-2 py-1 text-sm"
                >
                  {roleOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-gray-700 flex items-center gap-2">
                Status
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
                  className="border border-gray-300 rounded-md px-2 py-1 text-sm"
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="text-sm text-gray-600">
              Showing {totalTracked} phraseset{totalTracked === 1 ? '' : 's'}
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Your Phrasesets</h2>
              <PhrasesetList
                phrasesets={phrasesets}
                selectedId={selectedId}
                onSelect={handleSelect}
                isLoading={listLoading}
              />
            </div>
          </div>
          <div className="lg:col-span-2">
            <PhrasesetDetails
              phraseset={details}
              loading={detailsLoading}
              claiming={claiming}
              onClaim={handleClaim}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
