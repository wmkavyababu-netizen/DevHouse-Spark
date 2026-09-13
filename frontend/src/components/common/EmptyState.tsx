import React from 'react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div
      className={`glass-card p-8 sm:p-12 rounded-2xl text-center flex flex-col items-center justify-center max-w-lg mx-auto ${className}`}
    >
      <div className="w-16 h-16 rounded-2xl bg-cyan-950/60 border border-cyan-800/50 flex items-center justify-center text-cyan-400 mb-4 shadow-glow-cyan/50">
        {icon || (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9" strokeWidth="1.5" />
            <circle cx="12" cy="12" r="5" strokeWidth="1.5" strokeDasharray="3 3" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 7v5l3 3" />
          </svg>
        )}
      </div>

      <h3 className="text-lg font-bold text-slate-100 tracking-tight mb-2">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm leading-relaxed mb-6">{description}</p>

      {action && <div className="flex items-center justify-center gap-3">{action}</div>}
    </div>
  );
};
