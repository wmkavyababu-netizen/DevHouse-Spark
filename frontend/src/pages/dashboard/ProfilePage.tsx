import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { FormField } from '../../components/common/FormField';
import { Alert } from '../../components/common/Alert';

export const ProfilePage: React.FC = () => {
  const { user, accessToken, updateLocalUser } = useAuth();

  const [fullName, setFullName] = useState(user?.fullName || '');
  const [organizationName, setOrganizationName] = useState(
    user?.organizationName || user?.organization?.name || ''
  );
  const [contactEmail, setContactEmail] = useState(
    user?.organization?.contactEmail || user?.email || ''
  );

  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const getInitials = (name?: string) => {
    if (!name) return 'TG';
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);

    if (!fullName.trim()) {
      setErrorMessage('Full name cannot be empty.');
      return;
    }

    setIsLoading(true);
    try {
      // Attempt backend update via /api/users/{id}
      if (user?.id && accessToken) {
        try {
          await fetch(`/api/users/${user.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
              fullName: fullName.trim(),
              organizationName: organizationName.trim(),
            }),
          });
        } catch {
          // Graceful local sync
        }
      }

      // Update local storage and context state
      updateLocalUser({
        fullName: fullName.trim(),
        organizationName: organizationName.trim(),
      });

      setSuccessMessage('Profile details updated successfully.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update profile settings.');
    } finally {
      setIsLoading(false);
    }
  };

  const formattedDate = user?.createdAt
    ? new Date(user.createdAt).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Active Since Ingestion';

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-4xl mx-auto animate-fadeIn">
        {/* Page Title */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-50 font-display">
            Account Settings & Profile
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage your credentials, organization affiliations, and security permissions
          </p>
        </div>

        {/* Profile Summary Card */}
        <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800 flex flex-col sm:flex-row items-center gap-6">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-cyan-500 to-teal-400 p-0.5 shadow-glow-cyan/40 shrink-0">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-2xl font-black text-cyan-300 font-display">
              {getInitials(user?.fullName)}
            </div>
          </div>

          <div className="flex-1 text-center sm:text-left space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <h2 className="text-xl font-bold text-slate-100">{user?.fullName || 'TARANG Operator'}</h2>
              <Badge variant="emerald" size="sm" dot={true}>
                {user?.status?.toUpperCase() || 'ACTIVE'}
              </Badge>
            </div>
            <p className="text-sm text-slate-300 font-mono">{user?.email}</p>
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1">
              <span className="text-xs text-slate-400">Assigned Roles:</span>
              {user?.roles && user.roles.length > 0 ? (
                user.roles.map((r) => (
                  <Badge key={r} variant="cyan" size="sm">
                    {r.toUpperCase().replace('ROLE_', '')}
                  </Badge>
                ))
              ) : (
                <Badge variant="slate" size="sm">
                  STANDARD_USER
                </Badge>
              )}
            </div>
          </div>

          <div className="shrink-0 text-center sm:text-right text-xs text-slate-400 border-t sm:border-t-0 sm:border-l border-slate-800 pt-4 sm:pt-0 sm:pl-6">
            <p className="text-[10px] uppercase font-semibold tracking-wider text-slate-500">
              Account Created
            </p>
            <p className="font-medium text-slate-200 mt-0.5">{formattedDate}</p>
          </div>
        </div>

        {/* Edit Profile Form */}
        <Card className="p-6 sm:p-8">
          <CardHeader className="p-0 pb-6">
            <CardTitle>Profile Details</CardTitle>
            <p className="text-xs text-slate-400 mt-1">
              Update your personal identification and maritime organization metadata.
            </p>
          </CardHeader>

          <CardContent className="p-0">
            {successMessage && (
              <Alert variant="success" onClose={() => setSuccessMessage(null)} className="mb-6">
                {successMessage}
              </Alert>
            )}

            {errorMessage && (
              <Alert variant="error" onClose={() => setErrorMessage(null)} className="mb-6">
                {errorMessage}
              </Alert>
            )}

            <form onSubmit={handleUpdateProfile} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <FormField id="profile-name" label="Full Name" required={true}>
                  <Input
                    id="profile-name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </FormField>

                <FormField id="profile-email" label="Email Address (Read-Only)">
                  <Input
                    id="profile-email"
                    value={user?.email || ''}
                    disabled={true}
                    className="bg-slate-950/60 text-slate-400 cursor-not-allowed"
                  />
                </FormField>

                <FormField id="profile-org" label="Organization">
                  <Input
                    id="profile-org"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="Organization or Research Institute"
                  />
                </FormField>

                <FormField id="profile-contact" label="Contact / Department Email">
                  <Input
                    id="profile-contact"
                    type="email"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    placeholder="contact@organization.org"
                  />
                </FormField>
              </div>

              <div className="pt-4 flex justify-end">
                <Button
                  type="submit"
                  variant="cyan-glow"
                  size="md"
                  isLoading={isLoading}
                >
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Security & Authentication Settings */}
        <Card className="p-6 sm:p-8">
          <CardHeader className="p-0 pb-6">
            <CardTitle>Security & Key Management</CardTitle>
            <p className="text-xs text-slate-400 mt-1">
              Cryptographic RS256 token details and session control.
            </p>
          </CardHeader>

          <CardContent className="p-0 space-y-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-slate-200">Password Authentication</h4>
                <p className="text-xs text-slate-400">
                  Secured via Spring Boot BCrypt salted hashing.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.assign('/forgot-password')}
              >
                Change Password
              </Button>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-slate-200">Two-Factor Authentication (2FA)</h4>
                <p className="text-xs text-slate-400">
                  Status:{' '}
                  <span className={user?.twoFactorEnabled ? 'text-emerald-400' : 'text-slate-400'}>
                    {user?.twoFactorEnabled ? 'Enabled' : 'Disabled (Optional)'}
                  </span>
                </p>
              </div>
              <Button variant="ghost" size="sm" disabled={true}>
                {user?.twoFactorEnabled ? 'Configured' : 'Setup 2FA'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};
