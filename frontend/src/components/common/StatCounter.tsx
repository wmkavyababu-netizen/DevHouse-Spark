import React, { useEffect, useRef, useState } from 'react';

export interface StatCounterProps {
  end: number;
  duration?: number; // duration in ms
  prefix?: string;
  suffix?: string;
  decimals?: number;
  label: string;
  description: string;
  tag?: string;
  isLive?: boolean;
}

export const StatCounter: React.FC<StatCounterProps> = ({
  end,
  duration = 2000,
  prefix = '',
  suffix = '',
  decimals = 0,
  label,
  description,
  tag = 'Illustrative Estimate',
  isLive = false,
}) => {
  const [count, setCount] = useState(0);
  const [hasStarted, setHasStarted] = useState(false);
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasStarted) {
          setHasStarted(true);
        }
      },
      { threshold: 0.2 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => observer.disconnect();
  }, [hasStarted]);

  useEffect(() => {
    if (!hasStarted) return;

    let startTime: number | null = null;
    let animationFrameId: number;

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      // Ease out cubic
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const currentVal = easedProgress * end;

      setCount(currentVal);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setCount(end);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrameId);
  }, [hasStarted, end, duration]);

  const formattedValue = count.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  return (
    <div
      ref={elementRef}
      className="glass-card glass-card-hover p-6 rounded-2xl flex flex-col justify-between relative overflow-hidden"
    >
      {/* Top Tag */}
      <div className="flex items-center justify-between mb-4">
        <span
          className={`text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full border ${
            isLive
              ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800/60'
              : 'bg-cyan-950/80 text-cyan-400 border-cyan-800/60'
          }`}
        >
          {isLive ? 'Live Database' : tag}
        </span>
        <div className="w-2 h-2 rounded-full bg-cyan-500/40 animate-ping" />
      </div>

      {/* Main Counter Value */}
      <div className="my-2">
        <div className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-50 font-display flex items-baseline">
          {prefix && <span className="text-cyan-400 mr-1">{prefix}</span>}
          <span>{formattedValue}</span>
          {suffix && <span className="text-cyan-400 ml-1">{suffix}</span>}
        </div>
        <h4 className="text-sm font-semibold text-slate-200 mt-2">{label}</h4>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-400 leading-relaxed mt-2 border-t border-slate-800/80 pt-3">
        {description}
      </p>
    </div>
  );
};
