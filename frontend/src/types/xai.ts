export interface XaiEvidence {
  detection_id: string;
  class_id: number;
  class_name: string;
  confidence: number;
  confidence_class: string;
  saliency_score: number;
  saliency_focus: string;
  energy_inside_ratio: number;
  shadow_consistent: boolean;
  shadow_score: number;
  estimated_height_m: number;
  slant_range_m: number;
  explanation_notes: string;
  heatmap_base64?: string;
  heatmap_image_url?: string;
}
