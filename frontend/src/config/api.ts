/**
 * TARANG API Endpoints and Base Configuration
 * Note: Handled via same-origin Nginx gateway
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const AUTH_API_PREFIX = '/api/auth';
export const APP_API_PREFIX = '/api/v1';

export const API_ENDPOINTS = {
  // Auth Service Endpoints (Spring Boot)
  AUTH: {
    LOGIN: `${AUTH_API_PREFIX}/login`,
    REGISTER: `${AUTH_API_PREFIX}/register`,
    REFRESH: `${AUTH_API_PREFIX}/refresh`,
    LOGOUT: `${AUTH_API_PREFIX}/logout`,
    FORGOT_PASSWORD: `${AUTH_API_PREFIX}/forgot-password`,
    RESET_PASSWORD: `${AUTH_API_PREFIX}/reset-password`,
    ME: `${AUTH_API_PREFIX}/me`,
  },
  // Application & Pipeline Endpoints (FastAPI)
  APP: {
    HEALTH: `${APP_API_PREFIX}/health`,
    SURVEYS: `${APP_API_PREFIX}/surveys`,
    FRAMES: `${APP_API_PREFIX}/frames`,
    DETECTIONS: `${APP_API_PREFIX}/detections`,
    TARGETS: `${APP_API_PREFIX}/targets`,
    REVIEWS: `${APP_API_PREFIX}/reviews`,
    MISSIONS: `${APP_API_PREFIX}/missions`,
    ANALYTICS: `${APP_API_PREFIX}/analytics`,
    PUBLIC: `${APP_API_PREFIX}/public`,
    RETRAINING: `${APP_API_PREFIX}/admin/retraining`,
    REPORTS: `${APP_API_PREFIX}/reports`,
  },
} as const;
