import React from 'react';

export interface SonarMetadata {
  deviceModel?: string;
  frequencyKhz?: number;
  altitudeMeters?: number;
  headingDegrees?: number;
  speedKnots?: number;
  latitude?: number;
  longitude?: number;
}

export interface SonarMetadataPanelProps {
  metadata?: SonarMetadata | null;
  isLoading?: boolean;
}

export const SonarMetadataPanel: React.FC<SonarMetadataPanelProps> = ({
  metadata,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-slate-400">
        Loading sonar telemetry metadata...
      </div>
    );
  }

  if (!metadata) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-lg text-xs text-slate-500">
        No telemetry or navigation metadata available for this frame.
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-3">
      <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
        Telemetry & Navigation
      </h4>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-slate-400">Device:</span>
          <p className="font-mono text-slate-200">{metadata.deviceModel ?? 'Unknown'}</p>
        </div>
        <div>
          <span className="text-slate-400">Frequency:</span>
          <p className="font-mono text-slate-200">{metadata.frequencyKhz ? `${metadata.frequencyKhz} kHz` : 'N/A'}</p>
        </div>
        <div>
          <span className="text-slate-400">Altitude:</span>
          <p className="font-mono text-slate-200">{metadata.altitudeMeters ? `${metadata.altitudeMeters} m` : 'N/A'}</p>
        </div>
        <div>
          <span className="text-slate-400">Heading:</span>
          <p className="font-mono text-slate-200">{metadata.headingDegrees ? `${metadata.headingDegrees}°` : 'N/A'}</p>
        </div>
        <div className="col-span-2">
          <span className="text-slate-400">Position:</span>
          <p className="font-mono text-slate-200 text-[11px]">
            {metadata.latitude !== undefined && metadata.longitude !== undefined
              ? `${metadata.latitude.toFixed(6)}° N, ${metadata.longitude.toFixed(6)}° E`
              : 'GPS unavailable'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SonarMetadataPanel;
