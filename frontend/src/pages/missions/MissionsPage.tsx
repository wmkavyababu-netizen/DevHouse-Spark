import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Alert } from '../../components/common/Alert';
import { FormField } from '../../components/common/FormField';
import { Input } from '../../components/common/Input';
import { missionsApi } from '../../api';

interface Mission {
  id: string;
  name: string;
  target_cluster: string;
  target_count: number;
  assigned_vessel: string;
  lead_agency: string;
  status: 'active' | 'completed' | 'planned';
  estimated_recovery_kg: number;
  recovered_kg: number;
  date: string;
}

const SAMPLE_MISSIONS: Mission[] = [
  {
    id: 'MSN-2026-01',
    name: 'Bay of Bengal Ghost Gear Extraction Sortie 1',
    target_cluster: 'Cluster #104: 3x Derelict Gillnets',
    target_count: 3,
    assigned_vessel: 'Ocean Guardian (Support Tug + Crane)',
    lead_agency: 'Ocean Cleanup Taskforce',
    status: 'active',
    estimated_recovery_kg: 1850,
    recovered_kg: 620,
    date: '2026-09-12',
  },
  {
    id: 'MSN-2026-02',
    name: 'Harbor Channel Navigational Hazard Clearance',
    target_cluster: 'Cluster #089: 2x Metal Drums + Hull Debris',
    target_count: 2,
    assigned_vessel: 'Port Tender 4 (Commercial Diver Unit)',
    lead_agency: 'Port Authority',
    status: 'completed',
    estimated_recovery_kg: 920,
    recovered_kg: 920,
    date: '2026-09-08',
  },
];

export const MissionsPage: React.FC = () => {
  const [missions, setMissions] = useState<Mission[]>(SAMPLE_MISSIONS);
  const [missionName, setMissionName] = useState('');
  const [vessel, setVessel] = useState('Ocean Guardian (ROV Unit)');
  const [targetCluster, setTargetCluster] = useState('Cluster #104: Ghost Net Snag Field');
  const [recoveryEstimate, setRecoveryEstimate] = useState('1200');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    missionsApi.listMissions()
      .then((data) => {
        if (data && data.length > 0) {
          setMissions(data.map((m) => ({
            id: m.id,
            name: m.name,
            target_cluster: m.target_cluster || 'Cluster #104',
            target_count: m.target_count || 2,
            assigned_vessel: m.assigned_vessel,
            lead_agency: m.lead_agency,
            status: (m.status === 'active' || m.status === 'completed' || m.status === 'planned') ? m.status : 'planned',
            estimated_recovery_kg: m.estimated_recovery_kg || 1000,
            recovered_kg: m.recovered_kg || 0,
            date: m.date || '2026-09-12',
          })));
        }
      })
      .catch(() => {
        // Fallback in offline demo
      });
  }, []);

  const handleCreateMission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!missionName.trim()) return;

    try {
      const res = await missionsApi.createMission({
        name: missionName.trim(),
        target_cluster: targetCluster,
        assigned_vessel: vessel,
        lead_agency: 'Maritime Cleanup Unit',
        target_ids: ['tgt-01', 'tgt-02'],
        estimated_recovery_kg: Number(recoveryEstimate) || 1000,
      });

      const newMsn: Mission = {
        id: res.id || `MSN-2026-0${missions.length + 1}`,
        name: missionName.trim(),
        target_cluster: targetCluster,
        target_count: 2,
        assigned_vessel: vessel,
        lead_agency: 'Maritime Cleanup Unit',
        status: 'planned',
        estimated_recovery_kg: Number(recoveryEstimate) || 1000,
        recovered_kg: 0,
        date: new Date().toISOString().split('T')[0],
      };

      setMissions([newMsn, ...missions]);
      setMissionName('');
      setSuccessMsg(`Cleanup mission '${newMsn.name}' scheduled and route waypoints generated.`);
    } catch {
      // Local sandbox fallback
      const newMsn: Mission = {
        id: `MSN-2026-0${missions.length + 1}`,
        name: missionName.trim(),
        target_cluster: targetCluster,
        target_count: 2,
        assigned_vessel: vessel,
        lead_agency: 'Maritime Cleanup Unit',
        status: 'planned',
        estimated_recovery_kg: Number(recoveryEstimate) || 1000,
        recovered_kg: 0,
        date: new Date().toISOString().split('T')[0],
      };

      setMissions([newMsn, ...missions]);
      setMissionName('');
      setSuccessMsg(`[Offline Mode]: Cleanup mission '${newMsn.name}' scheduled locally.`);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-7xl mx-auto animate-fadeIn">
        {/* Title */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
              Maritime Cleanup Operations
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-50 font-display">
            Ocean Cleanup Missions
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Dispatch recovery vessels, track verified diver sorties, and record quantitative marine debris tonnage extracted.
          </p>
        </div>

        {successMsg && (
          <Alert variant="success" onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Missions List (2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-base font-bold text-slate-100 font-display">
              Operational Sorties ({missions.length})
            </h3>

            {missions.map((m) => {
              const progressPct = m.estimated_recovery_kg > 0
                ? Math.min(100, Math.round((m.recovered_kg / m.estimated_recovery_kg) * 100))
                : 0;

              return (
                <div key={m.id} className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-mono font-bold text-cyan-400">{m.id}</span>
                      <span className="text-slate-500 text-xs">•</span>
                      <span className="text-xs text-slate-400">{m.lead_agency}</span>
                    </div>
                    <Badge variant={m.status === 'completed' ? 'emerald' : m.status === 'active' ? 'cyan' : 'slate'} size="sm">
                      {m.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="space-y-1">
                    <h4 className="text-lg font-bold text-slate-100 font-display">{m.name}</h4>
                    <p className="text-xs text-slate-400">Target Area: <span className="text-slate-200">{m.target_cluster}</span></p>
                    <p className="text-xs text-slate-400">Vessel Assigned: <span className="text-cyan-300 font-medium">{m.assigned_vessel}</span></p>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1.5 pt-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Extracted Debris Progress:</span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {m.recovered_kg} / {m.estimated_recovery_kg} kg ({progressPct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-teal-500 to-emerald-400 h-full transition-all duration-300"
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Plan New Mission Form (1 col) */}
          <Card className="p-6 space-y-5">
            <CardHeader className="p-0 pb-1">
              <CardTitle>Schedule Cleanup Mission</CardTitle>
              <p className="text-xs text-slate-400 mt-1">
                Plan recovery sortie based on verified PostGIS debris cluster.
              </p>
            </CardHeader>

            <CardContent className="p-0">
              <form onSubmit={handleCreateMission} className="space-y-4">
                <FormField id="msn-name" label="Mission Title" required={true}>
                  <Input
                    id="msn-name"
                    value={missionName}
                    onChange={(e) => setMissionName(e.target.value)}
                    placeholder="e.g. Reef Ghost Net Recovery Sortie #2"
                    required
                  />
                </FormField>

                <FormField id="msn-target" label="Target Debris Cluster">
                  <select
                    id="msn-target"
                    value={targetCluster}
                    onChange={(e) => setTargetCluster(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-xs text-slate-100 outline-none focus:border-cyan-500"
                  >
                    <option value="Cluster #104: Ghost Net Snag Field">Cluster #104: Ghost Net Snag Field (High Risk)</option>
                    <option value="Cluster #089: Harbor Debris Trench">Cluster #089: Harbor Debris Trench (Nav Hazard)</option>
                    <option value="Cluster #201: Coastal Crab Pot Density">Cluster #201: Coastal Crab Pot Density (Medium)</option>
                  </select>
                </FormField>

                <FormField id="msn-vessel" label="Assigned Vessel / Diver Unit">
                  <Input
                    id="msn-vessel"
                    value={vessel}
                    onChange={(e) => setVessel(e.target.value)}
                  />
                </FormField>

                <FormField id="msn-est" label="Estimated Debris Weight (kg)">
                  <Input
                    id="msn-est"
                    type="number"
                    value={recoveryEstimate}
                    onChange={(e) => setRecoveryEstimate(e.target.value)}
                  />
                </FormField>

                <div className="pt-2">
                  <Button type="submit" variant="cyan-glow" size="md" className="w-full">
                    Dispatch Mission
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};
