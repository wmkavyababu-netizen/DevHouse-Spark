/**
 * Canonical TARANG Marine Debris Target Classes
 * Aligned with backend-app/app/ai/models/registry.py and PostgreSQL target_classes schema.
 */

export interface CanonicalTargetClass {
  id: number;
  name: string;
  displayName: string;
  description: string;
  colorHex: string;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
}

export const CANONICAL_TARGET_CLASSES: CanonicalTargetClass[] = [
  {
    id: 0,
    name: 'crab_pot',
    displayName: 'Crab Pot / Trap',
    description: 'Discarded or active commercial crab/lobster pot debris resting on seabed.',
    colorHex: '#f59e0b',
    riskLevel: 'medium',
  },
  {
    id: 1,
    name: 'submarine_pipeline',
    displayName: 'Submarine Pipeline / Cable',
    description: 'Subsea pipeline structure, cable or exposed marine infrastructure section.',
    colorHex: '#3b82f6',
    riskLevel: 'high',
  },
  {
    id: 2,
    name: 'shipwreck',
    displayName: 'Shipwreck / Vessel Hull',
    description: 'Sunken vessel, shipwreck debris field, or structural hull fragments.',
    colorHex: '#ef4444',
    riskLevel: 'critical',
  },
  {
    id: 3,
    name: 'ghost_net',
    displayName: 'Ghost Net / Derelict Gear',
    description: 'Entangled or drifting derelict monofilament fishing net posing severe marine hazard.',
    colorHex: '#ec4899',
    riskLevel: 'critical',
  },
  {
    id: 4,
    name: 'mine_cylinder',
    displayName: 'Cylindrical Debris / Container',
    description: 'Cylindrical container, industrial drum, or metallic cylinder on seafloor.',
    colorHex: '#eab308',
    riskLevel: 'critical',
  },
  {
    id: 5,
    name: 'unknown',
    displayName: 'Unknown / Acoustic Anomaly',
    description: 'Unclassified acoustic anomaly or out-of-distribution candidate requiring expert review.',
    colorHex: '#94a3b8',
    riskLevel: 'low',
  },
];

export const TARGET_CLASS_NAMES = CANONICAL_TARGET_CLASSES.map((c) => c.name);

export function getCanonicalClassById(id: number): CanonicalTargetClass | undefined {
  return CANONICAL_TARGET_CLASSES.find((c) => c.id === id);
}

export function getCanonicalClassByName(name: string): CanonicalTargetClass | undefined {
  return CANONICAL_TARGET_CLASSES.find((c) => c.name === name);
}
