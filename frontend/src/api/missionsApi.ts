import { apiClient } from './client';
import { CleanupMission, MissionCreatePayload } from '../types/mission';

export const missionsApi = {
  async listMissions(status?: string): Promise<CleanupMission[]> {
    const query = status && status !== 'all' ? `?status=${encodeURIComponent(status)}` : '';
    return apiClient<CleanupMission[]>(`/api/v1/missions${query}`);
  },

  async createMission(payload: MissionCreatePayload): Promise<CleanupMission> {
    return apiClient<CleanupMission>('/api/v1/missions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateMissionStatus(
    missionId: string,
    status: string,
    recoveredKg?: number,
    notes?: string
  ): Promise<CleanupMission> {
    return apiClient<CleanupMission>(`/api/v1/missions/${encodeURIComponent(missionId)}/status`, {
      method: 'PATCH',
      body: JSON.stringify({
        status,
        recovered_kg: recoveredKg,
        notes,
      }),
    });
  },
};
