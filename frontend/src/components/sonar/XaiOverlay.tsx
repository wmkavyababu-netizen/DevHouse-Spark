import React from 'react';

export interface XaiOverlayProps {
  heatmapUrl?: string;
  opacity?: number;
  visible?: boolean;
}

export const XaiOverlay: React.FC<XaiOverlayProps> = ({
  heatmapUrl,
  opacity = 0.6,
  visible = false,
}) => {
  if (!visible || !heatmapUrl) {
    return null;
  }

  return (
    <img
      src={heatmapUrl}
      alt="XAI Grad-CAM Heatmap"
      style={{ opacity }}
      className="absolute inset-0 w-full h-full object-contain pointer-events-none mix-blend-color-dodge"
    />
  );
};

export default XaiOverlay;
