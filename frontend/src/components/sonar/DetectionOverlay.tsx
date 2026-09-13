import React from 'react';

export interface DetectionBox {
  id: string;
  className: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
}

export interface DetectionOverlayProps {
  detections: DetectionBox[];
  selectedDetectionId?: string | null;
  onSelectDetection?: (id: string) => void;
  visible?: boolean;
}

export const DetectionOverlay: React.FC<DetectionOverlayProps> = ({
  detections,
  selectedDetectionId,
  onSelectDetection,
  visible = true,
}) => {
  if (!visible || detections.length === 0) {
    return null;
  }

  return (
    <div className="absolute inset-0 pointer-events-none">
      {detections.map((det) => {
        const [x1, y1, x2, y2] = det.bbox;
        const width = x2 - x1;
        const height = y2 - y1;
        const isSelected = selectedDetectionId === det.id;

        return (
          <div
            key={det.id}
            onClick={() => onSelectDetection && onSelectDetection(det.id)}
            style={{
              left: `${x1}px`,
              top: `${y1}px`,
              width: `${width}px`,
              height: `${height}px`,
            }}
            className={`absolute border-2 pointer-events-auto cursor-pointer transition ${
              isSelected
                ? 'border-amber-400 bg-amber-400/20 shadow-lg shadow-amber-500/20'
                : 'border-cyan-400 bg-cyan-400/10 hover:border-cyan-300'
            }`}
          >
            <div className="absolute -top-5 left-0 bg-slate-900/90 text-[10px] text-cyan-300 px-1.5 py-0.5 rounded whitespace-nowrap border border-cyan-800">
              {det.className} ({(det.confidence * 100).toFixed(1)}%)
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DetectionOverlay;
