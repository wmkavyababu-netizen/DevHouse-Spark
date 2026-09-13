import React from 'react';

export interface SegmentationOverlayProps {
  maskUrl?: string;
  opacity?: number;
  visible?: boolean;
}

export const SegmentationOverlay: React.FC<SegmentationOverlayProps> = ({
  maskUrl,
  opacity = 0.5,
  visible = true,
}) => {
  if (!visible || !maskUrl) {
    return null;
  }

  return (
    <img
      src={maskUrl}
      alt="U-Net Segmentation Overlay"
      style={{ opacity }}
      className="absolute inset-0 w-full h-full object-contain pointer-events-none mix-blend-screen"
    />
  );
};

export default SegmentationOverlay;
