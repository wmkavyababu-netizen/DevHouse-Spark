import React from 'react';

export interface PhysicsEvidence {
  slantRangeMeters?: number;
  acousticShadowLengthMeters?: number;
  expectedSizeMeters?: number;
  shadowConsistencyScore?: number;
  isPlausible?: boolean;
}

export interface PhysicsEvidencePanelProps {
  evidence?: PhysicsEvidence | null;
  isLoading?: boolean;
}

export const PhysicsEvidencePanel: React.FC<PhysicsEvidencePanelProps> = ({
  evidence,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-slate-400">
        Calculating acoustic physics validation...
      </div>
    );
  }

  if (!evidence) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-xs text-slate-500">
        No physics validation data available for this selection.
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Acoustic Physics Evidence</h4>
        <span
          className={`text-[10px] px-2 py-0.5 rounded font-medium ${
            evidence.isPlausible
              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
              : 'bg-amber-950 text-amber-400 border border-amber-800'
          }`}
        >
          {evidence.isPlausible ? 'Plausible' : 'Check Warning'}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-slate-400">Slant Range:</span>
          <p className="font-mono text-slate-200">{evidence.slantRangeMeters?.toFixed(2) ?? 'N/A'} m</p>
        </div>
        <div>
          <span className="text-slate-400">Shadow Length:</span>
          <p className="font-mono text-slate-200">{evidence.acousticShadowLengthMeters?.toFixed(2) ?? 'N/A'} m</p>
        </div>
        <div>
          <span className="text-slate-400">Expected Size:</span>
          <p className="font-mono text-slate-200">{evidence.expectedSizeMeters?.toFixed(2) ?? 'N/A'} m</p>
        </div>
        <div>
          <span className="text-slate-400">Shadow Score:</span>
          <p className="font-mono text-slate-200">
            {evidence.shadowConsistencyScore ? `${(evidence.shadowConsistencyScore * 100).toFixed(1)}%` : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PhysicsEvidencePanel;
