import React from 'react';

export interface SonarViewerProps {
  surveyId?: string;
  frameId?: string;
  isLoading?: boolean;
  error?: string | null;
}

export const SonarViewer: React.FC<SonarViewerProps> = ({
  surveyId,
  frameId,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-slate-900 border border-slate-800 rounded-lg text-slate-400">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
          <span>Loading sonar frame...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-950/20 border border-red-900/50 rounded-lg text-red-400">
        <p>Error loading sonar imagery: {error}</p>
      </div>
    );
  }

  if (!surveyId || !frameId) {
    return (
      <div className="flex items-center justify-center h-96 bg-slate-900 border border-slate-800 rounded-lg text-slate-500">
        <p>No sonar survey or frame selected.</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[600px] bg-black rounded-lg overflow-hidden border border-slate-800">
      <div className="absolute top-3 left-3 z-10 bg-slate-900/80 px-3 py-1 rounded text-xs text-cyan-400 border border-slate-700">
        Survey: {surveyId} | Frame: {frameId}
      </div>
      {/* SonarCanvas and overlays will mount here */}
    </div>
  );
};

export default SonarViewer;
