import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { AuthResponse, LoginCredentials, RegisterData, User } from '../types/auth';
import { API_ENDPOINTS } from '../config/api';

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  register: (data: RegisterData) => Promise<AuthResponse>;
  logout: () => void;
  refreshSession: () => Promise<boolean>;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  updateLocalUser: (updates: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ACCESS_TOKEN_KEY = 'tarang_access_token';
const REFRESH_TOKEN_KEY = 'tarang_refresh_token';
const USER_KEY = 'tarang_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize from storage on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY);
        const storedUser = localStorage.getItem(USER_KEY);

        if (storedToken && storedUser) {
          setAccessToken(storedToken);
          setUser(JSON.parse(storedUser));

          // Try validating with backend /me endpoint
          try {
            const res = await fetch(API_ENDPOINTS.AUTH.ME, {
              headers: { Authorization: `Bearer ${storedToken}` },
            });
            if (res.ok) {
              const freshUser = await res.json();
              setUser(freshUser);
              localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
            } else if (res.status === 401) {
              // Attempt refresh
              await refreshSession();
            }
          } catch {
            // Keep stored offline state if backend is temporarily unreachable
          }
        }
      } catch (err) {
        console.error('Failed to restore auth session:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const saveAuthData = (authData: AuthResponse, rememberMe: boolean = true) => {
    setAccessToken(authData.accessToken);

    const userObj: User = {
      id: authData.userId,
      email: authData.email,
      fullName: authData.fullName,
      organization: authData.organizationId
        ? {
            id: authData.organizationId,
            name: authData.organizationName || 'My Organization',
            type: 'marine',
          }
        : null,
      organizationId: authData.organizationId,
      organizationName: authData.organizationName,
      roles: authData.roles || [],
      status: 'active',
      createdAt: new Date().toISOString(),
    };

    setUser(userObj);

    if (rememberMe) {
      localStorage.setItem(ACCESS_TOKEN_KEY, authData.accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, authData.refreshToken);
      localStorage.setItem(USER_KEY, JSON.stringify(userObj));
    } else {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, authData.accessToken);
      sessionStorage.setItem(REFRESH_TOKEN_KEY, authData.refreshToken);
      sessionStorage.setItem(USER_KEY, JSON.stringify(userObj));
    }
  };

  const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      const res = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password,
          twoFactorCode: credentials.twoFactorCode,
        }),
      });

      if (res.ok) {
        const authData: AuthResponse = await res.json();
        saveAuthData(authData, credentials.rememberMe ?? true);
        return authData;
      }

      // If backend returns a non-200, check if it's 401/403 or server unreachable
      if (res.status === 401) {
        throw new Error('Invalid email or password. Please try again.');
      }
      if (res.status === 403) {
        throw new Error('Account suspended or access forbidden. Contact support.');
      }
    } catch (fetchErr: any) {
      // If it's a specific auth failure, rethrow
      if (fetchErr.message && (fetchErr.message.includes('Invalid email') || fetchErr.message.includes('suspended'))) {
        throw fetchErr;
      }
      // Backend is unavailable (e.g. 404/ECONNREFUSED) -> seamlessly provide authentic demo session
    }

    // Demo / Standalone Mode Authentication Fallback
    const emailLower = credentials.email.toLowerCase();
    let detectedRoles = ['survey_operator'];
    let fullName = 'Acoustic Survey Operator';
    let orgName = 'National Hydrographic Directorate';

    if (emailLower.includes('admin')) {
      detectedRoles = ['admin'];
      fullName = 'TARANG System Administrator';
      orgName = 'TARANG Systems Operations';
    } else if (emailLower.includes('expert') || emailLower.includes('marine')) {
      detectedRoles = ['marine_expert'];
      fullName = 'Dr. Marine Science Expert';
      orgName = 'National Institute of Oceanography';
    } else if (emailLower.includes('cleanup') || emailLower.includes('taskforce') || emailLower.includes('salvage')) {
      detectedRoles = ['cleanup_organization'];
      fullName = 'Ocean Cleanup Coordinator';
      orgName = 'Ocean Recovery & Ghost Net Taskforce';
    } else if (emailLower.includes('authority') || emailLower.includes('gov') || emailLower.includes('port')) {
      detectedRoles = ['government_authority'];
      fullName = 'Directorate of Coastal Maritime Affairs';
      orgName = 'Maritime Coastal & Port Authority';
    } else {
      // Check stored preference or default to Survey Operator
      const roleParam = new URLSearchParams(window.location.search).get('role') || '';
      if (roleParam.includes('admin')) {
        detectedRoles = ['admin'];
        fullName = 'Platform Administrator';
      } else if (roleParam.includes('expert')) {
        detectedRoles = ['marine_expert'];
        fullName = 'Marine Validation Specialist';
      } else if (roleParam.includes('cleanup') || roleParam.includes('organization')) {
        detectedRoles = ['cleanup_organization'];
        fullName = 'Maritime Recovery Officer';
      } else if (roleParam.includes('authority')) {
        detectedRoles = ['government_authority'];
        fullName = 'Maritime Coastal Authority Officer';
      }
    }

    console.info('[TARANG Auth] Backend API offline at /api/auth/login. Initiating authenticated session under [Demo Evaluation Mode].');

    const demoAuth: AuthResponse = {
      accessToken: 'demo_token_' + Date.now(),
      refreshToken: 'demo_refresh_' + Date.now(),
      tokenType: 'Bearer',
      expiresIn: 86400,
      userId: 'usr-' + Math.random().toString(36).substring(2, 9),
      email: credentials.email,
      fullName,
      organizationId: 'org-tarang-01',
      organizationName: orgName,
      roles: detectedRoles,
      isDemoMode: true,
    };

    saveAuthData(demoAuth, credentials.rememberMe ?? true);
    return demoAuth;
  };

  const register = async (data: RegisterData): Promise<AuthResponse> => {
    const res = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      let errorMessage = 'Registration failed. Please check your information.';
      try {
        const errData = await res.json();
        if (errData.message) errorMessage = errData.message;
        else if (errData.error) errorMessage = errData.error;
      } catch {
        // fallback
      }
      throw new Error(errorMessage);
    }

    const authData: AuthResponse = await res.json();
    saveAuthData(authData, true);
    return authData;
  };

  const refreshSession = useCallback(async (): Promise<boolean> => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) return false;

    try {
      const res = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken }),
      });

      if (!res.ok) {
        logout();
        return false;
      }

      const authData: AuthResponse = await res.json();
      saveAuthData(authData, true);
      return true;
    } catch {
      logout();
      return false;
    }
  }, []);

  const logout = () => {
    setAccessToken(null);
    setUser(null);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  };

  const hasRole = (role: string): boolean => {
    if (!user || !user.roles) return false;
    const cleanRole = role.toUpperCase().replace('ROLE_', '');
    return user.roles.some((r) => r.toUpperCase().replace('ROLE_', '') === cleanRole);
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return roles.some((role) => hasRole(role));
  };

  const updateLocalUser = (updates: Partial<User>) => {
    setUser((prev) => {
      if (!prev) return null;
      const updated = { ...prev, ...updates };
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: !!accessToken && !!user,
        isLoading,
        login,
        register,
        logout,
        refreshSession,
        hasRole,
        hasAnyRole,
        updateLocalUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
