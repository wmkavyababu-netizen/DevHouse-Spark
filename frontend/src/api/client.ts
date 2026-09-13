import { API_BASE_URL } from '../config/api';

export interface ApiError {
  status: number;
  message: string;
  detail?: any;
}

const ACCESS_TOKEN_KEY = 'tarang_access_token';

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    'X-Correlation-ID': `tarang-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      // Unauthorized: could dispatch logout event if in production
      throw {
        status: 401,
        message: 'Session expired or unauthorized. Please sign in again.',
      } as ApiError;
    }

    if (res.status === 403) {
      throw {
        status: 403,
        message: 'Forbidden: You do not have permission to perform this action.',
      } as ApiError;
    }

    if (!res.ok) {
      let detailMessage = `Request failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        detailMessage = errorData.detail || errorData.message || detailMessage;
      } catch {
        // Response wasn't JSON
      }
      throw {
        status: res.status,
        message: detailMessage,
      } as ApiError;
    }

    if (res.status === 204) {
      return {} as T;
    }

    return (await res.json()) as T;
  } catch (err: any) {
    if (err.status) {
      throw err;
    }
    // Network error / offline
    throw {
      status: 0,
      message: err.message || 'Network connection failed. Backend service may be unreachable.',
    } as ApiError;
  }
}
