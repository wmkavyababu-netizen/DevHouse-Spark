import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Badge } from '../../components/common/Badge';

// Fix Leaflet default icon paths in React/Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface TargetPoint {
  id: string;
  name: string;
  class_name: string;
  class_id: number;
  lat: number;
  lng: number;
  confidence: number;
  observations: number;
  depth_m: number;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
}

const SAMPLE_TARGETS: TargetPoint[] = [
  {
    id: 'TRG-BAY-001',
    name: 'Sunken Cargo Vessel Hull Fragment',
    class_name: 'shipwreck',
    class_id: 2,
    lat: 13.0832,
    lng: 80.2715,
    confidence: 0.94,
    observations: 3,
    depth_m: 24.5,
    risk_level: 'critical',
  },
  {
    id: 'TRG-BAY-002',
    name: 'Submerged Ghost Net Snag Field',
    class_name: 'ghost_net',
    class_id: 3,
    lat: 13.0881,
    lng: 80.2782,
    confidence: 0.82,
    observations: 2,
    depth_m: 18.2,
    risk_level: 'critical',
  },
  {
    id: 'TRG-BAY-003',
    name: 'Coastal Subsea Gas Pipeline Segment',
    class_name: 'submarine_pipeline',
    class_id: 1,
    lat: 13.0765,
    lng: 80.2650,
    confidence: 0.91,
    observations: 4,
    depth_m: 31.0,
    risk_level: 'high',
  },
  {
    id: 'TRG-BAY-004',
    name: 'Commercial Crab Pot Cluster (Derelict)',
    class_name: 'crab_pot',
    class_id: 0,
    lat: 13.0815,
    lng: 80.2690,
    confidence: 0.86,
    observations: 1,
    depth_m: 15.4,
    risk_level: 'medium',
  },
  {
    id: 'TRG-BAY-005',
    name: 'Cylindrical Industrial Metal Drum',
    class_name: 'mine_cylinder',
    class_id: 4,
    lat: 13.0862,
    lng: 80.2730,
    confidence: 0.88,
    observations: 2,
    depth_m: 21.8,
    risk_level: 'critical',
  },
];

export const GeospatialMapPage: React.FC = () => {
  const [selectedRisk, setSelectedRisk] = useState<string>('all');
  const [selectedTarget, setSelectedTarget] = useState<TargetPoint | null>(null);

  const filteredTargets = SAMPLE_TARGETS.filter((t) => {
    if (selectedRisk === 'all') return true;
    return t.risk_level === selectedRisk;
  });

  return (
    <DashboardLayout>
      <div className="space-y-4 max-w-7xl mx-auto animate-fadeIn h-[calc(100vh-6rem)] flex flex-col">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                PostGIS Geospatial Hotspots & Clusters
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-50 font-display">
              Marine Debris Bathymetric Map
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2 outline-none focus:border-cyan-500"
            >
              <option value="all">All Hazards ({SAMPLE_TARGETS.length})</option>
              <option value="critical">Critical Risk Only</option>
              <option value="high">High Risk Only</option>
              <option value="medium">Medium Risk Only</option>
            </select>
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 w-full rounded-2xl overflow-hidden border border-slate-800 relative z-10 glass-card">
          <MapContainer
            center={[13.0827, 80.2707]}
            zoom={14}
            scrollWheelZoom={true}
            style={{ width: '100%', height: '100%', minHeight: '480px' }}
          >
            {/* OpenStreetMap Dark / Clean Ocean Basemap */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {filteredTargets.map((target) => (
              <React.Fragment key={target.id}>
                {/* Uncertainty Radius Circle */}
                <Circle
                  center={[target.lat, target.lng]}
                  radius={45}
                  pathOptions={{
                    color: target.risk_level === 'critical' ? '#ef4444' : '#06b6d4',
                    fillColor: target.risk_level === 'critical' ? '#ef4444' : '#06b6d4',
                    fillOpacity: 0.25,
                    weight: 1.5,
                  }}
                />

                {/* Target Marker with Popup */}
                <Marker
                  position={[target.lat, target.lng]}
                  eventHandlers={{
                    click: () => setSelectedTarget(target),
                  }}
                >
                  <Popup>
                    <div className="p-1 space-y-1.5 text-xs text-slate-900">
                      <div className="font-bold text-sm text-cyan-900">{target.id}</div>
                      <div className="font-semibold">{target.name}</div>
                      <div className="text-[11px] text-slate-600">
                        Class: <b>{target.class_name}</b> | Conf: <b>{(target.confidence * 100).toFixed(0)}%</b>
                      </div>
                      <div className="text-[11px] text-slate-600">
                        Depth: {target.depth_m}m | Observations: {target.observations}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500 pt-1">
                        {target.lat.toFixed(5)}° N, {target.lng.toFixed(5)}° E
                      </div>
                    </div>
                  </Popup>
                </Marker>
              </React.Fragment>
            ))}
          </MapContainer>

          {/* Floating Selected Target Details Card */}
          {selectedTarget && (
            <div className="absolute bottom-6 right-6 z-[1000] glass-card p-4 rounded-xl border border-cyan-700/80 shadow-2xl max-w-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-cyan-400">{selectedTarget.id}</span>
                <button
                  type="button"
                  onClick={() => setSelectedTarget(null)}
                  className="text-slate-400 hover:text-slate-200 text-xs"
                >
                  ✕
                </button>
              </div>
              <h4 className="text-sm font-bold text-slate-100">{selectedTarget.name}</h4>
              <div className="flex items-center gap-2">
                <Badge variant={selectedTarget.risk_level === 'critical' ? 'rose' : 'cyan'} size="sm">
                  {selectedTarget.risk_level.toUpperCase()}
                </Badge>
                <span className="text-xs font-mono text-emerald-400">
                  {(selectedTarget.confidence * 100).toFixed(0)}% Fused Conf
                </span>
              </div>
              <div className="text-[11px] text-slate-400 space-y-0.5 pt-1">
                <div>Depth: {selectedTarget.depth_m}m</div>
                <div>Observations: {selectedTarget.observations} acoustic passes</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
