import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../common/Button';

export const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const navLinks = [
    { label: 'Home', path: '/' },
    { label: 'About', path: '/about' },
    { label: 'How It Works', path: '/how-it-works' },
    { label: 'Technology', path: '/technology' },
    { label: 'Access Platform', path: '/#access' },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 text-slate-900 shadow-sm transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          
          {/* Left: Official TARANG Logo & Positioning */}
          <div className="flex items-center gap-3 sm:gap-4">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="relative flex items-center justify-center">
                <img
                  src="/logo.png"
                  alt="TARANG Logo"
                  className="w-10 h-10 sm:w-12 sm:h-12 object-contain rounded-xl p-0.5 bg-slate-50 border border-slate-200 shadow-xs group-hover:scale-105 transition-transform"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-lg sm:text-xl font-black tracking-wider text-slate-900 font-display group-hover:text-cyan-700 transition-colors">
                  TARANG
                </span>
                <span className="hidden sm:inline-block text-[9px] tracking-widest uppercase font-mono text-cyan-700 -mt-0.5 font-semibold">
                  Seabed Intelligence Platform
                </span>
              </div>
            </Link>

            {/* Institutional Area: Dedicated slot for approved Ministry of Earth Sciences / Government Symbol Asset */}
            <div className="hidden xl:flex items-center pl-4 border-l border-slate-200">
              <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-[10px] font-mono text-slate-600">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-600" />
                <span>Institutional Portal • Marine Research & Surveys</span>
              </div>
            </div>
          </div>

          {/* Center Navigation Links (Minimal & Clear per Prompt Section 3) */}
          <nav className="hidden md:flex items-center gap-6 lg:gap-8">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.label}
                  to={link.path}
                  className={`text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-cyan-700 font-bold border-b-2 border-cyan-600 pb-0.5'
                      : 'text-slate-600 hover:text-cyan-700'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right: Primary Action / Auth */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <Link
                  to="/dashboard"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 hover:border-cyan-500 transition-colors"
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>{user?.fullName || 'Authorized User'}</span>
                </Link>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/dashboard')}
                >
                  Dashboard
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="text-slate-600 hover:text-rose-600"
                >
                  Sign Out
                </Button>
              </div>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm" className="text-slate-700 hover:text-slate-900 hover:bg-slate-100">
                    Login
                  </Button>
                </Link>
                <Link to="/request-access">
                  <Button variant="cyan-glow" size="sm" className="font-bold shadow-md shadow-cyan-600/20">
                    GET STARTED
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="md:hidden flex items-center gap-2">
            <Link to="/login">
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
                Login
              </span>
            </Link>
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              aria-label="Toggle Navigation Menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu Drawer (Light/White Marine per Section 16) */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-200 p-5 space-y-4 shadow-lg animate-fadeIn text-slate-800">
          <nav className="flex flex-col space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-cyan-700"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="border-t border-slate-200 pt-4 flex flex-col gap-2.5">
            {isAuthenticated ? (
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  setMobileMenuOpen(false);
                  navigate('/dashboard');
                }}
                className="w-full justify-center"
              >
                Open Dashboard
              </Button>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" size="md" className="w-full justify-center border-slate-300 text-slate-800 hover:bg-slate-50">
                    Login
                  </Button>
                </Link>
                <Link to="/request-access" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="cyan-glow" size="md" className="w-full justify-center font-bold">
                    GET STARTED
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
