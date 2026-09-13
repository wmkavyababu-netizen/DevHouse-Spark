import { apiClient } from './client';
import { XaiEvidence } from '../types/xai';

export interface AdHocInferencePayload {
  image_base64: string;
  confidence_threshold?: number;
  iou_threshold?: number;
}

export interface AdHocInferenceResponse {
  model_version: string;
  model_checksum: string;
  detections: Array<{
    class_id: number;
    class_name: string;
    confidence: number;
    bbox: [number, number, number, number];
  }>;
  total_detections: number;
}

export const detectionsApi = {
  async getTargetClasses(): Promise<Record<number, string>> {
    return apiClient<Record<number, string>>('/api/v1/detections/classes');
  },

  async runInference(payload: AdHocInferencePayload): Promise<AdHocInferenceResponse> {
    return apiClient<AdHocInferenceResponse>('/api/v1/detections/infer', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getDetectionXai(detectionId: string): Promise<XaiEvidence> {
    return apiClient<XaiEvidence>(`/api/v1/detections/${encodeURIComponent(detectionId)}/xai`);
  },
};
