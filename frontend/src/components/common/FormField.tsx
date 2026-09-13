import React from 'react';

export interface FormFieldProps {
  id?: string;
  label?: string;
  required?: boolean;
  error?: string | null;
  hint?: string;
  className?: string;
  children: React.ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  required = false,
  error,
  hint,
  className = '',
  children,
}) => {
  return (
    <div className={`space-y-1.5 w-full ${className}`}>
      {label && (
        <label
          htmlFor={id}
          className="block text-xs font-semibold uppercase tracking-wider text-slate-300"
        >
          {label}
          {required && <span className="text-cyan-400 ml-1 font-bold">*</span>}
        </label>
      )}

      {children}

      {error ? (
        <p className="text-xs text-rose-400 font-medium flex items-center gap-1.5 animate-fadeIn">
          <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
              clipRule="evenodd"
            />
          </svg>
          <span>{error}</span>
        </p>
      ) : hint ? (
        <p className="text-xs text-slate-400 leading-normal">{hint}</p>
      ) : null}
    </div>
  );
};
