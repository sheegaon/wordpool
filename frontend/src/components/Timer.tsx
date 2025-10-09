import React from 'react';
import { useTimer, formatTime } from '../hooks/useTimer';

interface TimerProps {
  expiresAt: string | null;
}

export const Timer: React.FC<TimerProps> = ({ expiresAt }) => {
  const { timeRemaining, isExpired, isWarning, isUrgent } = useTimer(expiresAt);

  if (!expiresAt) return null;

  const getTimerClass = () => {
    if (isExpired) return 'bg-red-600 text-white';
    if (isUrgent) return 'bg-red-500 text-white animate-pulse';
    if (isWarning) return 'bg-yellow-500 text-white';
    return 'bg-blue-500 text-white';
  };

  return (
    <div className={`px-6 py-3 rounded-lg font-bold text-2xl ${getTimerClass()}`}>
      {isExpired ? "Time's Up!" : formatTime(timeRemaining)}
    </div>
  );
};
