import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const roles = user?.roles || [];
  const isAdmin = roles.includes('admin');
  const isOperator = roles.includes('survey_operator');
  const isMarineExpert = roles.includes('marine_expert');
  const isCleanup = roles.includes('cleanup_organization');
  const isAuthority = roles.includes('government_authority');

  // Role display label
  const getRoleTitle = () => {
    if (isAdmin) return 'Platform Administrator';
    if (isOperator) return 'Hydrographic Survey Operator';
    if (isMarineExpert) return 'Marine Science Expert';
    if (isCleanup) return 'Ocean Cleanup Organization';
    if (isAuthority) return 'Government Maritime Authority';
    return 'Authorized Marine Stakeholder';
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fadeIn">
        {/* Welcome Header Card */}
        <div className="glass-card rounded-2xl p-6 sm:p-8 relative overflow-hidden border border-slate-800">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-cyan-500/10 via-teal-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-semibold tracking-wider uppercase text-cyan-400 font-mono">
                  {getRoleTitle()} • Active Session
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-50 font-display">
                Welcome back, {user?.fullName || 'Operator'}
              </h1>
              <p className="text-sm text-slate-300 flex flex-wrap items-center gap-2">
                <span>Organization:</span>
                <span className="font-semibold text-slate-100 bg-slate-900 px-2.5 py-0.5 rounded border border-slate-800">
                  {user?.organizationName || user?.organization?.name || 'TARANG Marine Intelligence'}
                </span>
                <span>•</span>
                <span>Role:</span>
                <span className="flex items-center gap-1">
                  {user?.roles?.map((r) => (
                    <Badge key={r} variant="cyan" size="sm">
                      {r.toUpperCase().replace('ROLE_', '')}
                    </Badge>
                  ))}
                </span>
              </p>
            </div>

            {/* Quick Primary Actions */}
            <div className="shrink-0 flex flex-wrap items-center gap-3">
              {isOperator && (
                <Link to="/surveys">
                  <Button
                    variant="cyan-glow"
                    size="md"
                    leftIcon={
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                    }
                  >
                    Upload SSS Survey
                  </Button>
                </Link>
              )}

              {isMarineExpert && (
                <Link to="/review">
                  <Button
                    variant="primary"
                    size="md"
                    className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                    leftIcon={
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    }
                  >
                    Open Review Queue
                  </Button>
                </Link>
              )}

              {isCleanup && (
                <div className="flex items-center gap-2">
                  <Link to="/missions">
                    <Button
                      variant="primary"
                      size="md"
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                    >
                      Plan Cleanup Mission
                    </Button>
                  </Link>
                  <Link to="/targets">
                    <Button variant="outline" size="md">
                      Validated Targets
                    </Button>
                  </Link>
                </div>
              )}

              {isAuthority && (
                <div className="flex items-center gap-2">
                  <Link to="/map">
                    <Button variant="cyan-glow" size="md">
                      Monitoring Map
                    </Button>
                  </Link>
                  <Link to="/analytics">
                    <Button variant="outline" size="md">
                      Analytics Reports
                    </Button>
                  </Link>
                </div>
              )}

              {isAdmin && (
                <Link to="/admin">
                  <Button
                    variant="danger"
                    size="md"
                    className="bg-rose-600 hover:bg-rose-500 text-white font-bold"
                  >
                    Model Improvement Console
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* 1. SURVEY OPERATOR DASHBOARD VIEW                             */}
        {/* ------------------------------------------------------------- */}
        {isOperator && (
          <div className="space-y-6">
            {/* Operator KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Surveys Ingested
                  </span>
                  <span className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-slate-100 font-display">2</div>
                  <p className="text-xs text-slate-400 mt-1">Raw multi-beam acoustic files</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Active Pipelines
                  </span>
                  <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-emerald-400 font-display">Completed</div>
                  <p className="text-xs text-slate-400 mt-1">Preprocessing &amp; AI inference ready</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Detections Extracted
                  </span>
                  <span className="p-2 rounded-lg bg-teal-950/80 text-teal-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-slate-100 font-display">6</div>
                  <p className="text-xs text-slate-400 mt-1">
                    <span className="text-cyan-400 font-semibold">2 Class A</span> auto-approved
                  </p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Awaiting Validation
                  </span>
                  <span className="p-2 rounded-lg bg-amber-950/80 text-amber-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-amber-400 font-display">4</div>
                  <p className="text-xs text-slate-400 mt-1">Class B/C queued for Marine Experts</p>
                </CardContent>
              </Card>
            </div>

            {/* Operator Recent Surveys */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-100 font-display">
                    Recent Sonar Surveys
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Multi-beam Side-Scan Sonar tracklines logged and processed by TARANG.
                  </p>
                </div>
                <Link to="/surveys">
                  <Button variant="outline" size="sm">
                    + Ingest SSS Log
                  </Button>
                </Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-3 px-3">Survey Name</th>
                      <th className="py-3 px-3">Format</th>
                      <th className="py-3 px-3">Date</th>
                      <th className="py-3 px-3">Pipeline Status</th>
                      <th className="py-3 px-3">Detections</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    <tr className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 px-3 font-medium text-slate-100">
                        Bay of Bengal Deep Survey Line A-104
                      </td>
                      <td className="py-3 px-3 font-mono text-cyan-400">XTF / 455kHz</td>
                      <td className="py-3 px-3 font-mono text-slate-400">2026-09-12</td>
                      <td className="py-3 px-3">
                        <Badge variant="emerald" size="sm" dot={true}>
                          Complete
                        </Badge>
                      </td>
                      <td className="py-3 px-3 font-mono">
                        4 targets <span className="text-slate-500">(1 Class A, 3 Class B)</span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link to="/workspace">
                          <Button variant="outline" size="sm" className="text-xs">
                            View Waterfall
                          </Button>
                        </Link>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 px-3 font-medium text-slate-100">
                        Port Approach Coastal Sweep Line 8
                      </td>
                      <td className="py-3 px-3 font-mono text-cyan-400">JSF / 900kHz</td>
                      <td className="py-3 px-3 font-mono text-slate-400">2026-09-11</td>
                      <td className="py-3 px-3">
                        <Badge variant="emerald" size="sm" dot={true}>
                          Complete
                        </Badge>
                      </td>
                      <td className="py-3 px-3 font-mono">
                        2 targets <span className="text-slate-500">(1 Class A, 1 Class C)</span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link to="/workspace">
                          <Button variant="outline" size="sm" className="text-xs">
                            View Waterfall
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 2. MARINE EXPERT DASHBOARD VIEW                               */}
        {/* ------------------------------------------------------------- */}
        {isMarineExpert && (
          <div className="space-y-6">
            {/* Marine Expert KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
                    Pending Reviews
                  </span>
                  <span className="p-2 rounded-lg bg-amber-950/80 text-amber-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-amber-400 font-display">4</div>
                  <p className="text-xs text-slate-400 mt-1">Class B &amp; C acoustic candidates</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Reviews Completed
                  </span>
                  <span className="p-2 rounded-lg bg-teal-950/80 text-teal-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-slate-100 font-display">18</div>
                  <p className="text-xs text-slate-400 mt-1">Validated across current surveys</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Validated Targets
                  </span>
                  <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-emerald-400 font-display">15</div>
                  <p className="text-xs text-slate-400 mt-1">Transferred to Cleanup Organizations</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Feedback Bucket
                  </span>
                  <span className="p-2 rounded-lg bg-rose-950/80 text-rose-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-rose-400 font-display">3</div>
                  <p className="text-xs text-slate-400 mt-1">Categorized rejections for retraining</p>
                </CardContent>
              </Card>
            </div>

            {/* Marine Expert Review Queue Preview */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-100 font-display">
                    Pending Validation Workload (Class B &amp; C Detections)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Detections with intermediate confidence requiring acoustic physics verification and Grad-CAM inspection.
                  </p>
                </div>
                <Link to="/review">
                  <Button variant="primary" size="sm" className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold">
                    Start Review Queue
                  </Button>
                </Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-3 px-3">Detection ID</th>
                      <th className="py-3 px-3">Predicted Class</th>
                      <th className="py-3 px-3">Confidence</th>
                      <th className="py-3 px-3">Classification</th>
                      <th className="py-3 px-3">Survey &amp; Frame</th>
                      <th className="py-3 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    <tr className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 px-3 font-mono text-cyan-400">det-rev-101</td>
                      <td className="py-3 px-3 font-semibold text-pink-400">Ghost Net / Derelict Gear</td>
                      <td className="py-3 px-3 font-mono">76.4%</td>
                      <td className="py-3 px-3">
                        <Badge variant="amber" size="sm">
                          Class B (Medium)
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-slate-400">Bay of Bengal Line A • Frame 142</td>
                      <td className="py-3 px-3 text-right">
                        <Link to="/review">
                          <Button variant="outline" size="sm" className="text-xs text-amber-400 hover:text-amber-300">
                            Inspect Physics &amp; Validate →
                          </Button>
                        </Link>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 px-3 font-mono text-cyan-400">det-rev-104</td>
                      <td className="py-3 px-3 font-semibold text-slate-300">Unknown Anomaly (OOD)</td>
                      <td className="py-3 px-3 font-mono">54.1%</td>
                      <td className="py-3 px-3">
                        <Badge variant="slate" size="sm">
                          Class C (Low / OOD)
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-slate-400">Bay of Bengal Line A • Frame 204</td>
                      <td className="py-3 px-3 text-right">
                        <Link to="/review">
                          <Button variant="outline" size="sm" className="text-xs text-amber-400 hover:text-amber-300">
                            Inspect Physics &amp; Validate →
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 3. CLEANUP ORGANIZATION DASHBOARD VIEW                        */}
        {/* ------------------------------------------------------------- */}
        {isCleanup && (
          <div className="space-y-6">
            {/* Cleanup KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                    Validated Targets
                  </span>
                  <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-emerald-400 font-display">5</div>
                  <p className="text-xs text-slate-400 mt-1">Confirmed by marine scientists</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Pending Mission
                  </span>
                  <span className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-cyan-400 font-display">3</div>
                  <p className="text-xs text-slate-400 mt-1">Ready for sortie assignment</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Active Missions
                  </span>
                  <span className="p-2 rounded-lg bg-blue-950/80 text-blue-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-blue-400 font-display">1</div>
                  <p className="text-xs text-slate-400 mt-1">Vessel: Ocean Guardian</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Tonnage Cleared
                  </span>
                  <span className="p-2 rounded-lg bg-purple-950/80 text-purple-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-slate-100 font-display">1.54 T</div>
                  <p className="text-xs text-slate-400 mt-1">Derived from confirmed recoveries</p>
                </CardContent>
              </Card>
            </div>

            {/* Actionable Validated Targets Table */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-100 font-display">
                    Actionable Validated Cleanup Targets
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Exclusively expert-validated targets. Unverified predictions and rejected items are filtered out.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Link to="/targets">
                    <Button variant="outline" size="sm">
                      View All Validated Targets
                    </Button>
                  </Link>
                  <Link to="/missions">
                    <Button variant="primary" size="sm" className="bg-emerald-600 hover:bg-emerald-500 font-bold">
                      + Create Recovery Mission
                    </Button>
                  </Link>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-3 px-3">Target Code</th>
                      <th className="py-3 px-3">Debris Category</th>
                      <th className="py-3 px-3">Coordinates</th>
                      <th className="py-3 px-3">Depth</th>
                      <th className="py-3 px-3">Hazard Level</th>
                      <th className="py-3 px-3">Mission Status</th>
                      <th className="py-3 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    <tr className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 px-3 font-mono font-bold text-cyan-400">TGT-8821</td>
                      <td className="py-3 px-3 font-medium text-pink-400">Ghost Net (Entanglement Hazard)</td>
                      <td className="py-3 px-3 font-mono text-slate-400">13.0827°N, 80.2707°E</td>
                      <td className="py-3 px-3 font-mono">24.5 m</td>
                      <td className="py-3 px-3">
                        <Badge variant="rose" size="sm">Critical</Badge>
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant="cyan" size="sm">Assigned Sortie 1</Badge>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link to="/missions">
                          <Button variant="outline" size="sm" className="text-xs">
                            Track Sortie →
                          </Button>
                        </Link>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 px-3 font-mono font-bold text-cyan-400">TGT-8823</td>
                      <td className="py-3 px-3 font-medium text-amber-400">Derelict Crab Pot / Trap Cage</td>
                      <td className="py-3 px-3 font-mono text-slate-400">13.0764°N, 80.2641°E</td>
                      <td className="py-3 px-3 font-mono">12.0 m</td>
                      <td className="py-3 px-3">
                        <Badge variant="amber" size="sm">Medium</Badge>
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant="slate" size="sm">Unassigned</Badge>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link to="/missions">
                          <Button variant="outline" size="sm" className="text-xs text-emerald-400 hover:text-emerald-300">
                            Assign to Mission →
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 4. GOVERNMENT AUTHORITY DASHBOARD VIEW                        */}
        {/* ------------------------------------------------------------- */}
        {isAuthority && (
          <div className="space-y-6">
            {/* Government Oversight KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Seabed Coverage
                  </span>
                  <span className="p-2 rounded-lg bg-teal-950/80 text-teal-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-xl font-bold text-slate-400 font-display">No data available</div>
                  <p className="text-xs text-slate-500 mt-1">Awaiting live telemetry ingestion</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Confirmed Hotspots
                  </span>
                  <span className="p-2 rounded-lg bg-amber-950/80 text-amber-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-xl font-bold text-slate-400 font-display">No data available</div>
                  <p className="text-xs text-slate-500 mt-1">Awaiting validated cluster sync</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Clearance Rate
                  </span>
                  <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-xl font-bold text-slate-400 font-display">No data available</div>
                  <p className="text-xs text-slate-500 mt-1">Awaiting post-mission metrics</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Active Vessels
                  </span>
                  <span className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-xl font-bold text-slate-400 font-display">No data available</div>
                  <p className="text-xs text-slate-500 mt-1">Awaiting vessel AIS telemetry</p>
                </CardContent>
              </Card>
            </div>

            {/* End-to-End Master Workflow Status Flow */}
            <Card className="p-6">
              <h3 className="text-base font-bold text-slate-100 font-display mb-2">
                Nationwide Seabed Debris Remediation Pipeline
              </h3>
              <p className="text-xs text-slate-400 mb-6">
                Real-time tracking from initial acoustic detection through scientific validation and final recovery.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">Stage 1: Detected</span>
                  <div className="text-2xl font-black text-slate-100 font-display">24</div>
                  <p className="text-[11px] text-slate-400">AI candidate detections</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                  <span className="text-[10px] font-mono text-amber-400 uppercase tracking-widest">Stage 2: Validated</span>
                  <div className="text-2xl font-black text-amber-400 font-display">18</div>
                  <p className="text-[11px] text-slate-400">Confirmed by Marine Experts</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                  <span className="text-[10px] font-mono text-blue-400 uppercase tracking-widest">Stage 3: Assigned</span>
                  <div className="text-2xl font-black text-blue-400 font-display">14</div>
                  <p className="text-[11px] text-slate-400">Allocated to recovery sorties</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                  <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest">Stage 4: Cleanup Completed</span>
                  <div className="text-2xl font-black text-emerald-400 font-display">10</div>
                  <p className="text-[11px] text-slate-400">Cleanup Mission Completed</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 5. ADMINISTRATOR DASHBOARD VIEW                                */}
        {/* ------------------------------------------------------------- */}
        {isAdmin && (
          <div className="space-y-6">
            {/* Admin KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">
                    Platform Security
                  </span>
                  <span className="p-2 rounded-lg bg-rose-950/80 text-rose-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-2xl font-extrabold text-emerald-400 font-display">RS256 Active</div>
                  <p className="text-xs text-slate-400 mt-1">RBAC authorization operational</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Feedback Bucket Size
                  </span>
                  <span className="p-2 rounded-lg bg-amber-950/80 text-amber-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-3xl font-extrabold text-amber-400 font-display">4 Samples</div>
                  <p className="text-xs text-slate-400 mt-1">Expert-curated rejection samples</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Active AI Model
                  </span>
                  <span className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-xl font-extrabold text-cyan-400 font-display">Current Model</div>
                  <p className="text-xs text-slate-400 mt-1">YOLOv8 Acoustic Baseline</p>
                </CardContent>
              </Card>

              <Card className="p-5">
                <CardHeader className="p-0 pb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Evaluation Policy
                  </span>
                  <span className="p-2 rounded-lg bg-purple-950/80 text-purple-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="text-xl font-extrabold text-purple-300 font-display">Review Gate</div>
                  <p className="text-xs text-slate-400 mt-1">Performance comparison &amp; admin sign-off</p>
                </CardContent>
              </Card>
            </div>

            {/* Admin Console Card */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-100 font-display">
                    Model Improvement &amp; Retraining Console
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Curate expert rejections from the Feedback Bucket, evaluate candidate models, and trigger retraining.
                  </p>
                </div>
                <Link to="/admin">
                  <Button variant="danger" size="sm" className="bg-rose-600 hover:bg-rose-500 font-bold">
                    Open Improvement Console →
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        )}

        {/* Global Access Profile Card */}
        <div className="glass-card rounded-xl p-6 border border-slate-800 space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Current Session Operational Zone
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Your permissions are governed by role-based access control (RBAC). Active permissions in this session:
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {isAdmin && <Badge variant="rose">Admin Model Improvement &amp; Governance</Badge>}
            {isOperator && <Badge variant="cyan">SSS Log Upload &amp; Sonar Workspace</Badge>}
            {isMarineExpert && <Badge variant="amber">Marine Expert Review &amp; Validation</Badge>}
            {isCleanup && <Badge variant="emerald">Validated Targets &amp; Sortie Planner</Badge>}
            {isAuthority && <Badge variant="teal">Maritime Monitoring &amp; Spatial Oversight</Badge>}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardPage;
