import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/common/Button';
import { Card, CardContent } from '../../components/common/Card';

export const HowItWorksPage: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Side-Scan Sonar Data Ingestion',
      subtitle: 'Raw Hydrographic Ping Files',
      desc: 'Survey vessels, towfish systems, and autonomous underwater vehicles (AUVs) collect acoustic backscatter across dual port and starboard transducers. TARANG natively parses industry formats including XTF, JSF, HSX, SDF, and standard acoustic waterfall tiles.',
      tag: 'Multi-Format Ingestion',
    },
    {
      num: '02',
      title: 'Acoustic Signal Preprocessing',
      subtitle: 'Noise Reduction & Geometric Correction',
      desc: 'Before computer vision inference, the raw signal undergoes Time-Varying Gain (TVG) normalization, nadir water-column blanking, destriping filters to eliminate acoustic banding, and vessel roll compensation.',
      tag: 'Acoustic Correction',
    },
    {
      num: '03',
      title: 'In-Process YOLOv8 Detection',
      subtitle: 'Localized Acoustic Feature Extraction',
      desc: 'The preprocessed waterfall frames are analyzed by an optimized YOLOv8 neural network trained specifically on acoustic sonar signatures across six target classes: Ghost Nets, Crab Pots, Submarine Pipelines, Shipwrecks, Mine Cylinders, and Novel Anomalies.',
      tag: 'Local YOLOv8',
    },
    {
      num: '04',
      title: 'Explainable AI & Physics Validation',
      subtitle: 'Saliency Heatmaps & Shadow Geometry',
      desc: 'Grad-CAM generates saliency heatmaps confirming that detections are grounded in genuine acoustic reflections rather than background seabed texture. Simultaneously, physics validation calculates expected shadow elongation relative to towfish altitude and slant range.',
      tag: 'Grad-CAM + Physics',
    },
    {
      num: '05',
      title: 'Geodesic Geo-tagging',
      subtitle: 'Slant-Range to WGS84 PostGIS Projection',
      desc: 'Combining vessel navigation logs, towfish layback, and pixel slant-range geometry, each target is projected into high-precision PostGIS WGS84 geographic coordinates accompanied by an acoustic uncertainty boundary radius.',
      tag: 'PostGIS Geodesic',
    },
    {
      num: '06',
      title: 'Expert Review & Active Learning',
      subtitle: 'Human-in-the-Loop Verification',
      desc: 'Marine experts review flagged candidates via a concurrency-controlled queue—accepting, rejecting, or correcting bounding boxes and classes. Decisions automatically populate active learning datasets to retrain candidate models.',
      tag: 'Closed Loop',
    },
    {
      num: '07',
      title: 'Unified Seabed Intelligence',
      subtitle: 'DBSCAN Deduplication & Sortie Planning',
      desc: 'Cross-survey DBSCAN clustering fuses duplicate observations across multiple vessel passes into a canonical debris entity. Stakeholders export actionable spatial intelligence and schedule targeted clearance sorties.',
      tag: 'Operational Intelligence',
    },
  ];

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
              <span>Scientific Workflow</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black text-slate-50 font-display">
              How TARANG Works
            </h1>
            <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
              From raw transducer echo pings to verified PostGIS targets—a seven-stage scientific pipeline built for marine reliability.
            </p>
          </div>

          {/* Workflow Steps Vertical Stack */}
          <div className="space-y-6">
            {steps.map((step) => (
              <Card key={step.num} className="bg-slate-900/80 border-slate-800 hover:border-cyan-500/50 transition-all">
                <CardContent className="p-6 sm:p-8 flex flex-col sm:flex-row gap-6 items-start">
                  <div className="flex sm:flex-col items-center gap-3">
                    <span className="w-12 h-12 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center font-mono font-black text-cyan-400 text-lg">
                      {step.num}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
                      {step.tag}
                    </span>
                  </div>

                  <div className="flex-1 space-y-2">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <h3 className="text-lg sm:text-xl font-bold text-slate-100 font-display">
                        {step.title}
                      </h3>
                      <span className="text-xs font-mono text-slate-400">{step.subtitle}</span>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Bottom Action Card */}
          <div className="p-8 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-950 border border-slate-800 text-center space-y-6">
            <h3 className="text-2xl font-bold text-slate-100 font-display">
              Explore Operational Sonar Intelligence
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 max-w-md mx-auto leading-relaxed">
              Authorized stakeholders can log in to access live survey ingestion, expert review queues, and bathymetric spatial targets.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/login">
                <Button variant="cyan-glow" size="lg">
                  Access Platform
                </Button>
              </Link>
              <Link to="/request-access">
                <Button variant="outline" size="lg">
                  Request Access
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

export default HowItWorksPage;
