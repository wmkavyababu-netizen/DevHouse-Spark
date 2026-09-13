import { apiClient } from './client';
import { DebrisTarget } from '../types/target';

export const targetsApi = {
  async listTargets(targetClass?: string, status?: string): Promise<DebrisTarget[]> {
    const params = new URLSearchParams();
    if (targetClass && targetClass !== 'all') params.append('class', targetClass);
    if (status && status !== 'all') params.append('status', status);

    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient<DebrisTarget[]>(`/api/v1/targets${qs}`);
  },

  async getTarget(targetId: string): Promise<DebrisTarget> {
    return apiClient<DebrisTarget>(`/api/v1/targets/${encodeURIComponent(targetId)}`);
  },
};
