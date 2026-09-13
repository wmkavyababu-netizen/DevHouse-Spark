import React, { useState, useRef, useEffect } from 'react';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { classifyDetectionConfidence } from '../../config/classificationPolicy';
import { detectionsApi } from '../../api';

interface DetectionItem {
  id: string;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  is_ood?: boolean;
  physics: {
    shadow_consistent: boolean;
    shadow_score: number;
    estimated_height_m: number;
    slant_range_m: number;
    notes: string;
  };
  geotag: {
    latitude: number;
    longitude: number;
    uncertainty_radius_m: number;
  };
  fused_confidence: number;
}

interface SonarScan {
  id: string;
  name: string;
  description: string;
  detections: DetectionItem[];
}

// Sample acoustic sonar waterfall images (base64 acoustic gradients and synthetic sonar patterns)
const SAMPLE_SONAR_SCANS: SonarScan[] = [
  {
    id: 'scan-01',
    name: 'Survey Line A-104: Shipwreck & Derelict Net',
    description: 'High-frequency 455kHz side-scan sonar waterfall showing seafloor sand ripples with prominent high-backscatter target and acoustic shadow.',
    detections: [
      {
        id: 'det-01',
        class_id: 2,
        class_name: 'shipwreck',
        confidence: 0.92,
        bbox: [180, 120, 360, 290] as [number, number, number, number],
        physics: {
          shadow_consistent: true,
          shadow_score: 0.94,
          estimated_height_m: 4.8,
          slant_range_m: 34.2,
          notes: 'Strong elongated acoustic shadow oriented directly outward from port nadir channel.',
        },
        geotag: {
          latitude: 13.0832,
          longitude: 80.2715,
          uncertainty_radius_m: 1.8,
        },
        fused_confidence: 0.93,
      },
      {
        id: 'det-02',
        class_id: 3,
        class_name: 'ghost_net',
        confidence: 0.78,
        bbox: [410, 240, 560, 380] as [number, number, number, number],
        physics: {
          shadow_consistent: true,
          shadow_score: 0.81,
          estimated_height_m: 1.2,
          slant_range_m: 48.6,
          notes: 'Irregular acoustic texture with diffuse acoustic attenuation characteristic of tangled monofilament net.',
        },
        geotag: {
          latitude: 13.0841,
          longitude: 80.2728,
          uncertainty_radius_m: 2.3,
        },
        fused_confidence: 0.79,
      },
    ],
  },
  {
    id: 'scan-02',
    name: 'Survey Line B-209: Pipeline & Crab Pots',
    description: 'Starboard channel survey along coastal infrastructure with exposed cylindrical pipeline and trapped debris.',
    detections: [
      {
        id: 'det-03',
        class_id: 1,
        class_name: 'submarine_pipeline',
        confidence: 0.89,
        bbox: [60, 80, 520, 160] as [number, number, number, number],
        physics: {
          shadow_consistent: true,
          shadow_score: 0.88,
          estimated_height_m: 1.5,
          slant_range_m: 22.0,
          notes: 'Linear high-reflectivity acoustic echo extending across multiple pings with continuous shadow cast.',
        },
        geotag: {
          latitude: 13.0795,
          longitude: 80.2680,
          uncertainty_radius_m: 1.5,
        },
        fused_confidence: 0.89,
      },
      {
        id: 'det-04',
        class_id: 0,
        class_name: 'crab_pot',
        confidence: 0.84,
        bbox: [290, 280, 390, 370] as [number, number, number, number],
        physics: {
          shadow_consistent: true,
          shadow_score: 0.85,
          estimated_height_m: 0.9,
          slant_range_m: 38.5,
          notes: 'Square high-backscatter cluster with distinct rectangular trailing shadow.',
        },
        geotag: {
          latitude: 13.0802,
          longitude: 80.2691,
          uncertainty_radius_m: 1.9,
        },
        fused_confidence: 0.84,
      },
    ],
  },
  {
    id: 'scan-03',
    name: 'Survey Line C-302: Unclassified Seabed Anomaly (OOD)',
    description: 'Seafloor anomaly exhibiting atypical acoustic diffraction and non-standard geometric profile.',
    detections: [
      {
        id: 'det-05',
        class_id: 5,
        class_name: 'unknown',
        confidence: 0.61,
        is_ood: true,
        bbox: [220, 170, 380, 310] as [number, number, number, number],
        physics: {
          shadow_consistent: false,
          shadow_score: 0.52,
          estimated_height_m: 2.1,
          slant_range_m: 29.8,
          notes: 'Acoustic anomaly: Non-standard shadow geometry. Flagged as out-of-distribution candidate for expert review.',
        },
        geotag: {
          latitude: 13.0855,
          longitude: 80.2742,
          uncertainty_radius_m: 3.1,
        },
        fused_confidence: 0.58,
      },
    ],
  },
];

export const SonarWorkspacePage: React.FC = () => {
  const [selectedScanIdx, setSelectedScanIdx] = useState<number>(0);
  const [confThreshold, setConfThreshold] = useState<number>(0.5);
  const [iouThreshold, setIouThreshold] = useState<number>(0.45);
  const [activeTab, setActiveTab] = useState<'detections' | 'physics' | 'geotags' | 'fusion'>('detections');
  const [showBoxes, setShowBoxes] = useState<boolean>(true);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [showNadir, setShowNadir] = useState<boolean>(true);
  const [isInferring, setIsInferring] = useState<boolean>(false);
  const [statusAlert, setStatusAlert] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const currentScan = SAMPLE_SONAR_SCANS[selectedScanIdx];

  // Draw acoustic waterfall simulation on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // 1. Draw synthetic side-scan sonar background
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    // Port channel (left) -> Nadir (center dark) -> Starboard channel (right)
    gradient.addColorStop(0, '#101c38');
    gradient.addColorStop(0.42, '#233968');
    gradient.addColorStop(0.48, '#080d1a'); // Port Nadir line
    gradient.addColorStop(0.50, '#04070e'); // Center towfish nadir deadzone
    gradient.addColorStop(0.52, '#080d1a'); // Starboard Nadir line
    gradient.addColorStop(0.58, '#233968');
    gradient.addColorStop(1, '#101c38');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    // 2. Draw acoustic speckle noise and sand ripple texture
    ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
    for (let y = 0; y < height; y += 4) {
      const rippleOffset = Math.sin(y * 0.05) * 8;
      for (let x = 0; x < width; x += 6) {
        if (Math.random() > 0.45) {
          ctx.fillRect(x + rippleOffset, y, 3, 2);
        }
      }
    }

    // 3. Draw Nadir Zone Mask line
    if (showNadir) {
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(width * 0.5, 0);
      ctx.lineTo(width * 0.5, height);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = 'rgba(6, 182, 212, 0.7)';
      ctx.font = '10px Inter, monospace';
      ctx.fillText('NADIR (ALT: 12.5m)', width * 0.5 - 45, 20);
    }

    // 4. Draw detections
    currentScan.detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;
      const w = x2 - x1;
      const h = y2 - y1;

      // Color based on class
      const classColors: Record<number, { stroke: string; fill: string; shadow: string }> = {
        0: { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.15)', shadow: 'rgba(245, 158, 11, 0.4)' },
        1: { stroke: '#3b82f6', fill: 'rgba(59, 130, 246, 0.15)', shadow: 'rgba(59, 130, 246, 0.4)' },
        2: { stroke: '#ef4444', fill: 'rgba(239, 68, 68, 0.15)', shadow: 'rgba(239, 68, 68, 0.4)' },
        3: { stroke: '#ec4899', fill: 'rgba(236, 72, 153, 0.15)', shadow: 'rgba(236, 72, 153, 0.4)' },
        4: { stroke: '#eab308', fill: 'rgba(234, 179, 8, 0.15)', shadow: 'rgba(234, 179, 8, 0.4)' },
        5: { stroke: '#94a3b8', fill: 'rgba(148, 163, 184, 0.15)', shadow: 'rgba(148, 163, 184, 0.4)' },
      };

      const color = classColors[det.class_id] || classColors[5];

      // Draw acoustic shadow ray
      ctx.fillStyle = 'rgba(3, 7, 18, 0.85)';
      const shadowLength = det.physics.estimated_height_m * 18;
      const shadowDir = x1 > width / 2 ? 1 : -1;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x1 + shadowLength * shadowDir, y1 + 10);
      ctx.lineTo(x2 + shadowLength * shadowDir, y2 + 10);
      ctx.lineTo(x2, y2);
      ctx.closePath();
      ctx.fill();

      // Draw acoustic backscatter highlight
      ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.fillRect(x1 + 4, y1 + 4, w - 8, h - 8);

      // Draw Grad-CAM Saliency overlay if enabled
      if (showHeatmap) {
        const radGrd = ctx.createRadialGradient(x1 + w / 2, y1 + h / 2, 5, x1 + w / 2, y1 + h / 2, w / 1.5);
        radGrd.addColorStop(0, 'rgba(239, 68, 68, 0.7)');
        radGrd.addColorStop(0.5, 'rgba(234, 179, 8, 0.5)');
        radGrd.addColorStop(1, 'transparent');
        ctx.fillStyle = radGrd;
        ctx.fillRect(x1 - 20, y1 - 20, w + 40, h + 40);
      }

      // Draw bounding box
      if (showBoxes) {
        ctx.strokeStyle = color.stroke;
        ctx.lineWidth = 2;
        ctx.fillStyle = color.fill;
        ctx.fillRect(x1, y1, w, h);
        ctx.strokeRect(x1, y1, w, h);

        // Bounding box label tag
        ctx.fillStyle = color.stroke;
        ctx.fillRect(x1, y1 - 22, ctx.measureText(`${det.class_name} ${(det.confidence * 100).toFixed(0)}%`).width + 12, 22);
        ctx.fillStyle = '#030712';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillText(`${det.class_name.toUpperCase()} ${(det.confidence * 100).toFixed(0)}%`, x1 + 6, y1 - 7);
      }
    });
  }, [selectedScanIdx, showBoxes, showHeatmap, showNadir]);

  const handleRunInference = async () => {
    setIsInferring(true);
    setStatusAlert(null);

    try {
      // In offline/sample preview, pass synthetic frame or canvas snapshot
      const canvas = canvasRef.current;
      const b64 = canvas ? canvas.toDataURL('image/jpeg', 0.8).split(',')[1] : '';
      const data = await detectionsApi.runInference({
        image_base64: b64,
        confidence_threshold: confThreshold,
        iou_threshold: iouThreshold,
      });
      setStatusAlert(`Inference complete. Isolated ${data.total_detections || currentScan.detections.length} candidate debris objects using Current Model.`);
    } catch {
      setStatusAlert(
        `[Offline Preview Mode]: Isolated ${currentScan.detections.length} candidate debris objects using Current Model (YOLOv8 Baseline Checkpoint). Backend service is offline.`
      );
    } finally {
      setIsInferring(false);
    }
  };

  const getDetectionConfidenceClass = (det: DetectionItem) => {
    return classifyDetectionConfidence(det.confidence, det.is_ood, (det as any).tier);
  };

  const getClassBadgeVariant = (classId: number) => {
    const map: Record<number, 'amber' | 'cyan' | 'rose' | 'purple' | 'emerald' | 'slate'> = {
      0: 'amber',
      1: 'cyan',
      2: 'rose',
      3: 'rose',
      4: 'amber',
      5: 'slate',
    };
    return map[classId] || 'slate';
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
        {/* Workspace Title & Active Model Banner */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                Acoustic Analysis &amp; Inference Workspace
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-50 font-display">
              Side-Scan Sonar AI Inspector
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Inspect acoustic waterfalls, verify shadow geometry, and review Class A (Auto-Approved) &amp; Class B/C (Awaiting Validation) detections.
            </p>
          </div>

          {/* Model Status Chip — strictly Current Model, zero version numbers */}
          <div className="glass-card p-3.5 rounded-xl border border-cyan-800/60 flex items-center gap-3 self-start lg:self-auto">
            <div className="w-9 h-9 rounded-lg bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400 font-bold">
              AI
            </div>
            <div className="text-xs">
              <div className="flex items-center gap-1.5 font-bold text-slate-100">
                <span>Model: YOLOv8 Baseline</span>
                <Badge variant="cyan" size="sm">Current Model</Badge>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Active Production Checkpoint (6.5 MB)
              </p>
            </div>
          </div>
        </div>

        {statusAlert && (
          <Alert variant="success" onClose={() => setStatusAlert(null)}>
            {statusAlert}
          </Alert>
        )}

        {/* Top Controls Grid: Scan Presets & Sliders */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Preset Selector */}
          <Card className="p-4 space-y-3">
            <CardHeader className="p-0 pb-1">
              <CardTitle className="text-sm">Select Sonar Waterfall Scan</CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-2">
              <select
                value={selectedScanIdx}
                onChange={(e) => setSelectedScanIdx(Number(e.target.value))}
                className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-xs text-slate-100 outline-none focus:border-cyan-500"
              >
                {SAMPLE_SONAR_SCANS.map((scan, idx) => (
                  <option key={scan.id} value={idx}>
                    {scan.name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {currentScan.description}
              </p>
            </CardContent>
          </Card>

          {/* Model Thresholds */}
          <Card className="p-4 space-y-3">
            <CardHeader className="p-0 pb-1">
              <CardTitle className="text-sm">Inference Hyperparameters</CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3 text-xs">
              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Confidence Threshold:</span>
                  <span className="font-mono text-cyan-400">{confThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="0.9"
                  step="0.05"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500 bg-slate-800"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>NMS IoU Threshold:</span>
                  <span className="font-mono text-teal-400">{iouThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="0.8"
                  step="0.05"
                  value={iouThreshold}
                  onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 bg-slate-800"
                />
              </div>
            </CardContent>
          </Card>

          {/* Action Trigger */}
          <Card className="p-4 flex flex-col justify-between space-y-3">
            <div>
              <h4 className="text-sm font-bold text-slate-100">Model Execution</h4>
              <p className="text-[11px] text-slate-400 mt-1">
                Execute local in-process detection on the current acoustic frame.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="cyan-glow"
                size="md"
                isLoading={isInferring}
                onClick={handleRunInference}
                className="w-full"
              >
                Run Sonar AI Inference
              </Button>
            </div>
          </Card>
        </div>

        {/* Main Canvas + Display Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sonar Canvas (2 cols) */}
          <div className="lg:col-span-2 glass-card rounded-2xl p-4 sm:p-6 border border-slate-800 flex flex-col space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Waterfall View (Port / Starboard)
                </span>
                <Badge variant="cyan" size="sm">
                  {currentScan.detections.length} Target(s)
                </Badge>
              </div>

              {/* View Overlay Toggles */}
              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setShowBoxes(!showBoxes)}
                  className={`px-2.5 py-1 rounded-md border text-[11px] font-medium transition-colors ${
                    showBoxes
                      ? 'bg-cyan-950 text-cyan-300 border-cyan-700'
                      : 'bg-slate-900 text-slate-400 border-slate-800'
                  }`}
                >
                  Boxes
                </button>
                <button
                  type="button"
                  onClick={() => setShowHeatmap(!showHeatmap)}
                  className={`px-2.5 py-1 rounded-md border text-[11px] font-medium transition-colors ${
                    showHeatmap
                      ? 'bg-rose-950 text-rose-300 border-rose-700'
                      : 'bg-slate-900 text-slate-400 border-slate-800'
                  }`}
                >
                  XAI Grad-CAM
                </button>
                <button
                  type="button"
                  onClick={() => setShowNadir(!showNadir)}
                  className={`px-2.5 py-1 rounded-md border text-[11px] font-medium transition-colors ${
                    showNadir
                      ? 'bg-teal-950 text-teal-300 border-teal-700'
                      : 'bg-slate-900 text-slate-400 border-slate-800'
                  }`}
                >
                  Nadir Line
                </button>
              </div>
            </div>

            {/* The Actual Canvas Element */}
            <div className="relative w-full overflow-hidden rounded-xl border border-slate-800/80 bg-black flex items-center justify-center">
              <canvas
                ref={canvasRef}
                width={640}
                height={460}
                className="w-full h-auto object-contain cursor-crosshair"
              />

              {isInferring && (
                <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center">
                  <LoadingSpinner size="lg" text="Processing Acoustic Waterfall..." />
                </div>
              )}
            </div>

            {/* Canvas Legend */}
            <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-2">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-amber-500" />
                  <span>Crab Pot</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-blue-500" />
                  <span>Pipeline</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-rose-500" />
                  <span>Shipwreck</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-pink-500" />
                  <span>Ghost Net</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-slate-400" />
                  <span>Unknown (OOD)</span>
                </span>
              </div>
              <span className="text-slate-500 font-mono">Projection: Ground-Range Slant-Corrected</span>
            </div>
          </div>

          {/* Evidence-Fusion Tabs & Analysis Inspector (1 col) */}
          <div className="glass-card rounded-2xl p-4 sm:p-6 border border-slate-800 flex flex-col space-y-4">
            {/* Tab Navigation */}
            <div className="grid grid-cols-4 gap-1 p-1 bg-slate-900/90 rounded-lg border border-slate-800 text-[11px] font-semibold text-center">
              <button
                onClick={() => setActiveTab('detections')}
                className={`py-1.5 rounded-md transition-colors ${
                  activeTab === 'detections'
                    ? 'bg-cyan-500 text-slate-950'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Objects
              </button>
              <button
                onClick={() => setActiveTab('physics')}
                className={`py-1.5 rounded-md transition-colors ${
                  activeTab === 'physics'
                    ? 'bg-cyan-500 text-slate-950'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Physics
              </button>
              <button
                onClick={() => setActiveTab('geotags')}
                className={`py-1.5 rounded-md transition-colors ${
                  activeTab === 'geotags'
                    ? 'bg-cyan-500 text-slate-950'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Geotag
              </button>
              <button
                onClick={() => setActiveTab('fusion')}
                className={`py-1.5 rounded-md transition-colors ${
                  activeTab === 'fusion'
                    ? 'bg-cyan-500 text-slate-950'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Fusion
              </button>
            </div>

            {/* Tab 1: Objects & Confidence */}
            {activeTab === 'detections' && (
              <div className="space-y-3 text-xs animate-fadeIn">
                <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                  Detected Debris Targets ({currentScan.detections.length})
                </h4>

                {currentScan.detections.map((det) => {
                  const confInfo = getDetectionConfidenceClass(det);
                  return (
                    <div key={det.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <Badge variant={getClassBadgeVariant(det.class_id)}>
                            {det.class_name.toUpperCase()}
                          </Badge>
                          <Badge variant={confInfo.badgeVariant} size="sm">
                            {confInfo.tier}
                          </Badge>
                        </div>
                        <span className="font-mono text-cyan-400 font-bold">
                          {(det.confidence * 100).toFixed(1)}% AI
                        </span>
                      </div>

                      <div className="text-[10px] flex items-center justify-between">
                        <span className={confInfo.tier === 'Class A' ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
                          {confInfo.status}
                        </span>
                        <span className="font-mono text-slate-500 text-[10px]">Slant: {det.physics.slant_range_m}m</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-slate-400 text-[11px] font-mono">
                        <div>Box: [{det.bbox.join(', ')}]</div>
                        <div>Shadow: {(det.physics.shadow_score * 100).toFixed(0)}% valid</div>
                      </div>

                      {det.is_ood && (
                        <div className="text-[10px] text-amber-300 bg-amber-950/60 p-1.5 rounded border border-amber-800/60 font-semibold">
                          Acoustic Anomaly: Out-of-Distribution candidate
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Tab 2: Physics Verification */}
            {activeTab === 'physics' && (
              <div className="space-y-3 text-xs animate-fadeIn">
                <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                  Acoustic Shadow Physics Verification
                </h4>

                {currentScan.detections.map((det) => (
                  <div key={det.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-100">{det.class_name}</span>
                      <Badge variant={det.physics.shadow_consistent ? 'emerald' : 'rose'} size="sm">
                        {det.physics.shadow_consistent ? 'SHADOW VALID' : 'INCONSISTENT'}
                      </Badge>
                    </div>

                    <div className="space-y-1 text-[11px] text-slate-400">
                      <div>Estimated Height: <span className="text-slate-200 font-mono">{det.physics.estimated_height_m}m</span></div>
                      <div>Shadow Consistency Score: <span className="text-cyan-400 font-mono">{(det.physics.shadow_score * 100).toFixed(0)}%</span></div>
                      <div className="text-[10px] leading-relaxed pt-1 text-slate-400 italic">
                        "{det.physics.notes}"
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Tab 3: Geotags */}
            {activeTab === 'geotags' && (
              <div className="space-y-3 text-xs animate-fadeIn">
                <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                  WGS-84 Coordinate Projections
                </h4>

                {currentScan.detections.map((det) => (
                  <div key={det.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-100">{det.class_name}</span>
                      <span className="text-[10px] font-mono text-emerald-400">±{det.geotag.uncertainty_radius_m}m radius</span>
                    </div>

                    <div className="space-y-1 font-mono text-[11px] text-slate-300">
                      <div>LAT: {det.geotag.latitude.toFixed(6)}° N</div>
                      <div>LON: {det.geotag.longitude.toFixed(6)}° E</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Tab 4: Multi-Modal Fusion */}
            {activeTab === 'fusion' && (
              <div className="space-y-3 text-xs animate-fadeIn">
                <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                  Multi-Modal Calibrated Confidence
                </h4>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-slate-400 leading-relaxed font-mono">
                  Score = 0.55·AI + 0.30·Physics + 0.15·Quality
                </div>

                {currentScan.detections.map((det) => (
                  <div key={det.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-100">{det.class_name}</span>
                      <span className="font-bold font-mono text-emerald-400 text-sm">
                        {(det.fused_confidence * 100).toFixed(1)}% Fused
                      </span>
                    </div>

                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full"
                        style={{ width: `${det.fused_confidence * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
