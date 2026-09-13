import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'cyan' | 'teal' | 'emerald' | 'amber' | 'rose' | 'purple' | 'slate';
  size?: 'sm' | 'md';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'cyan',
  size = 'sm',
  dot = false,
  className = '',
  ...props
}) => {
  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
  };

  const variantStyles = {
    cyan: 'bg-cyan-950/70 text-cyan-300 border border-cyan-700/50',
    teal: 'bg-teal-950/70 text-teal-300 border border-teal-700/50',
    emerald: 'bg-emerald-950/70 text-emerald-300 border border-emerald-700/50',
    amber: 'bg-amber-950/70 text-amber-300 border border-amber-700/50',
    rose: 'bg-rose-950/70 text-rose-300 border border-rose-700/50',
    purple: 'bg-purple-950/70 text-purple-300 border border-purple-700/50',
    slate: 'bg-slate-800 text-slate-300 border border-slate-700',
  };

  const dotColors = {
    cyan: 'bg-cyan-400',
    teal: 'bg-teal-400',
    emerald: 'bg-emerald-400',
    amber: 'bg-amber-400',
    rose: 'bg-rose-400',
    purple: 'bg-purple-400',
    slate: 'bg-slate-400',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full tracking-wide select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]} animate-pulse`} />
      )}
      <span>{children}</span>
    </span>
  );
};
