import React from 'react';
import Lottie from 'lottie-react';
import flipAnimation from '../flip-littie.json';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Shuffling the tiles...',
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-32 h-32',
    lg: 'w-48 h-48',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className={sizeClasses[size]}>
        <Lottie
          animationData={flipAnimation}
          loop={true}
        />
      </div>
      {message && (
        <p className="text-quip-navy text-sm font-medium animate-pulse">
          {message}
        </p>
      )}
    </div>
  );
};
