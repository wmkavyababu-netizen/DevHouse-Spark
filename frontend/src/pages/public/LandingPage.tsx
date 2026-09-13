import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/common/Button';
import { IntroSequence } from '../../components/common/IntroSequence';

/* ------------------------------------------------------------------ */
/*  Access roles — slugs must match the ones used in LoginPage.tsx     */
/* ------------------------------------------------------------------ */
const ACCESS_ROLES = [
  {
    slug: 'survey-operator',
    title: 'Survey Operator',
    badge: 'Survey Operations',
    description:
      'Upload Side-Scan Sonar surveys, monitor acoustic processing pipelines, and inspect candidate detections.',
    iconClass: 'text-cyan-400',
    badgeClass: 'text-cyan-300 border-cyan-900/60 bg-cyan-950/40',
    hoverClass: 'hover:border-cyan-500/50',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
        />
      </svg>
    ),
  },
  {
    slug: 'marine-expert',
    title: 'Marine Expert',
    badge: 'Validation & Science',
    description:
      'Review Class B & C detections, inspect acoustic shadow physics, and curate AI feedback.',
    iconClass: 'text-amber-400',
    badgeClass: 'text-amber-300 border-amber-900/60 bg-amber-950/40',
    hoverClass: 'hover:border-amber-500/50',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    slug: 'cleanup-organization',
    title: 'Cleanup Organization',
    badge: 'Ocean Cleanup Operations',
    description:
      'Manage validated marine debris targets, plan recovery sorties, and record recovered debris tonnage.',
    iconClass: 'text-emerald-400',
    badgeClass: 'text-emerald-300 border-emerald-900/60 bg-emerald-950/40',
    hoverClass: 'hover:border-emerald-500/50',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />
      </svg>
    ),
  },
  {
    slug: 'government-authority',
    title: 'Government Authority',
    badge: 'Maritime Oversight',
    description:
      'Monitor nationwide seabed coverage, regional target distribution, and high-level cleanup metrics.',
    iconClass: 'text-teal-400',
    badgeClass: 'text-teal-300 border-teal-900/60 bg-teal-950/40',
    hoverClass: 'hover:border-teal-500/50',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
        />
      </svg>
    ),
  },
];

export const LandingPage: React.FC = () => {
  const [showIntro, setShowIntro] = useState<boolean>(() => {
    return !sessionStorage.getItem('tarang_intro_seen');
  });

  const handleIntroComplete = () => {
    sessionStorage.setItem('tarang_intro_seen', 'true');
    setShowIntro(false);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showIntro) {
        handleIntroComplete();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showIntro]);

  const workflowStages = [
    {
      step: '01',
      title: 'SSS Data',
      desc: 'Raw multi-beam acoustic survey logs (XTF, JSF, HSX, SDF, PNG).',
      icon: (
        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
      ),
    },
    {
      step: '02',
      title: 'Preprocessing',
      desc: 'Nadir blanking, TVG normalization, destriping & roll correction.',
      icon: (
        <svg className="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
        </svg>
      ),
    },
    {
      step: '03',
      title: 'AI Detection',
      desc: 'In-process YOLOv8 acoustic detection & bounding box inference.',
      icon: (
        <svg className="w-5 h-5 text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      ),
    },
    {
      step: '04',
      title: 'Explainable AI',
      desc: 'Grad-CAM saliency heatmaps & acoustic shadow consistency physics.',
      icon: (
        <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
    },
    {
      step: '05',
      title: 'Geo-tagging',
      desc: 'Slant-range to WGS84 geodesic projection with uncertainty radius.',
      icon: (
        <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
    {
      step: '06',
      title: 'Expert Validation',
      desc: 'Human-in-the-loop review queue feeding active learning retraining.',
      icon: (
        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      step: '07',
      title: 'Seabed Intelligence',
      desc: 'DBSCAN spatial deduplication, target clustering & sortie planning.',
      icon: (
        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  return (
    <>
      {showIntro && <IntroSequence onComplete={handleIntroComplete} />}

      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
        <Navbar />

        {/* HERO */}
        <section className="relative overflow-hidden pt-12 pb-20 sm:pt-20 sm:pb-28 lg:pt-24 lg:pb-32 bg-radial-gradient-hero border-b border-slate-900">
          <div className="absolute inset-0 sonar-grid-pattern opacity-25 pointer-events-none" />
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[30rem] h-[30rem] bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
              <div className="flex-1 text-center lg:text-left space-y-6">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  <span>India's First Unified Seabed Mapping Intelligent Platform</span>
                </div>

                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-50 font-display leading-tight sm:leading-none">
                  See What Lies Beneath.
                </h1>

                <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-light max-w-2xl mx-auto lg:mx-0">
                  TARANG transforms Side-Scan Sonar data into intelligent seabed information, helping
                  authorized marine stakeholders detect, understand and map underwater anomalies and
                  debris.
                </p>

                <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-center lg:justify-start gap-3 sm:gap-4 max-w-md mx-auto lg:mx-0">
                  <a href="#access" className="flex-1 sm:flex-initial">
                    <Button
                      variant="cyan-glow"
                      size="lg"
                      className="w-full justify-center text-sm font-bold shadow-glow-cyan/30"
                    >
                      ACCESS TARANG
                    </Button>
                  </a>
                  <Link to="/how-it-works" className="flex-1 sm:flex-initial">
                    <Button
                      variant="outline"
                      size="lg"
                      className="w-full justify-center text-sm border-slate-700 hover:border-cyan-500 text-slate-200"
                    >
                      EXPLORE PLATFORM
                    </Button>
                  </Link>
                </div>

                <div className="pt-4 text-xs font-mono text-slate-400">
                  TARANG — Technology for Aquatic Recognition, Assessment, Navigation and Geo-tagging
                </div>
              </div>

              {/* Sonar preview card */}
              <div className="flex-1 w-full max-w-lg lg:max-w-none flex justify-center">
                <div className="relative w-full max-w-md rounded-2xl bg-slate-900/90 border border-slate-800 p-4 sm:p-6 shadow-2xl space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3 text-xs font-mono text-slate-400">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-slate-200 font-semibold">SSS Acoustic Channel: 455 kHz</span>
                    </div>
                    <span className="text-cyan-400">Slant Range: 50m</span>
                  </div>

                  <div className="relative h-64 sm:h-72 rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden flex flex-col justify-between p-3">
                    <div
                      className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse"
                      style={{ top: '38%' }}
                    />
                    <div className="absolute inset-y-0 left-1/2 w-0.5 bg-cyan-950/80 -translate-x-1/2 border-l border-dashed border-cyan-800/40" />

                    <div className="absolute top-1/3 left-1/4 p-2 rounded border border-cyan-400/80 bg-cyan-950/40 backdrop-blur-xs">
                      <span className="text-[10px] font-mono text-cyan-300 font-bold block">
                        TGT-01: Ghost Net
                      </span>
                      <span className="text-[9px] font-mono text-emerald-400">
                        Conf: 94.2% • Physics Valid
                      </span>
                    </div>

                    <div className="absolute bottom-1/4 right-1/4 p-2 rounded border border-teal-500/80 bg-teal-950/40 backdrop-blur-xs">
                      <span className="text-[10px] font-mono text-teal-300 font-bold block">
                        TGT-02: Pipeline
                      </span>
                      <span className="text-[9px] font-mono text-teal-400">Continuous Echo Cast</span>
                    </div>

                    <div className="flex justify-between text-[10px] font-mono text-slate-500 z-10">
                      <span>Port Channel</span>
                      <span className="text-cyan-400 font-bold">Nadir Track</span>
                      <span>Starboard Channel</span>
                    </div>

                    <div className="flex justify-between text-[10px] font-mono text-slate-500 z-10">
                      <span>Lat: 13.0827°N</span>
                      <span>Lon: 80.2707°E</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
                    <span>Geodesic PostGIS Clustering Active</span>
                    <span className="text-cyan-400">In-Process YOLOv8</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* WORKFLOW */}
        <section className="py-16 sm:py-24 bg-slate-900/30 border-b border-slate-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-3xl mx-auto space-y-3">
              <span className="text-xs font-bold tracking-widest uppercase text-cyan-400 font-mono">
                Acoustic Pipeline
              </span>
              <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-100 font-display">
                What TARANG Provides
              </h2>
              <p className="text-slate-400 text-sm sm:text-base">
                A structured end-to-end scientific workflow transforming raw sonar pings into
                actionable intelligence.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-4">
              {workflowStages.map((stage, idx) => (
                <div
                  key={stage.step}
                  className="relative p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-3 group hover:border-cyan-500/50 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-cyan-400">{stage.step}</span>
                    <div className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 group-hover:border-cyan-500/40 transition-colors">
                      {stage.icon}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                      {stage.title}
                    </h3>
                    <p className="text-[11px] text-slate-400 leading-relaxed mt-1">{stage.desc}</p>
                  </div>

                  {idx < workflowStages.length - 1 && (
                    <div className="hidden lg:block absolute -right-2.5 top-1/2 -translate-y-1/2 z-10 text-slate-600 font-bold">
                      →
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* PROBLEM STATEMENT */}
        <section className="py-16 sm:py-24 bg-slate-950 border-b border-slate-900">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 text-center">
            <span className="text-xs font-bold tracking-widest uppercase text-cyan-400 font-mono">
              The Ocean Survey Reality
            </span>

            <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-100 font-display leading-tight">
              The Seabed Contains Information We Cannot Reliably See from the Surface.
            </h2>

            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl mx-auto">
              Side-Scan Sonar provides detailed acoustic views of the seafloor, but large survey
              datasets can be difficult and time-consuming to inspect manually. TARANG is designed to
              help transform these sonar observations into structured, reviewable and geospatially
              meaningful information.
            </p>

            <div className="pt-2">
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 text-sm font-bold text-cyan-400 hover:text-cyan-300 transition-colors group"
              >
                <span>Learn How It Works</span>
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </Link>
            </div>
          </div>
        </section>

        {/* ACCESS GATEWAY */}
        <section
          id="access"
          className="relative py-16 sm:py-24 bg-gradient-to-b from-slate-900/60 to-slate-950 border-b border-slate-900"
        >
          <div className="absolute inset-0 sonar-grid-pattern opacity-15 pointer-events-none" />

          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800/60 text-xs font-mono text-cyan-300">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                <span>Role-Based Protected Infrastructure</span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-black text-slate-50 font-display">
                Select Your Access Category
              </h2>
              <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
                TARANG is designed for authorized marine, survey, research and coastal stakeholders.
                Choose the category that matches your organization role to continue to sign in.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {ACCESS_ROLES.map((role) => (
                <Link
                  key={role.slug}
                  to={`/login?role=${role.slug}`}
                  className={`group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-6 transition-all duration-200 ${role.hoverClass} hover:bg-slate-900 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/40`}
                >
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div
                        className={`p-2.5 rounded-xl bg-slate-950 border border-slate-800 ${role.iconClass} group-hover:border-slate-700 transition-colors`}
                      >
                        {role.icon}
                      </div>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border ${role.badgeClass}`}
                      >
                        {role.badge}
                      </span>
                    </div>

                    <div className="space-y-1.5">
                      <h3 className="text-base font-bold text-slate-100 font-display group-hover:text-cyan-300 transition-colors">
                        {role.title}
                      </h3>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        {role.description}
                      </p>
                    </div>
                  </div>

                  <div className="mt-6 flex items-center gap-2 text-xs font-semibold text-slate-500 group-hover:text-cyan-400 transition-colors">
                    <span>Continue to Login</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </Link>
              ))}
            </div>

            <div className="pt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
              <p className="text-sm text-slate-400">Looking for general public information?</p>
              <Link to="/public/map">
                <Button variant="outline" size="md" className="text-xs font-semibold">
                  EXPLORE PUBLIC MAP
                </Button>
              </Link>
              <span className="text-slate-600 hidden sm:inline">•</span>
              <p className="text-sm text-slate-400">Need institutional credentials?</p>
              <Link to="/request-access">
                <Button variant="secondary" size="md" className="text-xs font-semibold">
                  REQUEST ACCESS
                </Button>
              </Link>
            </div>

            <div className="pt-2 flex items-center justify-between text-[11px] font-mono text-slate-500 border-t border-slate-900">
              <span>Protected by RBAC &amp; RS256 Authentication • Strict Institutional Governance</span>
              <Link
                to="/login?role=administrator"
                className="text-slate-600 hover:text-slate-400 transition-colors underline"
              >
                Internal System Administration
              </Link>
            </div>
          </div>
        </section>

        <Footer />
      </div>
    </>
  );
};

export default LandingPage;