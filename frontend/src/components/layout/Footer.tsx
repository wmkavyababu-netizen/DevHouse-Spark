import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-900 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Col 1: Brand & Mission */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <img
                src="/tarang-logo.png"
                alt="TARANG Logo"
                className="w-8 h-8 object-contain rounded-lg p-0.5 bg-slate-900 border border-cyan-500/40 shadow-glow-cyan/30"
              />
              <span className="text-lg font-black tracking-wider text-slate-100 font-display">
                TARANG
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
              Autonomous AI-driven side-scan sonar intelligence for marine debris detection,
              physics-grounded evidence validation, geospatial clustering, and mission-critical ocean cleanup.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-mono text-slate-400">
                Core Pipeline: <span className="text-cyan-400">Active</span> • Offline In-Process Engine
              </span>
            </div>
          </div>

          {/* Col 2: Platform */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4">
              Acoustic Pipeline
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  Device Adapters (XTF/JSF)
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  TVG & Slant-Range Correction
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  YOLOv8 Acoustic Detector
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  XAI Grad-CAM Saliency
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  Shadow Physics Validation
                </span>
              </li>
            </ul>
          </div>

          {/* Col 3: Operations & Roles */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4">
              Stakeholder Portals
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li>
                <Link to="/login" className="hover:text-cyan-400 transition-colors">
                  Survey Vessel Operators
                </Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-cyan-400 transition-colors">
                  Marine Expert Review Queue
                </Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-cyan-400 transition-colors">
                  Port Authorities
                </Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-cyan-400 transition-colors">
                  Ocean Cleanup Organizations
                </Link>
              </li>
              <li>
                <Link to="/public/map" className="hover:text-cyan-400 transition-colors">
                  Public Geospatial Map
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Resources & Compliance */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4">
              Resources & Privacy
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  Acoustic Benchmark Dataset
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  PostGIS Spatial API
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  Terms of Service
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  Privacy Policy
                </span>
              </li>
              <li>
                <span className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer">
                  Security & RS256 Tokens
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-slate-900 mt-12 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} TARANG Project. Built for Marine Conservation & Ocean Cleanups.</p>
          <div className="flex items-center gap-6">
            <span>FastAPI Core</span>
            <span>•</span>
            <span>Spring Boot Auth</span>
            <span>•</span>
            <span>PostGIS Database</span>
            <span>•</span>
            <span>React + Vite</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
