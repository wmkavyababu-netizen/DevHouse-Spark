export interface NavigationTelemetry {
  latitude: number;
  longitude: number;
  altitude_m: number;
  depth_m: number;
  heading_deg: number;
  pitch_deg: number;
  roll_deg: number;
  speed_knots: number;
  timestamp?: string;
}

export interface SurveyRecord {
  id: string;
  title: string;
  vessel: string;
  altitude_m: number;
  frequency_khz: number;
  format: string;
  file_size_mb: number;
  frames_count: number;
  quality_score: number;
  status: 'uploaded' | 'validating' | 'processing' | 'completed' | 'failed';
  created_at: string;
  detections_count: number;
  notes: string;
}

export interface SurveyCreatePayload {
  title: string;
  vessel?: string;
  altitude_m?: number;
  frequency_khz?: number;
  format?: string;
  notes?: string;
}
