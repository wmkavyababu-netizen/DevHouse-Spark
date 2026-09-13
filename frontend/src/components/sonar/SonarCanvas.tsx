import React, { useRef } from 'react';

export interface SonarCanvasProps {
  imageUrl?: string;
  onPixelClick?: (x: number, y: number) => void;
}

export const SonarCanvas: React.FC<SonarCanvasProps> = ({
  imageUrl,
  onPixelClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  if (!imageUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center text-slate-600 bg-slate-950 font-mono text-xs">
        [Awaiting frame imagery]
      </div>
    );
  }

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-black">
      <canvas
        ref={canvasRef}
        className="max-w-full max-h-full cursor-crosshair"
        onClick={(e) => {
          if (onPixelClick && canvasRef.current) {
            const rect = canvasRef.current.getBoundingClientRect();
            onPixelClick(e.clientX - rect.left, e.clientY - rect.top);
          }
        }}
      />
    </div>
  );
};

export default SonarCanvas;
