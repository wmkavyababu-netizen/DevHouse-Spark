/**
 * TARANG System Constants & Class Ontologies
 */
export const TARGET_CLASSES = [
  'ghost_net',
  'pipeline',
  'tyre',
  'metal_debris',
  'plastic_debris',
  'container',
  'shipwreck',
  'unknown_object',
] as const;

export type TargetClassType = (typeof TARGET_CLASSES)[number];

export const PIPELINE_STAGES = [
  'ingestion',
  'nadir_mask',
  'slant_range',
  'tvg_calibration',
  'destriping',
  'denoising',
  'enhancement',
  'quality_assessment',
  'ai_inference',
  'physics_validation',
  'geotagging',
  'deduplication',
] as const;

export const USER_ROLES = {
  ADMIN: 'ADMIN',
  OPERATOR: 'OPERATOR',
  EXPERT_REVIEWER: 'EXPERT_REVIEWER',
  MISSION_PLANNER: 'MISSION_PLANNER',
  VIEWER: 'VIEWER',
} as const;
