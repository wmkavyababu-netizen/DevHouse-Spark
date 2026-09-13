import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/common/Button';
import { Card, CardContent } from '../../components/common/Card';

export const TechnologyPage: React.FC = () => {
  const techPillars = [
    {
      title: 'Acoustic Signal Processing',
      badge: 'Physical Hydroacoustics',
      points: [
        'Time-Varying Gain (TVG) correction compensating for underwater acoustic spreading and absorption losses.',
        'Dynamic nadir column blanking to eliminate false positive reflections in the central water column.',
        'Wavelet destriping filters reducing acoustic beam interference and vessel cavitation noise.',
        'IMU sensor roll-compensation preventing distorted ping offsets during turbulent sea states.',
      ],
    },
    {
      title: 'In-Process YOLOv8 Architecture',
      badge: 'Edge Neural Inference',
      points: [
        'Custom-trained convolutional backbones optimized for side-scan sonar backscatter texture.',
        'Direct local PyTorch/ONNX inference executing in-process without third-party API dependencies.',
        'Fine-tuned multi-scale detection anchors designed for small derelict pots and sprawling ghost nets.',
        'Canary model release gates requiring verified mAP improvement before operational deployment.',
      ],
    },
    {
      title: 'Physics-Grounded Evidence Validation',
      badge: 'Acoustic Optics Verification',
      points: [
        'Slant-range to ground-range geometric projection using towfish altitude and acoustic wave speed.',
        'Acoustic shadow length calculations verifying target height above the seafloor bed.',
        'Aspect-ratio and backscatter intensity checks ruling out natural biogenic sedimentary forms.',
        'Grad-CAM saliency heatmaps highlighting neural attention on acoustic echo-shadow pairs.',
      ],
    },
    {
      title: 'PostGIS Geodesic Spatial Intelligence',
      badge: 'Geospatial Clustering',
      points: [
        'Dead-reckoning navigation fusion integrating ship GPS, USBL positioning, and towfish layback.',
        'Geodesic distance calculations ensuring sub-meter spatial precision on ellipsoidal coordinates.',
        'DBSCAN cross-survey spatial clustering fusing repeated sonar passes into canonical entities.',
        'Automatic target uncertainty radius generation for diver and ROV clearance planning.',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950 font-sans">
      <Navbar />

      <main className="flex-1 py-12 sm:py-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 sonar-grid-pattern opacity-20 pointer-events-none" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-4xl mx-auto space-y-12">
          
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>System Architecture</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black text-slate-50 font-display">
              TARANG Technology
            </h1>
            <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Engineered specifically for harsh marine operational environments—combining hydroacoustic signal processing, local computer vision, and spatial database clustering.
            </p>
          </div>

          {/* Pillars Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {techPillars.map((pillar) => (
              <Card key={pillar.title} className="bg-slate-900/80 border-slate-800 hover:border-cyan-500/40 transition-all">
                <CardContent className="p-6 sm:p-8 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
                      {pillar.badge}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-slate-100 font-display">
                    {pillar.title}
                  </h3>

                  <ul className="space-y-2.5 text-xs text-slate-300">
                    {pillar.points.map((pt, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-cyan-400 mt-0.5">•</span>
                        <span className="leading-relaxed">{pt}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Security & Governance Box */}
          <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <h3 className="text-base font-bold text-slate-100 font-display">
                Institutional Data Security & Governance
              </h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              All raw hydrographic logs, vessel navigation tracklines, and detected seabed coordinates are isolated behind Role-Based Access Control (RBAC) with RS256 token verification. Sensitive underwater target locations are restricted to verified institutional users.
            </p>
          </div>

          {/* Access CTA */}
          <div className="p-8 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-950 border border-slate-800 text-center space-y-6">
            <h3 className="text-2xl font-bold text-slate-100 font-display">
              Request Platform Clearance
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 max-w-md mx-auto leading-relaxed">
              TARANG technology is accessible to authorized government, port, hydrographic, and marine research partners.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/request-access">
                <Button variant="cyan-glow" size="lg">
                  Submit Access Request
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" size="lg">
                  Login to Platform
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

export default TechnologyPage;
