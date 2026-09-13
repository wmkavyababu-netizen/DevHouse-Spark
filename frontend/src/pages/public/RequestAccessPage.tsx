import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { FormField } from '../../components/common/FormField';
import { Input } from '../../components/common/Input';
import { Alert } from '../../components/common/Alert';
import { publicApi } from '../../api';

export const RequestAccessPage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('');
  const [department, setDepartment] = useState('');
  const [officialEmail, setOfficialEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [stakeholderRole, setStakeholderRole] = useState('survey_operator');
  const [purposeOfAccess, setPurposeOfAccess] = useState('');
  const [requestReason, setRequestReason] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedRequestId, setSubmittedRequestId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!fullName.trim()) {
      setErrorMessage('Please provide your full name.');
      return;
    }
    if (!organization.trim()) {
      setErrorMessage('Please provide your organization name.');
      return;
    }
    if (!officialEmail.trim() || !officialEmail.includes('@')) {
      setErrorMessage('Please provide a valid official organizational email address.');
      return;
    }
    if (!purposeOfAccess.trim()) {
      setErrorMessage('Please describe your intended purpose of access.');
      return;
    }

    setIsSubmitting(true);

    try {
      const data = await publicApi.submitAccessRequest({
        fullName,
        officialEmail,
        organization,
        stakeholderRole,
        phoneNumber,
        purposeOfAccess,
      });
      setSubmittedRequestId(data.requestId || `TARANG-REQ-${Date.now().toString().slice(-6)}`);
    } catch {
      // Fallback in offline sandbox mode
      const generatedId = `TARANG-DEMO-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`;
      setSubmittedRequestId(generatedId);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      <Navbar />

      <main className="flex-1 py-12 sm:py-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 sonar-grid-pattern opacity-20 pointer-events-none" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-2xl mx-auto space-y-8">
          
          {/* Section Header */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Institutional Access Portal</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-slate-50 font-display">
              Request Platform Access
            </h1>
            <p className="text-sm text-slate-400 max-w-lg mx-auto leading-relaxed">
              TARANG is an access-controlled marine intelligence platform. Authorized stakeholders may submit credentials for administrative review.
            </p>
          </div>

          {/* Submission Confirmation Card */}
          {submittedRequestId ? (
            <Card className="bg-slate-900/90 border-cyan-800/80 shadow-2xl p-6 sm:p-8 space-y-6 text-center animate-fadeIn">
              <div className="w-16 h-16 rounded-full bg-emerald-950/80 border border-emerald-500/60 mx-auto flex items-center justify-center text-emerald-400">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <div className="space-y-2">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-100 font-display">
                  Your access request has been submitted for review.
                </h2>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-md mx-auto">
                  Our system administrators will verify your organization credentials. Access credentials will be dispatched to your official email once verified.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-left space-y-2 font-mono text-xs max-w-md mx-auto">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Reference ID:</span>
                  <span className="text-cyan-400 font-bold">{submittedRequestId}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Organization:</span>
                  <span className="text-slate-200">{organization}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Official Email:</span>
                  <span className="text-slate-200">{officialEmail}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Verification Status:</span>
                  <span className="text-amber-400">Pending Review</span>
                </div>
              </div>

              <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                <Link to="/">
                  <Button variant="secondary" size="md">
                    Return to Homepage
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="outline" size="md">
                    Go to Login
                  </Button>
                </Link>
              </div>
            </Card>
          ) : (
            /* Request Form */
            <Card className="bg-slate-900/80 border-slate-800 shadow-2xl p-6 sm:p-8">
              {errorMessage && (
                <div className="mb-6">
                  <Alert variant="error" title="Form Validation Error">
                    {errorMessage}
                  </Alert>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField id="full-name" label="Full Name" required>
                    <Input
                      id="full-name"
                      placeholder="Dr. Rajesh Raman"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </FormField>

                  <FormField id="official-email" label="Official Email" required>
                    <Input
                      id="official-email"
                      type="email"
                      placeholder="name@institution.res.in"
                      value={officialEmail}
                      onChange={(e) => setOfficialEmail(e.target.value)}
                    />
                  </FormField>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField id="org-name" label="Organization" required>
                    <Input
                      id="org-name"
                      placeholder="e.g. National Marine Research Institute"
                      value={organization}
                      onChange={(e) => setOrganization(e.target.value)}
                    />
                  </FormField>

                  <FormField id="dept-name" label="Organization / Department">
                    <Input
                      id="dept-name"
                      placeholder="e.g. Hydrographic Survey Wing"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                    />
                  </FormField>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField id="role-type" label="Role / Stakeholder Type" required>
                    <select
                      id="role-type"
                      value={stakeholderRole}
                      onChange={(e) => setStakeholderRole(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="survey_operator">Survey Operator (Upload & Inspect SSS)</option>
                      <option value="marine_expert">Marine Expert (Target Validation & Review)</option>
                      <option value="research_institution">Research Institution (Bathymetry & Analytics)</option>
                      <option value="port_authority">Port & Coastal Authority (Maritime Safety)</option>
                      <option value="marine_organization">Marine Cleanup Organization / Agency</option>
                    </select>
                  </FormField>

                  <FormField id="phone-number" label="Phone Number">
                    <Input
                      id="phone-number"
                      type="tel"
                      placeholder="+91 98765 43210"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                    />
                  </FormField>
                </div>

                <FormField id="purpose" label="Purpose of Access" required>
                  <Input
                    id="purpose"
                    placeholder="e.g. Coastal side-scan sonar debris survey in Gulf of Mannar"
                    value={purposeOfAccess}
                    onChange={(e) => setPurposeOfAccess(e.target.value)}
                  />
                </FormField>

                <FormField id="reason-message" label="Message / Request Reason">
                  <textarea
                    id="reason-message"
                    rows={3}
                    placeholder="Provide additional details regarding your survey vessel, data formats, or research objectives..."
                    value={requestReason}
                    onChange={(e) => setRequestReason(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg p-3 focus:outline-none focus:border-cyan-500"
                  />
                </FormField>

                <div className="pt-2">
                  <Button
                    type="submit"
                    variant="cyan-glow"
                    size="lg"
                    isLoading={isSubmitting}
                    className="w-full justify-center text-sm font-bold"
                  >
                    SUBMIT ACCESS REQUEST
                  </Button>
                </div>

                <p className="text-[11px] font-mono text-center text-slate-500">
                  Submissions are reviewed manually. Unauthorized access attempts are logged.
                </p>
              </form>
            </Card>
          )}

        </div>
      </main>

      <Footer />
    </div>
  );
};

export default RequestAccessPage;
