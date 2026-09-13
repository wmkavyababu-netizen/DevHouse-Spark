import { apiClient } from './client';

export interface ReviewQueueItem {
  id: string;
  survey_title: string;
  frame_number: number;
  class_id: number;
  class_name: string;
  confidence: number;
  confidence_class: 'Class A' | 'Class B' | 'Class C';
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  claimed_by: string | null;
  status: 'unreviewed' | 'claimed' | 'validated' | 'rejected' | 'corrected';
  notes?: string;
  image_url?: string;
  bbox?: [number, number, number, number];
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReviewDecisionPayload {
  decision: 'accepted' | 'corrected' | 'rejected';
  corrected_class_id?: number;
  rejection_reason?: string;
  notes?: string;
}

export const reviewsApi = {
  async getQueue(page = 1, pageSize = 20): Promise<ReviewQueueResponse> {
    return apiClient<ReviewQueueResponse>(`/api/v1/reviews/queue?page=${page}&page_size=${pageSize}`);
  },

  async claimDetection(detectionId: string, timeoutMinutes = 30): Promise<{ claimed: boolean; message: string }> {
    return apiClient<{ claimed: boolean; message: string }>(
      `/api/v1/reviews/claim/${encodeURIComponent(detectionId)}?timeout_minutes=${timeoutMinutes}`,
      { method: 'POST' }
    );
  },

  async releaseClaim(detectionId: string): Promise<{ released: boolean }> {
    return apiClient<{ released: boolean }>(
      `/api/v1/reviews/release/${encodeURIComponent(detectionId)}`,
      { method: 'POST' }
    );
  },

  async submitDecision(detectionId: string, payload: ReviewDecisionPayload): Promise<{ success: boolean; message: string }> {
    return apiClient<{ success: boolean; message: string }>(
      `/api/v1/reviews/decision?detection_id=${encodeURIComponent(detectionId)}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },
};
