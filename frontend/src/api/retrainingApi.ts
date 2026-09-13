import { apiClient } from './client';

export interface TriggerRetrainingPayload {
  dataset_version_id: string;
  new_version?: string;
  epochs?: number;
}

export interface TriggerRetrainingResponse {
  job_id: string;
  dataset_version_id: string;
  new_version?: string;
  status: string;
  message: string;
}

export interface RetrainingJobStatusResponse {
  job_id: string;
  status: string;
  progress_percentage?: number;
  result?: Record<string, unknown>;
  error?: string;
}

export interface CurateFeedbackResponse {
  message?: string;
  curated_count?: number;
  status?: string;
}

export interface CandidateReviewResponse {
  status: string;
  decision: 'approved' | 'rejected';
  message: string;
  notes?: string;
}

export interface ModelSummary {
  id: string;
  name: string;
  version: string;
  status: string;
  is_active: boolean;
  deployment_percentage: number;
  parameters: Record<string, unknown>;
  created_at: string;
}

export const retrainingApi = {
  async curateFeedback(datasetVersionId?: string): Promise<CurateFeedbackResponse> {
    return apiClient<CurateFeedbackResponse>('/api/v1/admin/retraining/curate', {
      method: 'POST',
      body: JSON.stringify({ dataset_version_id: datasetVersionId }),
    });
  },

  async triggerRetraining(payload: TriggerRetrainingPayload): Promise<TriggerRetrainingResponse> {
    return apiClient<TriggerRetrainingResponse>('/api/v1/admin/retraining/trigger', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getJobStatus(jobId: string): Promise<RetrainingJobStatusResponse> {
    return apiClient<RetrainingJobStatusResponse>(
      `/api/v1/admin/retraining/jobs/${encodeURIComponent(jobId)}`
    );
  },

  async listModels(): Promise<ModelSummary[]> {
    return apiClient<ModelSummary[]>('/api/v1/admin/retraining/models');
  },

  async getDrift(modelVersion: string = 'v1.0', threshold: number = 0.1): Promise<Record<string, unknown>> {
    return apiClient<Record<string, unknown>>(
      `/api/v1/admin/retraining/drift?model_version=${encodeURIComponent(modelVersion)}&threshold=${threshold}`
    );
  },

  async submitCandidateReview(
    decision: 'approved' | 'rejected',
    notes?: string
  ): Promise<CandidateReviewResponse> {
    return apiClient<CandidateReviewResponse>('/api/v1/admin/retraining/candidate/review', {
      method: 'POST',
      body: JSON.stringify({ decision, notes }),
    });
  },
};
