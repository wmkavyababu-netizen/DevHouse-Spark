import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { Navbar } from '../../components/layout/Navbar';
import { Footer } from '../../components/layout/Footer';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

// Fix Leaflet default icon paths in React/Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface PublicZone {
  id: string;
  name: string;
  region: string;
  lat: number;
  lng: number;
  debrisType: string;
  status: string;
  clusterRadiusM: number;
  description: string;
}

const PUBLIC_ZONES: PublicZone[] = [
  {
    id: 'PUB-BOB-01',
    name: 'Bay of Bengal Deep Survey Sector',
    region: 'East Coast • Tamil Nadu Offshore',
    lat: 13.0827,
    lng: 80.2707,
    debrisType: 'Ghost Nets & Derelict Gear',
    status: 'Active Cleanup Operations',
    clusterRadiusM: 800,
    description: 'Benthic survey transect showing clustered derelict monofilament nets on natural coral reef outcroppings.',
  },
  {
    id: 'PUB-MUM-02',
    name: 'Mumbai High Offshore Channel',
    region: 'West Coast • Maharashtra',
    lat: 18.922,
    lng: 72.834,
    debrisType: 'Submarine Infrastructure & Cylinders',
    status: 'Navigational Monitoring',
    clusterRadiusM: 1200,
    description: 'Navigational clearance sector monitoring exposed industrial piping and metallic cylindrical debris.',
  },
  {
    id: 'PUB-GOM-03',
    name: 'Gulf of Mannar Biosphere Zone',
    region: 'South Coast • Marine Protected Area',
    lat: 9.15,
    lng: 79.12,
    debrisType: 'Abandoned Trap Cages & Nets',
    status: 'Conservation Hotspot',
    clusterRadiusM: 650,
    description: 'High-priority marine biodiversity sanctuary with verified derelict crab and lobster pot clusters.',
  },
  {
    id: 'PUB-KCH-04',
    name: 'Cochin Port Approach Fairway',
    region: 'Southwest Coast • Kerala',
    lat: 9.965,
    lng: 76.242,
    debrisType: 'Vessel Hull Debris Field',
    status: 'Hazard Cleared',
    clusterRadiusM: 500,
    description: 'Post-cleanup acoustic verification confirming clearance of fractured hull plating in shipping lane.',
  },
];

export const PublicMapPage: React.FC = () => {
  const [selectedZone, setSelectedZone] = useState<PublicZone | null>(null);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400 font-mono">
                Public Transparency Portal • Non-Sensitive Telemetry
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-50 font-display">
              Public Marine Debris Geospatial Viewer
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Generalized coastal debris hotspots, ghost net hazard corridors, and verified cleanup zones across Indian territorial waters.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/request-access">
              <Button variant="cyan-glow" size="sm" className="font-semibold">
                Request Operational Access
              </Button>
            </Link>
          </div>
        </div>

        {/* Map and Info Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-[520px]">
          {/* Leaflet Map (3 cols) */}
          <div className="lg:col-span-3 rounded-2xl overflow-hidden border border-slate-800 glass-card relative min-h-[500px]">
            <MapContainer
              center={[13.0827, 80.2707]}
              zoom={6}
              scrollWheelZoom={true}
              style={{ width: '100%', height: '100%', minHeight: '500px' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {PUBLIC_ZONES.map((zone) => (
                <React.Fragment key={zone.id}>
                  <Circle
                    center={[zone.lat, zone.lng]}
                    radius={zone.clusterRadiusM * 50}
                    pathOptions={{
                      color: '#06b6d4',
                      fillColor: '#06b6d4',
                      fillOpacity: 0.2,
                      weight: 1.5,
                    }}
                  />

                  <Marker
                    position={[zone.lat, zone.lng]}
                    eventHandlers={{
                      click: () => setSelectedZone(zone),
                    }}
                  >
                    <Popup>
                      <div className="p-1 space-y-1 text-xs text-slate-900">
                        <div className="font-bold text-sm text-cyan-900">{zone.name}</div>
                        <div className="text-[11px] font-semibold text-slate-700">{zone.region}</div>
                        <div className="text-[11px] text-slate-600">
                          Classification: <b>{zone.debrisType}</b>
                        </div>
                        <div className="text-[10px] text-emerald-700 font-bold">
                          {zone.status}
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                </React.Fragment>
              ))}
            </MapContainer>

            {/* Selected Zone Float Card */}
            {selectedZone && (
              <div className="absolute bottom-6 right-6 z-[1000] glass-card p-4 rounded-xl border border-cyan-700/80 shadow-2xl max-w-sm space-y-2 bg-slate-900/95">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-cyan-400">{selectedZone.id}</span>
                  <button
                    type="button"
                    onClick={() => setSelectedZone(null)}
                    className="text-slate-400 hover:text-slate-200 text-xs"
                  >
                    ✕
                  </button>
                </div>
                <h4 className="text-sm font-bold text-slate-100">{selectedZone.name}</h4>
                <p className="text-xs text-slate-400">{selectedZone.region}</p>
                <div className="flex items-center gap-2 pt-1">
                  <Badge variant="cyan" size="sm">{selectedZone.debrisType}</Badge>
                  <Badge variant="emerald" size="sm">{selectedZone.status}</Badge>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed pt-1">
                  {selectedZone.description}
                </p>
              </div>
            )}
          </div>

          {/* Public Overview & Role Access Sidebar (1 col) */}
          <div className="space-y-5 flex flex-col justify-between">
            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-display">
                National Coastal Oversight
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                TARANG aggregates acoustic side-scan sonar observations into centralized spatial models to eliminate ghost gear threats and coordinate verified cleanup operations.
              </p>

              <div className="space-y-2 pt-1 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Active Monitored Regions</span>
                  <span className="font-bold text-slate-100">4 Territorial Zones</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Coordinate Privacy</span>
                  <span className="font-bold text-emerald-400">Generalized ±5km</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Supported Sensors</span>
                  <span className="font-mono text-cyan-300">455kHz / 900kHz SSS</span>
                </div>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-cyan-900/60 bg-cyan-950/20 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-300 font-mono">
                Need High-Resolution SSS Logs?
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed">
                Raw sonar waterfalls, millimeter-accurate WGS84 coordinates, and AI review queues are protected by Role-Based Access Control.
              </p>
              <div className="pt-1">
                <Link to="/request-access" className="w-full block">
                  <Button variant="cyan-glow" size="sm" className="w-full text-xs font-semibold">
                    Request Institutional Access
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default PublicMapPage;
