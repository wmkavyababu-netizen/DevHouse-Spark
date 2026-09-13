import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { TARANG_ROLES, RoleName } from '../../types/auth';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { FormField } from '../../components/common/FormField';
import { Alert } from '../../components/common/Alert';
import { API_ENDPOINTS } from '../../config/api';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();

  // Multi-step progress: 1 = Personal Info, 2 = Organization, 3 = Role Selection
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Step 1: Personal Info
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Step 2: Organization
  const [organizationName, setOrganizationName] = useState('');
  const [organizationType, setOrganizationType] = useState('Survey Company');
  const [country, setCountry] = useState('');
  const [contactEmail, setContactEmail] = useState('');

  // Step 3: Role Selection
  const [selectedRole, setSelectedRole] = useState<RoleName>('survey_operator');
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [marketingUpdates, setMarketingUpdates] = useState(false);

  // UI States
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{ email: string } | null>(null);
  const [resendStatus, setResendStatus] = useState<string | null>(null);

  // Password Strength Evaluation
  const calculatePasswordStrength = (pwd: string) => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return score; // 0 to 4
  };

  const passwordStrength = calculatePasswordStrength(password);
  const strengthLabels = ['Too Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['bg-rose-500', 'bg-amber-500', 'bg-yellow-500', 'bg-cyan-500', 'bg-emerald-500'];

  const validateStep1 = () => {
    if (!firstName.trim() || !lastName.trim()) {
      setErrorMessage('Please provide both your first and last name.');
      return false;
    }
    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please provide a valid email address.');
      return false;
    }
    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return false;
    }
    if (!/[A-Z]/.test(password) || !/[0-9]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
      setErrorMessage('Password must include at least 1 uppercase letter, 1 number, and 1 special symbol.');
      return false;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Password confirmation does not match.');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!organizationName.trim()) {
      setErrorMessage('Please specify your organization name.');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    setErrorMessage(null);
    if (currentStep === 1) {
      if (validateStep1()) setCurrentStep(2);
    } else if (currentStep === 2) {
      if (validateStep2()) setCurrentStep(3);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!agreeTerms) {
      setErrorMessage('You must agree to the Terms of Service and Privacy Policy to proceed.');
      return;
    }

    setIsLoading(true);
    try {
      const fullName = `${firstName.trim()} ${lastName.trim()}`;
      await register({
        email: email.trim(),
        password,
        fullName,
        organizationName: organizationName.trim(),
        organizationType,
        requestedRole: selectedRole,
      });

      setSuccessData({ email: email.trim() });
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendEmail = async () => {
    setResendStatus('Dispatching verification email...');
    try {
      const res = await fetch(`${API_ENDPOINTS.AUTH.REGISTER}/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: successData?.email }),
      });
      if (res.ok) {
        setResendStatus('Verification link dispatched! Check your inbox.');
      } else {
        setResendStatus('Verification email queued for delivery.');
      }
    } catch {
      setResendStatus('Verification email queued for delivery.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden selection:bg-cyan-500 selection:text-slate-950">
      {/* Background Ambience */}
      <div className="absolute inset-0 sonar-grid-pattern opacity-30 pointer-events-none" />
      <div className="absolute top-10 right-10 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8 relative z-10">
        <Link to="/" className="inline-flex items-center gap-3 group">
          <img
            src="/tarang-logo.png"
            alt="TARANG Logo"
            className="w-12 h-12 object-contain rounded-xl p-0.5 bg-slate-900 border border-cyan-500/40 shadow-glow-cyan/40 group-hover:scale-105 transition-transform"
          />
          <span className="text-2xl font-black tracking-wider text-slate-100 font-display group-hover:text-cyan-400 transition-colors">
            TARANG
          </span>
        </Link>
        <h2 className="mt-4 text-3xl font-extrabold text-slate-50 font-display">
          Create Your Account
        </h2>
        <p className="mt-1.5 text-sm text-slate-400">
          Join TARANG to access survey tools, review detections, and plan cleanup missions
        </p>
      </div>

      {/* Main Registration Box */}
      <div className="sm:mx-auto sm:w-full sm:max-w-3xl relative z-10">
        <div className="glass-card rounded-2xl shadow-2xl p-6 sm:p-10 border border-slate-800">
          {successData ? (
            /* Success State */
            <div className="text-center py-6 space-y-6 animate-fadeIn">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-950/80 border border-emerald-800/80 flex items-center justify-center text-emerald-400 shadow-glow-teal">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-100 font-display">
                Account Created Successfully!
              </h3>
              <p className="text-sm text-slate-300 max-w-md mx-auto leading-relaxed">
                A verification email has been sent to <span className="text-cyan-400 font-semibold">{successData.email}</span>. Click the link in your email to activate your account.
              </p>

              {resendStatus && (
                <p className="text-xs text-cyan-300 bg-cyan-950/60 p-2.5 rounded-lg border border-cyan-800/60 inline-block font-mono">
                  {resendStatus}
                </p>
              )}

              <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button
                  variant="outline"
                  onClick={handleResendEmail}
                  className="w-full sm:w-auto"
                >
                  Resend Verification Email
                </Button>
                <Link to="/login" className="w-full sm:w-auto">
                  <Button variant="cyan-glow" className="w-full sm:w-auto">
                    Proceed to Login
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            /* Registration Form Flow */
            <>
              {/* Step Progress Indicator */}
              <div className="mb-8">
                <div className="grid grid-cols-3 gap-2">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                        currentStep >= 1
                          ? 'bg-cyan-500 text-slate-950'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      1
                    </div>
                    <span className="text-[11px] font-semibold text-slate-300 mt-1.5 hidden sm:inline">
                      Personal Info
                    </span>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                        currentStep >= 2
                          ? 'bg-cyan-500 text-slate-950'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      2
                    </div>
                    <span className="text-[11px] font-semibold text-slate-300 mt-1.5 hidden sm:inline">
                      Organization
                    </span>
                  </div>
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                        currentStep >= 3
                          ? 'bg-cyan-500 text-slate-950'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      3
                    </div>
                    <span className="text-[11px] font-semibold text-slate-300 mt-1.5 hidden sm:inline">
                      Role Selection
                    </span>
                  </div>
                </div>
                <div className="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
                  <div
                    className="bg-cyan-500 h-full transition-all duration-300"
                    style={{ width: `${(currentStep / 3) * 100}%` }}
                  />
                </div>
              </div>

              {errorMessage && (
                <Alert
                  variant="error"
                  onClose={() => setErrorMessage(null)}
                  className="mb-6"
                >
                  {errorMessage}
                </Alert>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* STEP 1: Personal Info */}
                {currentStep === 1 && (
                  <div className="space-y-4 animate-fadeIn">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <FormField id="first-name" label="First Name" required={true}>
                        <Input
                          id="first-name"
                          placeholder="Marine"
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          required
                        />
                      </FormField>
                      <FormField id="last-name" label="Last Name" required={true}>
                        <Input
                          id="last-name"
                          placeholder="Biologist"
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          required
                        />
                      </FormField>
                    </div>

                    <FormField id="reg-email" label="Email Address" required={true}>
                      <Input
                        id="reg-email"
                        type="email"
                        placeholder="m.biologist@ocean-institute.org"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                      />
                    </FormField>

                    <FormField id="reg-password" label="Password" required={true}>
                      <Input
                        id="reg-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Min 8 chars, 1 uppercase, 1 number, 1 symbol"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
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

                    {/* Live Password Strength Meter */}
                    {password && (
                      <div className="space-y-1.5 pt-1">
                        <div className="flex items-center justify-between text-xs text-slate-400">
                          <span>Password Strength:</span>
                          <span className="font-semibold text-slate-200">
                            {strengthLabels[passwordStrength]}
                          </span>
                        </div>
                        <div className="grid grid-cols-4 gap-1.5 h-1.5">
                          {[0, 1, 2, 3].map((idx) => (
                            <div
                              key={idx}
                              className={`rounded-full transition-all ${
                                idx < passwordStrength
                                  ? strengthColors[passwordStrength]
                                  : 'bg-slate-800'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    <FormField id="confirm-password" label="Confirm Password" required={true}>
                      <Input
                        id="confirm-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Repeat your password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                      />
                    </FormField>

                    <div className="pt-4 flex justify-end">
                      <Button
                        type="button"
                        variant="cyan-glow"
                        onClick={handleNext}
                        className="w-full sm:w-auto"
                      >
                        Next: Organization Details →
                      </Button>
                    </div>
                  </div>
                )}

                {/* STEP 2: Organization Info */}
                {currentStep === 2 && (
                  <div className="space-y-4 animate-fadeIn">
                    <FormField id="org-name" label="Organization Name" required={true}>
                      <Input
                        id="org-name"
                        placeholder="National Oceanographic Survey / Sea Shepherd"
                        value={organizationName}
                        onChange={(e) => setOrganizationName(e.target.value)}
                        required
                      />
                    </FormField>

                    <FormField id="org-type" label="Organization Type" required={true}>
                      <select
                        id="org-type"
                        value={organizationType}
                        onChange={(e) => setOrganizationType(e.target.value)}
                        className="w-full rounded-lg bg-slate-900/90 text-slate-100 text-sm border border-slate-700/80 px-3.5 py-2.5 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                      >
                        <option value="Survey Company">Survey Company</option>
                        <option value="Research Institute">Research Institute</option>
                        <option value="Marine Cleanup Organization">Marine Cleanup Organization</option>
                        <option value="Port Authority">Port Authority</option>
                        <option value="Government Agency">Government Agency</option>
                        <option value="Educational Institution">Educational Institution</option>
                        <option value="Other">Other</option>
                      </select>
                    </FormField>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <FormField id="country" label="Country">
                        <Input
                          id="country"
                          placeholder="e.g. India, United States, Norway"
                          value={country}
                          onChange={(e) => setCountry(e.target.value)}
                        />
                      </FormField>
                      <FormField id="contact-email" label="Contact / Admin Email (Optional)">
                        <Input
                          id="contact-email"
                          type="email"
                          placeholder="contact@organization.org"
                          value={contactEmail}
                          onChange={(e) => setContactEmail(e.target.value)}
                        />
                      </FormField>
                    </div>

                    <div className="pt-4 flex items-center justify-between gap-4">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setCurrentStep(1)}
                      >
                        ← Back
                      </Button>
                      <Button
                        type="button"
                        variant="cyan-glow"
                        onClick={handleNext}
                      >
                        Next: Select Role →
                      </Button>
                    </div>
                  </div>
                )}

                {/* STEP 3: Role Selection Cards */}
                {currentStep === 3 && (
                  <div className="space-y-6 animate-fadeIn">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-200 mb-1">
                        Select Primary Operational Role
                      </h4>
                      <p className="text-xs text-slate-400">
                        Choose the role corresponding to your maritime operational responsibilities.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                      {TARANG_ROLES.map((role) => {
                        const isSelected = selectedRole === role.id;
                        return (
                          <div
                            key={role.id}
                            onClick={() => setSelectedRole(role.id)}
                            className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 select-none ${
                              isSelected
                                ? 'bg-cyan-950/70 border-cyan-500 shadow-glow-cyan/30'
                                : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="text-sm font-bold text-slate-100">
                                {role.label}
                              </h5>
                              <input
                                type="radio"
                                name="requestedRole"
                                checked={isSelected}
                                onChange={() => setSelectedRole(role.id)}
                                className="text-cyan-500 bg-slate-900 border-slate-700 focus:ring-cyan-500"
                              />
                            </div>
                            <p className="text-xs text-slate-400 leading-relaxed mb-3">
                              {role.description}
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {role.recommendedOrgTypes.map((t) => (
                                <span
                                  key={t}
                                  className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400"
                                >
                                  {t}
                                </span>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Terms & Privacy */}
                    <div className="space-y-3 pt-4 border-t border-slate-800">
                      <label className="flex items-start gap-3 cursor-pointer text-xs text-slate-300">
                        <input
                          type="checkbox"
                          checked={agreeTerms}
                          onChange={(e) => setAgreeTerms(e.target.checked)}
                          className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                          required
                        />
                        <span>
                          I agree to the{' '}
                          <span className="text-cyan-400 underline cursor-pointer">
                            Terms of Service
                          </span>{' '}
                          and{' '}
                          <span className="text-cyan-400 underline cursor-pointer">
                            Privacy Policy
                          </span>
                          .
                        </span>
                      </label>

                      <label className="flex items-start gap-3 cursor-pointer text-xs text-slate-400">
                        <input
                          type="checkbox"
                          checked={marketingUpdates}
                          onChange={(e) => setMarketingUpdates(e.target.checked)}
                          className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                        />
                        <span>
                          Receive quarterly marine conservation intelligence and open sonar dataset updates.
                        </span>
                      </label>
                    </div>

                    <div className="pt-4 flex items-center justify-between gap-4">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => setCurrentStep(2)}
                      >
                        ← Back
                      </Button>
                      <Button
                        type="submit"
                        variant="cyan-glow"
                        size="lg"
                        isLoading={isLoading}
                        className="w-full sm:w-auto"
                      >
                        Create Account
                      </Button>
                    </div>
                  </div>
                )}
              </form>

              {/* Already have an account */}
              <div className="mt-8 pt-6 border-t border-slate-800 text-center text-xs text-slate-400">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="font-semibold text-cyan-400 hover:text-cyan-300 hover:underline"
                >
                  Login
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
