import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Input } from '../../components/common/Input';
import { targetsApi } from '../../api';
import { DebrisTarget } from '../../types/target';

const INITIAL_TARGETS: DebrisTarget[] = [
  {
    id: 'tgt-01',
    code: 'TGT-8821',
    target_class: 'ghost_net',
    class_label: 'Ghost Net (Entanglement Hazard)',
    confidence: 0.942,
    confidence_class: 'Class A',
    latitude: 13.0827,
    longitude: 80.2707,
    depth_m: 24.5,
    cluster_radius_m: 2.1,
    observation_count: 4,
    status: 'assigned',
    hazard_level: 'critical',
    first_detected: '2026-09-10 14:22:10 UTC',
    surveys_count: 2,
    description: 'Dense synthetic monofilament snag cluster anchored to benthic outcrop. Observed across Survey A and Survey C.',
  },
  {
    id: 'tgt-02',
    code: 'TGT-8822',
    target_class: 'mine_cylinder',
    class_label: 'Mine Cylinder / Unexploded Ordnance',
    confidence: 0.965,
    confidence_class: 'Class A',
    latitude: 13.0885,
    longitude: 80.2782,
    depth_m: 18.2,
    cluster_radius_m: 1.4,
    observation_count: 5,
    status: 'validated',
    hazard_level: 'critical',
    first_detected: '2026-09-11 09:15:33 UTC',
    surveys_count: 2,
    description: 'High acoustic reflectivity cylinder with consistent shadow elongation across starboard passes. Immediate diversion advised.',
  },
  {
    id: 'tgt-03',
    code: 'TGT-8823',
    target_class: 'crab_pot',
    class_label: 'Derelict Crab Pot / Trap Cage',
    confidence: 0.884,
    confidence_class: 'Class A',
    latitude: 13.0764,
    longitude: 80.2641,
    depth_m: 12.0,
    cluster_radius_m: 0.9,
    observation_count: 2,
    status: 'detected',
    hazard_level: 'medium',
    first_detected: '2026-09-12 08:30:19 UTC',
    surveys_count: 1,
    description: 'Wire-mesh cage structure partially silted. Weak acoustic shadow consistent with benthic sediment deposition.',
  },
  {
    id: 'tgt-04',
    code: 'TGT-8824',
    target_class: 'shipwreck',
    class_label: 'Shipwreck Structural Debris',
    confidence: 0.912,
    confidence_class: 'Class A',
    latitude: 13.0931,
    longitude: 80.2855,
    depth_m: 31.8,
    cluster_radius_m: 5.6,
    observation_count: 7,
    status: 'validated',
    hazard_level: 'high',
    first_detected: '2026-09-08 11:42:00 UTC',
    surveys_count: 3,
    description: 'Fractured hull plating and rib structure spanning 14m length. Multiple acoustic shadows confirming vertical relief.',
  },
  {
    id: 'tgt-05',
    code: 'TGT-8825',
    target_class: 'submarine_pipeline',
    class_label: 'Submarine Pipeline Segment',
    confidence: 0.978,
    confidence_class: 'Class A',
    latitude: 13.0712,
    longitude: 80.2598,
    depth_m: 15.4,
    cluster_radius_m: 1.8,
    observation_count: 6,
    status: 'validated',
    hazard_level: 'high',
    first_detected: '2026-09-09 16:04:45 UTC',
    surveys_count: 2,
    description: 'Continuous linear acoustic feature partially exposed between KM 12 and KM 13. High backscatter with clean acoustic shadow.',
  },
  {
    id: 'tgt-06',
    code: 'TGT-8826',
    target_class: 'ghost_net',
    class_label: 'Derelict Trawl Net Flotilla',
    confidence: 0.825,
    confidence_class: 'Class A',
    latitude: 13.0801,
    longitude: 80.2734,
    depth_m: 22.1,
    cluster_radius_m: 3.2,
    observation_count: 3,
    status: 'cleared',
    hazard_level: 'low',
    first_detected: '2026-09-07 10:11:20 UTC',
    surveys_count: 2,
    description: 'Target removed via Mission MSN-2026-01 on 2026-09-12. Post-clearance acoustic verification confirmed clear seabed.',
  },
];

export const TargetsPage: React.FC = () => {
  const { hasRole } = useAuth();
  const isCleanup = hasRole('cleanup_organization');

  const [targets, setTargets] = useState<DebrisTarget[]>(INITIAL_TARGETS);
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [inspectTarget, setInspectTarget] = useState<DebrisTarget | null>(null);

  useEffect(() => {
    targetsApi.listTargets()
      .then((data) => {
        if (data && data.length > 0) {
          setTargets(data);
        }
      })
      .catch(() => {
        // Retain initial baseline targets in offline mode
      });
  }, []);

  const filteredTargets = targets.filter((t) => {
    // Rejected detections never appear as cleanup targets
    if ((t.status as string) === 'rejected') return false;

    // Cleanup Organizations ONLY see validated / actionable targets
    if (isCleanup && t.status === 'detected') return false;

    if (selectedClass !== 'all' && t.target_class !== selectedClass) return false;
    if (selectedStatus !== 'all' && t.status !== selectedStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        t.code.toLowerCase().includes(q) ||
        t.class_label.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getStatusBadge = (status: DebrisTarget['status']) => {
    switch (status) {
      case 'cleared':
        return <Badge variant="emerald">Cleared</Badge>;
      case 'assigned':
      case 'in_progress':
        return <Badge variant="amber">Cleanup Assigned</Badge>;
      case 'validated':
        return <Badge variant="cyan">Expert Validated</Badge>;
      case 'awaiting_validation':
        return <Badge variant="purple">Awaiting Review</Badge>;
      case 'detected':
      default:
        return <Badge variant="slate">Detected</Badge>;
    }
  };

  const getHazardBadge = (level: DebrisTarget['hazard_level']) => {
    switch (level) {
      case 'critical':
        return <Badge variant="rose">CRITICAL</Badge>;
      case 'high':
        return <Badge variant="amber">HIGH</Badge>;
      case 'medium':
        return <Badge variant="cyan">MEDIUM</Badge>;
      case 'low':
      default:
        return <Badge variant="slate">LOW</Badge>;
    }
  };

  const getClassBadge = (cls: DebrisTarget['target_class']) => {
    switch (cls) {
      case 'ghost_net':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-950/80 text-purple-300 border border-purple-800/50">Ghost Net</span>;
      case 'submarine_pipeline':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/50">Pipeline</span>;
      case 'shipwreck':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800/50">Shipwreck</span>;
      case 'mine_cylinder':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-950/80 text-rose-300 border border-rose-800/50">Mine Cylinder</span>;
      case 'crab_pot':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-950/80 text-cyan-300 border border-cyan-800/50">Crab Pot</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300">Unknown</span>;
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black tracking-tight text-slate-100 font-display">
                {isCleanup ? 'Validated Marine Cleanup Targets' : 'Debris Targets & Spatial Clusters'}
              </h1>
              <Badge variant="cyan" size="sm">
                {isCleanup ? 'Expert Validated Only' : 'PostGIS Spatial Fused'}
              </Badge>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              {isCleanup
                ? 'Exclusively verified targets approved by marine domain experts. Unverified raw detections and rejected items are excluded.'
                : 'Multi-frame acoustic targets clustered across survey passes via DBSCAN + geodesic spatial deduplication.'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {isCleanup && (
              <Link to="/missions">
                <Button variant="cyan-glow" size="sm">
                  + Plan Cleanup Mission
                </Button>
              </Link>
            )}
            <Link to="/map">
              <Button variant="secondary" size="sm">
                View on Bathymetry Map
              </Button>
            </Link>
            {!isCleanup && (
              <Link to="/workspace">
                <Button variant="primary" size="sm">
                  AI Sonar Inspector
                </Button>
              </Link>
            )}
          </div>
        </div>

        {/* Summary Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="p-4">
              <span className="text-xs text-slate-400 font-mono uppercase">Fused Targets</span>
              <div className="text-2xl font-black text-slate-100 mt-1 font-display">{targets.length}</div>
              <span className="text-[11px] text-cyan-400">Clustered from 27 frames</span>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="p-4">
              <span className="text-xs text-slate-400 font-mono uppercase">Critical Hazards</span>
              <div className="text-2xl font-black text-rose-400 mt-1 font-display">
                {targets.filter((t) => t.hazard_level === 'critical').length}
              </div>
              <span className="text-[11px] text-rose-300/80">UXO & Snag Hazards</span>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="p-4">
              <span className="text-xs text-slate-400 font-mono uppercase">Active Recoveries</span>
              <div className="text-2xl font-black text-amber-400 mt-1 font-display">
                {targets.filter((t) => t.status === 'assigned' || t.status === 'in_progress').length}
              </div>
              <span className="text-[11px] text-amber-300/80">Under Maritime Cleanup Operation</span>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="p-4">
              <span className="text-xs text-slate-400 font-mono uppercase">Cleared Targets</span>
              <div className="text-2xl font-black text-emerald-400 mt-1 font-display">
                {targets.filter((t) => t.status === 'cleared').length}
              </div>
              <span className="text-[11px] text-emerald-300/80">Verified Clear Seabed</span>
            </CardContent>
          </Card>
        </div>

        {/* Filter and Search Bar */}
        <Card className="bg-slate-900/80 border-slate-800">
          <CardContent className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="w-full md:w-72">
              <Input
                placeholder="Search target code, class, or note..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Class:</span>
                <select
                  value={selectedClass}
                  onChange={(e) => setSelectedClass(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
                >
                  <option value="all">All Classes</option>
                  <option value="ghost_net">Ghost Net</option>
                  <option value="crab_pot">Crab Pot</option>
                  <option value="submarine_pipeline">Pipeline</option>
                  <option value="shipwreck">Shipwreck</option>
                  <option value="mine_cylinder">Mine Cylinder</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Status:</span>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
                >
                  <option value="all">All Statuses</option>
                  <option value="detected">Detected</option>
                  <option value="verified">Verified</option>
                  <option value="assigned_cleanup">Assigned Cleanup</option>
                  <option value="cleared">Cleared</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Targets Table */}
        <Card className="bg-slate-900/60 border-slate-800 overflow-hidden">
          <CardHeader className="border-b border-slate-800 py-3.5 px-4 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold text-slate-200">
              Target Catalog ({filteredTargets.length} items)
            </CardTitle>
            <span className="text-xs text-slate-500 font-mono">DBSCAN Spatial Radius: 15.0m</span>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Target Code</th>
                  <th className="py-3 px-4">Class</th>
                  <th className="py-3 px-4">Coordinates (WGS84)</th>
                  <th className="py-3 px-4">Depth</th>
                  <th className="py-3 px-4">Fused Conf</th>
                  <th className="py-3 px-4">Obs</th>
                  <th className="py-3 px-4">Hazard</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTargets.map((target) => (
                  <tr key={target.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                      {target.code}
                    </td>
                    <td className="py-3 px-4">
                      {getClassBadge(target.target_class)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {target.latitude.toFixed(4)}°N, {target.longitude.toFixed(4)}°E
                      <span className="block text-[10px] text-slate-500">±{target.cluster_radius_m}m radius</span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      -{target.depth_m.toFixed(1)} m
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-emerald-400">
                      {(target.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200">
                        {target.observation_count} frames
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {getHazardBadge(target.hazard_level)}
                    </td>
                    <td className="py-3 px-4">
                      {getStatusBadge(target.status)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setInspectTarget(target)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition-colors"
                        >
                          Details
                        </button>
                        {isCleanup ? (
                          <Link
                            to={`/missions?target=${target.code}`}
                            className="px-2.5 py-1 rounded bg-emerald-950/80 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800/50 text-xs font-semibold transition-colors"
                          >
                            Assign Sortie
                          </Link>
                        ) : (
                          <Link
                            to="/workspace"
                            className="px-2 py-1 rounded bg-cyan-950/80 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-800/50 text-xs transition-colors"
                          >
                            Inspect Sonar
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Target Details Modal */}
        {inspectTarget && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <span className="text-xs font-mono text-cyan-400">{inspectTarget.code}</span>
                  <h3 className="text-lg font-bold text-slate-100">{inspectTarget.class_label}</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setInspectTarget(null)}
                  className="text-slate-400 hover:text-slate-200 text-lg p-1"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80">
                  <span className="text-slate-400 font-mono block mb-1">Acoustic Description:</span>
                  <p className="text-slate-200">{inspectTarget.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 block">Position (WGS84)</span>
                    <span className="font-mono text-cyan-300">
                      {inspectTarget.latitude.toFixed(6)}°N, {inspectTarget.longitude.toFixed(6)}°E
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 block">Estimated Depth</span>
                    <span className="font-mono text-cyan-300">-{inspectTarget.depth_m.toFixed(1)} meters</span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 block">Fused Model Confidence</span>
                    <span className="font-mono text-emerald-400 font-bold">
                      {(inspectTarget.confidence * 100).toFixed(1)}% (v1.0 model.pt)
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 block">Multi-pass Observations</span>
                    <span className="font-mono text-slate-200">
                      {inspectTarget.observation_count} frames across {inspectTarget.surveys_count} survey runs
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-slate-500">First Detection: {inspectTarget.first_detected}</span>
                  {getHazardBadge(inspectTarget.hazard_level)}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-3">
                <Button variant="secondary" size="sm" onClick={() => setInspectTarget(null)}>
                  Close
                </Button>
                <Link to="/map">
                  <Button variant="primary" size="sm">
                    Open in Geospatial Map
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default TargetsPage;
