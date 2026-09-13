import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { FormField } from '../../components/common/FormField';
import { Alert } from '../../components/common/Alert';
import { API_ENDPOINTS } from '../../config/api';

export const ForgotPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const urlToken = searchParams.get('token');

  // Step 1: Request reset link; Step 2: Enter token & new password
  const [step, setStep] = useState<1 | 2>(urlToken ? 2 : 1);

  // Form states
  const [email, setEmail] = useState('');
  const [token, setToken] = useState(urlToken || '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // UI status
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [step1Success, setStep1Success] = useState(false);
  const [step2Success, setStep2Success] = useState(false);

  // Strength check
  const calculateStrength = (pwd: string) => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return score;
  };

  const strength = calculateStrength(newPassword);
  const strengthLabels = ['Too Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['bg-rose-500', 'bg-amber-500', 'bg-yellow-500', 'bg-cyan-500', 'bg-emerald-500'];

  // Step 1 Submit: Send Reset Link
  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please provide a valid registered email address.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.message || 'Failed to dispatch reset link.');
      }

      setStep1Success(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error processing password reset request.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2 Submit: Reset Password
  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!token.trim()) {
      setErrorMessage('Please provide your password reset token.');
      return;
    }
    if (newPassword.length < 8) {
      setErrorMessage('New password must be at least 8 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMessage('Password confirmation does not match.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: token.trim(),
          newPassword,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.message || 'Invalid or expired password reset token.');
      }

      setStep2Success(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-cyan-500 selection:text-slate-950">
      {/* Background Ambience */}
      <div className="absolute inset-0 sonar-grid-pattern opacity-30 pointer-events-none" />
      <div className="absolute top-10 left-10 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8 relative z-10">
        <Link to="/" className="inline-flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 p-0.5 shadow-glow-cyan/50 group-hover:scale-105 transition-transform duration-200">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <svg className="w-5 h-5 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <span className="text-2xl font-black tracking-wider text-slate-100 font-display">
            TARANG
          </span>
        </Link>
        <h2 className="mt-4 text-3xl font-extrabold text-slate-50 font-display">
          {step === 1 ? 'Reset Your Password' : 'Set New Password'}
        </h2>
        <p className="mt-1.5 text-sm text-slate-400">
          {step === 1
            ? 'Enter your account email to receive a password recovery link'
            : 'Enter your verification token and select a new secure password'}
        </p>
      </div>

      {/* Main Card */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="glass-card rounded-2xl shadow-2xl p-6 sm:p-8 border border-slate-800">
          {errorMessage && (
            <Alert
              variant="error"
              onClose={() => setErrorMessage(null)}
              className="mb-6"
            >
              {errorMessage}
            </Alert>
          )}

          {/* STEP 1: REQUEST RESET LINK */}
          {step === 1 && !step1Success && (
            <form onSubmit={handleStep1Submit} className="space-y-5 animate-fadeIn">
              <FormField id="reset-email" label="Account Email" required={true}>
                <Input
                  id="reset-email"
                  type="email"
                  placeholder="marine.expert@survey.org"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                    </svg>
                  }
                  required
                />
              </FormField>

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="cyan-glow"
                  size="lg"
                  isLoading={isLoading}
                  className="w-full"
                >
                  Send Reset Link
                </Button>
              </div>

              <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-800 text-slate-400">
                <Link to="/login" className="hover:text-cyan-400">
                  ← Back to Login
                </Link>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="text-cyan-400 hover:underline"
                >
                  Already have a token?
                </button>
              </div>
            </form>
          )}

          {/* STEP 1 SUCCESS PANEL */}
          {step === 1 && step1Success && (
            <div className="space-y-6 text-center py-4 animate-fadeIn">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-cyan-950/80 border border-cyan-800/80 flex items-center justify-center text-cyan-400 shadow-glow-cyan">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-100 font-display">
                Reset Link Sent!
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Check your inbox for password recovery instructions. The link expires in 1 hour.
              </p>

              <div className="pt-2 flex flex-col gap-3">
                <Button
                  variant="cyan-glow"
                  onClick={() => setStep(2)}
                  className="w-full"
                >
                  Enter Reset Token
                </Button>
                <Link to="/login">
                  <Button variant="ghost" className="w-full">
                    Return to Login
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {/* STEP 2: SET NEW PASSWORD */}
          {step === 2 && !step2Success && (
            <form onSubmit={handleStep2Submit} className="space-y-5 animate-fadeIn">
              <FormField id="reset-token" label="Reset Token" required={true}>
                <Input
                  id="reset-token"
                  placeholder="Paste UUID token from email"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
              </FormField>

              <FormField id="new-password" label="New Password" required={true}>
                <Input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Min 8 chars, 1 uppercase, 1 number, 1 symbol"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {showPassword ? 'Hide' : 'Show'}
                    </button>
                  }
                  required
                />
              </FormField>

              {/* Password strength */}
              {newPassword && (
                <div className="space-y-1.5 pt-0.5">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Strength:</span>
                    <span className="font-semibold text-slate-200">
                      {strengthLabels[strength]}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 h-1.5">
                    {[0, 1, 2, 3].map((idx) => (
                      <div
                        key={idx}
                        className={`rounded-full transition-all ${
                          idx < strength ? strengthColors[strength] : 'bg-slate-800'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              )}

              <FormField id="confirm-new-password" label="Confirm New Password" required={true}>
                <Input
                  id="confirm-new-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Repeat new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </FormField>

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="cyan-glow"
                  size="lg"
                  isLoading={isLoading}
                  className="w-full"
                >
                  Reset Password
                </Button>
              </div>

              <div className="text-center text-xs pt-2">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  ← Request a new link instead
                </button>
              </div>
            </form>
          )}

          {/* STEP 2 SUCCESS */}
          {step === 2 && step2Success && (
            <div className="space-y-6 text-center py-4 animate-fadeIn">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-950/80 border border-emerald-800/80 flex items-center justify-center text-emerald-400 shadow-glow-teal">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-100 font-display">
                Password Reset Successful!
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Your credentials have been securely updated. You can now login with your new password.
              </p>

              <div className="pt-2">
                <Link to="/login">
                  <Button variant="cyan-glow" size="lg" className="w-full">
                    Go to Login
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
