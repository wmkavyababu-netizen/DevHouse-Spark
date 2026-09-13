import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/common/Button';
import { Card, CardContent } from '../../components/common/Card';

export const AboutPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950 font-sans">
      <Navbar />

      <main className="flex-1 py-12 sm:py-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 sonar-grid-pattern opacity-20 pointer-events-none" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-4xl mx-auto space-y-12">
          
          {/* Section Header */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Platform Mission & Context</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black text-slate-50 font-display">
              About TARANG
            </h1>
            <p className="text-xs sm:text-sm font-mono uppercase tracking-widest text-cyan-400 font-semibold">
              Technology for Aquatic Recognition, Assessment, Navigation and Geo-tagging
            </p>
          </div>

          {/* Mission Narrative */}
          <div className="p-6 sm:p-10 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6 text-slate-300 text-sm sm:text-base leading-relaxed">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-100 font-display">
              India's First Unified Seabed Mapping Intelligent Platform
            </h2>

            <p>
              The seafloor is a vast, dark and dynamic domain. While surface marine waste and shoreline debris are readily visible, discarded fishing gear, industrial pipelines, lost equipment, and sunken obstructions settle onto the seabed where they remain undetected for decades.
            </p>

            <p>
              Traditional optical imaging cannot penetrate murky, low-light benthic depths. Hydrographic survey teams rely on high-frequency **Side-Scan Sonar (SSS)** to scan expansive undersea swaths. However, manual frame-by-frame analysis of thousands of acoustic echo records is labor-intensive and prone to human inspection fatigue.
            </p>

            <p className="font-semibold text-cyan-300">
              TARANG was created to bridge this gap: transforming raw, scattered acoustic sonar pings into structured, geospatially anchored, and scientifically verified marine intelligence.
            </p>
          </div>

          {/* Core Operating Principles */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-slate-900/60 border-slate-800">
              <CardContent className="p-6 space-y-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400 font-mono font-bold">
                  01
                </div>
                <h3 className="text-base font-bold text-slate-100 font-display">Scientific Integrity</h3>
                <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                  Detections are grounded in physical acoustic principles—including shadow length, slant-range geometry, and Grad-CAM saliency verification.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800">
              <CardContent className="p-6 space-y-3">
                <div className="w-10 h-10 rounded-xl bg-teal-950/80 border border-teal-800/60 flex items-center justify-center text-teal-400 font-mono font-bold">
                  02
                </div>
                <h3 className="text-base font-bold text-slate-100 font-display">Offline First</h3>
                <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                  Inference runs entirely in-process inside survey vessel computers without reliance on external cloud servers or third-party APIs.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800">
              <CardContent className="p-6 space-y-3">
                <div className="w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-800/60 flex items-center justify-center text-purple-400 font-mono font-bold">
                  03
                </div>
                <h3 className="text-base font-bold text-slate-100 font-display">Human-in-the-Loop</h3>
                <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                  Marine experts review and validate detected targets, directly feeding verified annotations back into continuous model retraining.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Access CTA Strip */}
          <div className="p-8 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-950 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="space-y-1 text-center sm:text-left">
              <h3 className="text-lg font-bold text-slate-100 font-display">Ready to deploy TARANG for your operations?</h3>
              <p className="text-xs text-slate-400">Institutional credentials required for platform access.</p>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/request-access">
                <Button variant="cyan-glow" size="md">
                  Request Access
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="md">
                  Login
                </Button>
              </Link>
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
};

export default AboutPage;
