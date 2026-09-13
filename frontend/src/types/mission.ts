export type MissionStatus = 'planned' | 'active' | 'completed' | 'cancelled';

export interface CleanupMission {
  id: string;
  name: string;
  target_cluster: string;
  target_count: number;
  assigned_vessel: string;
  lead_agency: string;
  status: MissionStatus;
  estimated_recovery_kg: number;
  recovered_kg: number;
  date: string;
  notes?: string;
}

export interface MissionCreatePayload {
  name: string;
  target_cluster: string;
  assigned_vessel?: string;
  lead_agency?: string;
  target_ids?: string[];
  estimated_recovery_kg?: number;
  notes?: string;
}
