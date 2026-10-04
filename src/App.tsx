import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useSessionExpiry } from './hooks/useSessionExpiry';
import { useAuthStore } from './store/authStore';
import { AppShell } from './components/layout/AppShell';
import { AuthShell } from './components/layout/AuthShell';

const AccessDeniedPage = lazy(() => import('./pages/AccessDeniedPage').then((module) => ({ default: module.AccessDeniedPage })));
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage').then((module) => ({ default: module.AdminUsersPage })));
const AuditLogPage = lazy(() => import('./pages/AuditLogPage').then((module) => ({ default: module.AuditLogPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage').then((module) => ({ default: module.ForgotPasswordPage })));
const HistoryPage = lazy(() => import('./pages/HistoryPage').then((module) => ({ default: module.HistoryPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((module) => ({ default: module.LoginPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage })));
const ProfilePage = lazy(() => import('./pages/ProfilePage').then((module) => ({ default: module.ProfilePage })));
const RequestAccessPage = lazy(() => import('./pages/RequestAccessPage').then((module) => ({ default: module.RequestAccessPage })));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage').then((module) => ({ default: module.ResetPasswordPage })));
const ResultsPage = lazy(() => import('./pages/ResultsPage').then((module) => ({ default: module.ResultsPage })));
const SessionExpiredPage = lazy(() => import('./pages/SessionExpiredPage').then((module) => ({ default: module.SessionExpiredPage })));
const UploadPage = lazy(() => import('./pages/UploadPage').then((module) => ({ default: module.UploadPage })));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}

function RoleGate({ allowedRoles, children }: { allowedRoles: Array<'admin' | 'clinician' | 'technician'>; children: React.ReactNode }) {
  const user = useAuthStore((state) => state.user);
  const location = useLocation();
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/access-denied" replace />;
  }
  return children;
}

function DefaultLanding() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />;
}

export default function App() {
  useSessionExpiry();

  return (
    <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading workspace…</div>}>
      <Routes>
        <Route path="/" element={<DefaultLanding />} />
        <Route element={<AuthShell />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<RequestAccessPage />} />
          <Route path="/request-access" element={<Navigate to="/signup" replace />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/session-expired" element={<SessionExpiredPage />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
        </Route>
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/results/:analysisId" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route
            path="/admin/users"
            element={
              <RoleGate allowedRoles={['admin']}>
                <AdminUsersPage />
              </RoleGate>
            }
          />
          <Route
            path="/audit-log"
            element={
              <RoleGate allowedRoles={['admin', 'clinician', 'technician']}>
                <AuditLogPage />
              </RoleGate>
            }
          />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
