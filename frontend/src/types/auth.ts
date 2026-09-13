export type RoleName =
  | 'admin'
  | 'survey_operator'
  | 'marine_expert'
  | 'cleanup_organization'
  | 'government_authority';

export interface Role {
  id: string;
  name: RoleName;
  description: string;
  permissions?: Record<string, string[]>;
}

export interface Organization {
  id: string;
  name: string;
  slug?: string;
  type: string;
  country?: string;
  contactEmail?: string;
}

export interface User {
  id: string;
  email: string;
  fullName: string;
  organization?: Organization | null;
  organizationId?: string | null;
  organizationName?: string | null;
  roles: string[];
  status: string;
  isDemoMode?: boolean;
  twoFactorEnabled?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  userId: string;
  email: string;
  fullName: string;
  organizationId?: string | null;
  organizationName?: string | null;
  roles: string[];
  isDemoMode?: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  twoFactorCode?: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  fullName: string;
  organizationName?: string;
  organizationType?: string;
  requestedRole?: string;
}

export interface MessageResponse {
  message: string;
  success?: boolean;
}

/**
 * Authoritative TARANG Roles
 * 4 Primary Operational Roles + 1 Internal Admin Role
 */
export const TARANG_ROLES: Array<{
  id: RoleName;
  name: RoleName;
  label: string;
  description: string;
  badgeColor: string;
  recommendedOrgTypes: string[];
}> = [
  {
    id: 'survey_operator',
    name: 'survey_operator',
    label: 'Survey Operator',
    description: 'Upload and process Side-Scan Sonar surveys and inspect AI detections.',
    badgeColor: 'cyan',
    recommendedOrgTypes: ['Survey Agency', 'Hydrographic Directorate', 'Marine Contractor'],
  },
  {
    id: 'marine_expert',
    name: 'marine_expert',
    label: 'Marine Expert',
    description: 'Validate AI detections, review evidence, and curate feedback.',
    badgeColor: 'amber',
    recommendedOrgTypes: ['Marine Research Institute', 'Oceanographic Center', 'University'],
  },
  {
    id: 'cleanup_organization',
    name: 'cleanup_organization',
    label: 'Cleanup Organization',
    description: 'Manage validated cleanup targets and recovery missions.',
    badgeColor: 'emerald',
    recommendedOrgTypes: ['Marine Cleanup Entity', 'Salvage Contractor', 'Marine Conservation Agency'],
  },
  {
    id: 'government_authority',
    name: 'government_authority',
    label: 'Government Authority',
    description: 'Monitor overall statistics, regional coverage, and progress reports.',
    badgeColor: 'teal',
    recommendedOrgTypes: ['Maritime Board', 'Port Authority', 'Ministry Directorate'],
  },
  {
    id: 'admin',
    name: 'admin',
    label: 'Administrator',
    description: 'Internal platform administration, user access, and model improvement curation.',
    badgeColor: 'rose',
    recommendedOrgTypes: ['System Operations'],
  },
];
