import React from 'react';

export interface FrameNavigatorProps {
  currentFrame: number;
  totalFrames: number;
  onFrameChange: (frameNumber: number) => void;
  disabled?: boolean;
}

export const FrameNavigator: React.FC<FrameNavigatorProps> = ({
  currentFrame,
  totalFrames,
  onFrameChange,
  disabled = false,
}) => {
  return (
    <div className="flex items-center justify-between bg-slate-900 px-4 py-2 border border-slate-800 rounded-lg">
      <div className="text-xs text-slate-400">
        Frame <span className="text-cyan-400 font-semibold">{totalFrames > 0 ? currentFrame : 0}</span> of{' '}
        <span className="text-slate-300">{totalFrames}</span>
      </div>
      <div className="flex items-center space-x-2">
        <button
          type="button"
          disabled={disabled || currentFrame <= 1}
          onClick={() => onFrameChange(currentFrame - 1)}
          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs rounded border border-slate-700 transition"
        >
          Previous
        </button>
        <button
          type="button"
          disabled={disabled || currentFrame >= totalFrames}
          onClick={() => onFrameChange(currentFrame + 1)}
          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs rounded border border-slate-700 transition"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default FrameNavigator;
