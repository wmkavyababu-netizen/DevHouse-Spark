import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';

// Public Pages
import { LandingPage } from './pages/public/LandingPage';
import { AboutPage } from './pages/public/AboutPage';
import { HowItWorksPage } from './pages/public/HowItWorksPage';
import { TechnologyPage } from './pages/public/TechnologyPage';
import { RequestAccessPage } from './pages/public/RequestAccessPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { PublicMapPage } from './pages/public/PublicMapPage';

// Protected Operational Pages
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { SonarWorkspacePage } from './pages/sonar/SonarWorkspacePage';
import { SurveyUploadPage } from './pages/surveys/SurveyUploadPage';
import { ReviewQueuePage } from './pages/review/ReviewQueuePage';
import { GeospatialMapPage } from './pages/map/GeospatialMapPage';
import { TargetsPage } from './pages/targets/TargetsPage';
import { MissionsPage } from './pages/missions/MissionsPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { AdminRetrainingPage } from './pages/admin/AdminRetrainingPage';
import { ProfilePage } from './pages/dashboard/ProfilePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Website Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="/technology" element={<TechnologyPage />} />
          <Route path="/request-access" element={<RequestAccessPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/public/map" element={<PublicMapPage />} />

          {/* Protected Operational Role-Based Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/workspace"
            element={
              <ProtectedRoute allowedRoles={['survey_operator', 'admin']}>
                <SonarWorkspacePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/surveys"
            element={
              <ProtectedRoute allowedRoles={['survey_operator', 'admin']}>
                <SurveyUploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute allowedRoles={['marine_expert', 'admin']}>
                <ReviewQueuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/map"
            element={
              <ProtectedRoute allowedRoles={['survey_operator', 'marine_expert', 'cleanup_organization', 'government_authority', 'admin']}>
                <GeospatialMapPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/targets"
            element={
              <ProtectedRoute allowedRoles={['survey_operator', 'marine_expert', 'cleanup_organization', 'government_authority', 'admin']}>
                <TargetsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/missions"
            element={
              <ProtectedRoute allowedRoles={['cleanup_organization', 'admin']}>
                <MissionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute allowedRoles={['government_authority', 'marine_expert', 'admin']}>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminRetrainingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          {/* Fallback Redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
