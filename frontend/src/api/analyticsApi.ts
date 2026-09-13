import { apiClient } from './client';
import { GovernmentOverviewData, RemediationPipelineCounts } from '../types/analytics';

export const analyticsApi = {
  async getOverview(): Promise<GovernmentOverviewData> {
    return apiClient<GovernmentOverviewData>('/api/v1/analytics/overview');
  },

  async getPipeline(): Promise<RemediationPipelineCounts> {
    return apiClient<RemediationPipelineCounts>('/api/v1/analytics/pipeline');
  },
};
