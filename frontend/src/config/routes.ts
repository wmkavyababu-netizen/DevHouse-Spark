/**
 * TARANG Application Route Constants
 */
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  SURVEYS: '/surveys',
  SURVEY_DETAIL: (id: string = ':id') => `/surveys/${id}`,
  SURVEY_UPLOAD: '/surveys/upload',
  SONAR_VIEWER: (id: string = ':id') => `/surveys/${id}/viewer`,
  TARGETS: '/targets',
  TARGET_DETAIL: (id: string = ':id') => `/targets/${id}`,
  MAP: '/map',
  REVIEW: '/review',
  MISSIONS: '/missions',
  ANALYTICS: '/analytics',
  REPORTS: '/reports',
  ADMIN: '/admin',
} as const;
