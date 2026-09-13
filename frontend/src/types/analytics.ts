export interface RemediationPipelineCounts {
  stage1_detected: number;
  stage2_validated: number;
  stage3_assigned: number;
  stage4_in_progress: number;
  stage5_completed: number;
}

export interface GovernmentOverviewData {
  has_live_telemetry: boolean;
  survey_coverage_km2: number | null;
  confirmed_hotspots_count: number | null;
  clearance_rate_pct: number | null;
  active_vessels_count: number | null;
  total_classified_targets: number;
  total_recovered_kg: number;
  pipeline: RemediationPipelineCounts;
}
