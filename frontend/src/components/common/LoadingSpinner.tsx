import React from 'react';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  text,
  className = '',
}) => {
  const sizeMap = {
    sm: 'w-5 h-5 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-16 h-16 border-4',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-6 space-y-3 ${className}`}>
      <div className="relative flex items-center justify-center">
        {/* Sonar Ping Ring */}
        <div className={`absolute rounded-full bg-cyan-500/20 animate-sonar-ping ${size === 'lg' ? 'w-24 h-24' : 'w-16 h-16'}`} />
        {/* Core Spinning Ring */}
        <div
          className={`rounded-full border-t-cyan-400 border-r-teal-500 border-b-transparent border-l-transparent animate-spin ${sizeMap[size]}`}
        />
        {/* Center Sonar Sensor Dot */}
        <div className="absolute w-2 h-2 rounded-full bg-cyan-400 shadow-glow-cyan" />
      </div>
      {text && (
        <p className="text-xs uppercase tracking-wider font-semibold text-cyan-400 animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
};
