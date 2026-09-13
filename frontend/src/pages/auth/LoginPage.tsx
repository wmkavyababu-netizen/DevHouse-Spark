import React, { useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { FormField } from '../../components/common/FormField';
import { Alert } from '../../components/common/Alert';

/* ------------------------------------------------------------------ */
/*  Role configuration — slugs must match ACCESS_ROLES on LandingPage  */
/* ------------------------------------------------------------------ */
const ROLE_CONFIG: Record<
  string,
  {
    title: string;
    description: string;
    badgeClass: string;
    dotClass: string;
    defaultEmail: string;
  }
> = {
  'survey-operator': {
    title: 'Survey Operator',
    description: 'Access survey upload, processing and candidate detection workflows.',
    badgeClass: 'text-cyan-300 border-cyan-800/60 bg-cyan-950/60',
    dotClass: 'bg-cyan-400',
    defaultEmail: 'operator@tarang.gov.in',
  },
  'marine-expert': {
    title: 'Marine Expert',
    description: 'Access acoustic physics review, Grad-CAM evidence and target validation.',
    badgeClass: 'text-amber-300 border-amber-800/60 bg-amber-950/60',
    dotClass: 'bg-amber-400',
    defaultEmail: 'expert@tarang.gov.in',
  },
  'cleanup-organization': {
    title: 'Cleanup Organization',
    description: 'Access validated targets, recovery sortie planning, and cleanup progress tracking.',
    badgeClass: 'text-emerald-300 border-emerald-800/60 bg-emerald-950/60',
    dotClass: 'bg-emerald-400',
    defaultEmail: 'cleanup@tarang.org',
  },
  'government-authority': {
    title: 'Government Authority',
    description: 'Access nationwide spatial intelligence, survey coverage, and compliance reports.',
    badgeClass: 'text-teal-300 border-teal-800/60 bg-teal-950/60',
    dotClass: 'bg-teal-400',
    defaultEmail: 'authority@tarang.gov.in',
  },
  administrator: {
    title: 'Administrator',
    description: 'Access internal system configuration, audit logs, and model improvement.',
    badgeClass: 'text-rose-300 border-rose-800/60 bg-rose-950/60',
    dotClass: 'bg-rose-400',
    defaultEmail: 'admin@tarang.dev',
  },
};

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  /* Role context from ?role=... (display only — never trusted for authz) */
  const role = searchParams.get('role') || 'survey-operator';
  const selectedRole = ROLE_CONFIG[role] || ROLE_CONFIG['survey-operator'];

  const [email, setEmail] = useState(() => selectedRole?.defaultEmail || 'operator@tarang.gov.in');
  const [password, setPassword] = useState('TarangSecure2026!');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Update email if role changes
  React.useEffect(() => {
    if (selectedRole?.defaultEmail) {
      setEmail(selectedRole.defaultEmail);
    }
  }, [role]);

  const selectRoleDemo = (roleKey: string) => {
    setSearchParams({ role: roleKey });
    const targetConfig = ROLE_CONFIG[roleKey];
    if (targetConfig) {
      setEmail(targetConfig.defaultEmail);
      setPassword('TarangSecure2026!');
    }
  };

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim()) {
      setErrorMessage('Please enter your email address.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter your password.');
      return;
    }

    setIsLoading(true);
    try {
      await login({
        email: email.trim(),
        password,
        rememberMe,
      });
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg = err.message || 'Invalid email or password. Please try again.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-cyan-500 selection:text-slate-950">
      {/* Background ambience */}
      <div className="absolute inset-0 sonar-grid-pattern opacity-25 pointer-events-none" />
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8 relative z-10">
        <Link to="/" className="inline-flex items-center gap-3 group">
          <img
            src="/logo.png"
            alt="TARANG Logo"
            className="w-12 h-12 object-contain rounded-xl p-0.5 bg-slate-900 border border-cyan-500/40 shadow-glow-cyan/40 group-hover:scale-105 transition-transform"
          />
          <span className="text-2xl font-black tracking-wider text-slate-100 font-display group-hover:text-cyan-400 transition-colors">
            TARANG
          </span>
        </Link>

        {/* Role badge (only if a valid role was selected) */}
        {selectedRole && (
          <div
            className={`mt-5 inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-mono ${selectedRole.badgeClass}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${selectedRole.dotClass} animate-pulse`} />
            <span>{selectedRole.title}</span>
          </div>
        )}

        <h2 className="mt-4 text-3xl font-extrabold text-slate-50 font-display">
          {selectedRole ? `${selectedRole.title} Login` : 'TARANG Login'}
        </h2>
        <p className="mt-1.5 text-sm text-slate-400 max-w-sm mx-auto">
          {selectedRole?.description || 'Sign in to access TARANG.'}
        </p>
      </div>

      {/* Login Card */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="glass-card rounded-2xl shadow-2xl overflow-hidden border border-slate-800 bg-slate-900/90 p-6 sm:p-8">
          {errorMessage && (
            <Alert variant="error" onClose={() => setErrorMessage(null)} className="mb-6">
              {errorMessage}
            </Alert>
          )}

          {/* Demo Role Switcher Tabs */}
          <div className="mb-6 pb-5 border-b border-slate-800/80">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-2 font-semibold">
              Select Demo Persona / Role Profile:
            </span>
            <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-2 text-xs">
              {Object.entries(ROLE_CONFIG).map(([rKey, rCfg]) => {
                const isActive = role === rKey;
                return (
                  <button
                    key={rKey}
                    type="button"
                    onClick={() => selectRoleDemo(rKey)}
                    className={`px-2.5 py-1.5 rounded-lg text-left text-[11px] font-medium transition-all flex items-center gap-1.5 border ${
                      isActive
                        ? 'bg-slate-800 text-slate-100 border-cyan-500/50 shadow-sm'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${rCfg.dotClass}`} />
                    <span className="truncate">{rCfg.title}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <FormField id="login-email" label="Email Address" required={true}>
              <Input
                id="login-email"
                type="email"
                autoComplete="email"
                placeholder="marine.expert@survey.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                    />
                  </svg>
                }
                required
              />
            </FormField>

            {/* Password */}
            <FormField id="login-password" label="Password" required={true}>
              <Input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-400 hover:text-slate-200 focus:outline-none"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"
                        />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                    )}
                  </button>
                }
                required
              />
            </FormField>

            {/* Remember me & Forgot Password */}
            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-slate-950"
                />
                <span>Remember me</span>
              </label>
              <Link
                to="/forgot-password"
                className="font-medium text-cyan-400 hover:text-cyan-300 hover:underline"
              >
                Forgot your password?
              </Link>
            </div>

            {/* Submit */}
            <div className="pt-2">
              <Button
                type="submit"
                variant="cyan-glow"
                size="lg"
                isLoading={isLoading}
                className="w-full"
              >
                LOGIN
              </Button>
            </div>
          </form>

          {/* Request Access */}
          <div className="mt-8 pt-6 border-t border-slate-800 text-center text-xs text-slate-400">
            Don't have authorized access?{' '}
            <Link
              to="/request-access"
              className="font-semibold text-cyan-400 hover:text-cyan-300 hover:underline"
            >
              Request Access
            </Link>
          </div>
        </div>

        {/* Back to access selection */}
        <div className="mt-5 text-center">
          <Link
            to="/#access"
            className="text-xs text-slate-400 hover:text-cyan-400 transition-colors inline-flex items-center gap-1.5"
          >
            <span>←</span>
            <span>Back to Access Selection</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;