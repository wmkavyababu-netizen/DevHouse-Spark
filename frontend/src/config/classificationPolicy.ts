/**
 * TARANG Centralized Classification & Confidence Routing Policy
 * Drives Class A / Class B / Class C detection tiers across the platform.
 * Can be configured via system settings or backend API response.
 */

export interface ClassificationPolicy {
  classAThreshold: number; // High confidence threshold (e.g. 0.80) -> Auto-Approved
  classBThreshold: number; // Medium confidence threshold (e.g. 0.60) -> Awaiting Validation
  allowAutoApproval: boolean;
}

export const DEFAULT_CLASSIFICATION_POLICY: ClassificationPolicy = {
  classAThreshold: 0.80,
  classBThreshold: 0.60,
  allowAutoApproval: true,
};

export type ConfidenceTier = 'Class A' | 'Class B' | 'Class C';

export interface TierClassification {
  tier: ConfidenceTier;
  badgeVariant: 'emerald' | 'amber' | 'slate';
  label: string;
  status: string;
}

/**
 * Classifies detection confidence according to the centralized policy
 * Prioritizes backend-supplied tier/status if present.
 */
export function classifyDetectionConfidence(
  confidence: number,
  isOod?: boolean,
  backendTier?: string | null,
  policy: ClassificationPolicy = DEFAULT_CLASSIFICATION_POLICY
): TierClassification {
  // 1. Authoritative Backend Tier Check
  if (backendTier) {
    const clean = backendTier.toUpperCase();
    if (clean.includes('CLASS A') || clean === 'A' || clean === 'AUTO_APPROVED') {
      return {
        tier: 'Class A',
        badgeVariant: 'emerald',
        label: 'Class A • High Confidence',
        status: 'Auto-Approved Pipeline',
      };
    }
    if (clean.includes('CLASS B') || clean === 'B') {
      return {
        tier: 'Class B',
        badgeVariant: 'amber',
        label: 'Class B • Medium Confidence',
        status: 'Awaiting Marine Expert Validation',
      };
    }
    if (clean.includes('CLASS C') || clean === 'C' || clean === 'OOD') {
      return {
        tier: 'Class C',
        badgeVariant: 'slate',
        label: 'Class C • Low Confidence / Anomaly',
        status: 'Awaiting Marine Expert Validation',
      };
    }
  }

  // 2. Centralized Policy Evaluation
  if (isOod || confidence < policy.classBThreshold) {
    return {
      tier: 'Class C',
      badgeVariant: 'slate',
      label: 'Class C • Low Confidence / Anomaly',
      status: 'Awaiting Marine Expert Validation',
    };
  }

  if (confidence >= policy.classAThreshold && policy.allowAutoApproval) {
    return {
      tier: 'Class A',
      badgeVariant: 'emerald',
      label: 'Class A • High Confidence',
      status: 'Auto-Approved Pipeline',
    };
  }

  return {
    tier: 'Class B',
    badgeVariant: 'amber',
    label: 'Class B • Medium Confidence',
    status: 'Awaiting Marine Expert Validation',
  };
}
