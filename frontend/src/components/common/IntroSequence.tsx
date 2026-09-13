import React, { useState, useEffect } from 'react';

interface IntroSequenceProps {
  onComplete: () => void;
}

export const IntroSequence: React.FC<IntroSequenceProps> = ({ onComplete }) => {
  const [typedTitle, setTypedTitle] = useState('');
  const [showSubtitle, setShowSubtitle] = useState(false);
  const [showTagline, setShowTagline] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);

  const fullTitle = 'TARANG';

  useEffect(() => {
    // Step 1: Type TARANG letter by letter
    let currentIdx = 0;
    const typingInterval = setInterval(() => {
      if (currentIdx <= fullTitle.length) {
        setTypedTitle(fullTitle.slice(0, currentIdx));
        currentIdx++;
      } else {
        clearInterval(typingInterval);

        // Step 2: Reveal acronym definition after 400ms
        setTimeout(() => {
          setShowSubtitle(true);

          // Step 3: Reveal national platform positioning after 800ms
          setTimeout(() => {
            setShowTagline(true);

            // Step 4: Smooth transition into homepage after 1200ms
            setTimeout(() => {
              triggerExit();
            }, 1800);
          }, 800);
        }, 400);
      }
    }, 120);

    return () => clearInterval(typingInterval);
  }, []);

  const triggerExit = () => {
    setIsFadingOut(true);
    setTimeout(() => {
      onComplete();
    }, 700);
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950 text-slate-100 transition-opacity duration-700 select-none ${
        isFadingOut ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      {/* Subtle Acoustic Sonar Sweeping Grid (Calm, Scientific) */}
      <div className="absolute inset-0 sonar-grid-pattern opacity-25 pointer-events-none" />
      <div className="absolute w-[36rem] h-[36rem] rounded-full border border-cyan-500/10 pointer-events-none animate-pulse" />
      <div className="absolute w-[24rem] h-[24rem] rounded-full border border-cyan-500/15 pointer-events-none" />
      <div className="absolute w-[12rem] h-[12rem] rounded-full border border-cyan-500/20 pointer-events-none" />

      {/* Center Identity Container */}
      <div className="relative z-10 max-w-3xl px-6 text-center space-y-6">
        
        {/* Actual TARANG Logo Asset */}
        <div className="flex justify-center mb-2">
          <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl p-1 bg-slate-900/90 border border-cyan-500/40 shadow-2xl shadow-cyan-950 flex items-center justify-center">
            <img
              src="/logo.png"
              alt="TARANG Emblem"
              className="w-full h-full object-contain filter drop-shadow-[0_4px_12px_rgba(6,182,212,0.3)]"
            />
          </div>
        </div>

        {/* Step 1: Type TARANG */}
        <div className="h-16 sm:h-20 flex items-center justify-center">
          <h1 className="text-4xl sm:text-6xl font-black tracking-widest text-slate-50 font-display">
            {typedTitle}
            <span className="inline-block w-1.5 h-10 sm:h-14 bg-cyan-400 ml-2 animate-pulse align-middle" />
          </h1>
        </div>

        {/* Step 2: Acronym Definition */}
        <div
          className={`transition-all duration-700 transform ${
            showSubtitle ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
          }`}
        >
          <p className="text-xs sm:text-base font-mono tracking-wider text-cyan-300 uppercase font-semibold">
            Technology for Aquatic Recognition, Assessment, Navigation and Geo-tagging
          </p>
        </div>

        {/* Step 3: Positioning Statement */}
        <div
          className={`transition-all duration-700 delay-100 transform ${
            showTagline ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
          }`}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-800/60 shadow-glow-cyan/20 text-xs sm:text-sm font-medium text-slate-200">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>India's First Unified Seabed Mapping Intelligent Platform</span>
          </div>
        </div>

      </div>

      {/* Skip Button in Bottom Corner */}
      <button
        type="button"
        onClick={triggerExit}
        className="absolute bottom-8 right-8 z-20 px-4 py-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300 hover:text-cyan-300 transition-colors flex items-center gap-2"
        aria-label="Skip Introduction"
      >
        <span>Skip Intro</span>
        <span className="text-[10px] text-slate-500 border border-slate-700 px-1.5 py-0.5 rounded">ESC</span>
      </button>

      {/* System Caliber Subtitle */}
      <div className="absolute bottom-8 left-8 text-[11px] font-mono text-slate-600 hidden sm:block">
        Side-Scan Sonar Marine Intelligence System
      </div>
    </div>
  );
};

export default IntroSequence;
