export type RejectionReasonId =
  | 'false_positive'
  | 'class_confusion'
  | 'acoustic_artifact'
  | 'poor_image_quality'
  | 'difficult_environment'
  | 'other';

export interface FeedbackCategorySummary {
  name: string;
  count: number;
  pct: number;
  color: string;
}

export interface FeedbackRecord {
  id: string;
  detection_id: string;
  survey_id?: string;
  predicted_class: string;
  predicted_confidence: number;
  confidence_class: string;
  expert_decision: 'accepted' | 'corrected' | 'rejected';
  rejection_reason?: string;
  corrected_class?: string;
  expert_notes?: string;
  expert_name: string;
  timestamp: string;
}

export interface CandidateEvaluationMetric {
  className: string;
  currentScore: number;
  candidateScore: number;
  delta: string;
  status: 'Improved' | 'Regressed' | 'Maintained';
}
