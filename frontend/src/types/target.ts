export type TargetStatus =
  | 'detected'
  | 'awaiting_validation'
  | 'validated'
  | 'assigned'
  | 'in_progress'
  | 'cleared'
  | 'rejected';

export type HazardLevel = 'critical' | 'high' | 'medium' | 'low';

export interface DebrisTarget {
  id: string;
  code: string;
  target_class: string;
  class_label: string;
  confidence: number;
  confidence_class: string;
  latitude: number;
  longitude: number;
  depth_m: number;
  cluster_radius_m: number;
  observation_count: number;
  status: TargetStatus;
  hazard_level: HazardLevel;
  first_detected: string;
  surveys_count: number;
  description: string;
}
