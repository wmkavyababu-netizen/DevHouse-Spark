import { ConfidenceTier } from '../config/classificationPolicy';

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface AcousticPhysicsEvidence {
  shadow_consistent: boolean;
  shadow_score: number;
  estimated_height_m: number;
  slant_range_m: number;
  notes: string;
}

export interface GeotagInfo {
  latitude: number;
  longitude: number;
  uncertainty_radius_m: number;
}

export interface DetectionItem {
  id: string;
  survey_id?: string;
  frame_number?: number;
  class_id: number;
  class_name: string;
  confidence: number;
  confidence_class: ConfidenceTier;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  is_ood?: boolean;
  status: 'awaiting_validation' | 'auto_approved' | 'validated' | 'rejected' | 'corrected';
  physics: AcousticPhysicsEvidence;
  geotag: GeotagInfo;
  fused_confidence: number;
  crop_image_url?: string;
  waterfall_image_url?: string;
}
