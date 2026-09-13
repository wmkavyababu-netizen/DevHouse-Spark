import { apiClient } from './client';
import { SurveyRecord, SurveyCreatePayload } from '../types/survey';

export const surveysApi = {
  async listSurveys(status?: string): Promise<SurveyRecord[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiClient<SurveyRecord[]>(`/api/v1/surveys${query}`);
  },

  async getSurvey(id: string): Promise<SurveyRecord> {
    return apiClient<SurveyRecord>(`/api/v1/surveys/${encodeURIComponent(id)}`);
  },

  async createSurvey(payload: SurveyCreatePayload): Promise<SurveyRecord> {
    return apiClient<SurveyRecord>('/api/v1/surveys', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
