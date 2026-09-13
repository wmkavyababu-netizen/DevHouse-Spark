import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error = false, leftIcon, rightIcon, disabled, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            {leftIcon}
          </div>
        )}
        <input
          ref={ref}
          disabled={disabled}
          className={`w-full rounded-lg bg-slate-900/90 text-slate-100 text-sm transition-all duration-200 border 
            ${leftIcon ? 'pl-10' : 'pl-3.5'} 
            ${rightIcon ? 'pr-10' : 'pr-3.5'} 
            py-2.5 outline-none placeholder:text-slate-500
            ${
              error
                ? 'border-rose-500/80 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20'
                : 'border-slate-700/80 hover:border-slate-600 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20'
            }
            disabled:bg-slate-950 disabled:border-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed
            ${className}`}
          {...props}
        />
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400">
            {rightIcon}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
