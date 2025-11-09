/**
 * Main App Component (Phase 4.3.1)
 *
 * Application entry point with routing and global providers.
 * Updated: 2025-01-08 - Added lazy loading for all routes (Phase 4.3.1)
 * Updated: 2025-01-08 - Added ErrorBoundary integration
 * Updated: 2025-01-08 - Added Suspense with LoadingFallback
 *
 * Performance Optimizations:
 * - Lazy loading all page components with React.lazy
 * - Code splitting by route for optimal bundle size
 * - Suspense boundaries with loading states
 * - Error boundaries for graceful error handling
 */

import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ToastProvider, ToastViewport } from './components/ui/Toast'
import { useToast } from './hooks/useToast'
import { Toast, ToastTitle, ToastDescription, ToastClose } from './components/ui/Toast'
import ProtectedRoute, { UnauthorizedPage } from './components/ProtectedRoute'
import { UserRole } from './types'
import { queryClient } from './lib/queryClient'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoadingFallback } from './components/LoadingFallback'
import { SkipToContent } from './components/SkipToContent'

// Lazy load all page components for code splitting
// Auth Pages - Load immediately (no lazy) as they're the entry point
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'

// Student Pages - Lazy loaded
const StudentDashboard = lazy(() => import('./pages/student/StudentDashboard'))
const StudentProfile = lazy(() => import('./pages/student/StudentProfile'))
const ContentRequestPage = lazy(() => import('./pages/student/ContentRequestPage'))
const StudentVideosPage = lazy(() => import('./pages/student/StudentVideosPage'))
const VideoPlayerPage = lazy(() => import('./pages/student/VideoPlayerPage'))

// Teacher Pages - Lazy loaded
const TeacherDashboard = lazy(() => import('./pages/TeacherDashboard'))
const TeacherClassesPage = lazy(() => import('./pages/teacher/TeacherClassesPage'))
const TeacherClassDashboard = lazy(() => import('./pages/teacher/TeacherClassDashboard'))
const StudentDetailPage = lazy(() => import('./pages/teacher/StudentDetailPage'))

// Admin Pages - Lazy loaded
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const UserManagement = lazy(() => import('./pages/admin/UserManagement'))

// Super Admin Pages - Lazy loaded
const SuperAdminDashboard = lazy(() => import('./pages/SuperAdminDashboard'))
const RequestMonitoring = lazy(() => import('./pages/super-admin/RequestMonitoring'))
const SystemMetricsDashboard = lazy(() => import('./pages/super-admin/SystemMetricsDashboard'))

// Toast Notifications Container
const ToastContainer: React.FC = () => {
  const { toasts, dismiss } = useToast()

  return (
    <ToastProvider>
      {toasts.map((toast) => (
        <Toast key={toast.id} variant={toast.variant} onOpenChange={() => dismiss(toast.id)}>
          <div className="grid gap-1">
            {toast.title && <ToastTitle>{toast.title}</ToastTitle>}
            {toast.description && <ToastDescription>{toast.description}</ToastDescription>}
          </div>
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SkipToContent />
          <ToastContainer />
          <Suspense fallback={<LoadingFallback message="Loading application..." />}>
            <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Navigate to="/auth/login" replace />} />
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/register" element={<RegisterPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        {/* Student Routes */}
        <Route
          path="/student/dashboard"
          element={
            <ProtectedRoute allowedRoles={[UserRole.STUDENT]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/profile"
          element={
            <ProtectedRoute allowedRoles={[UserRole.STUDENT]}>
              <StudentProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/content/request"
          element={
            <ProtectedRoute allowedRoles={[UserRole.STUDENT]}>
              <ContentRequestPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/videos"
          element={
            <ProtectedRoute allowedRoles={[UserRole.STUDENT]}>
              <StudentVideosPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/videos/:cacheKey"
          element={
            <ProtectedRoute allowedRoles={[UserRole.STUDENT]}>
              <VideoPlayerPage />
            </ProtectedRoute>
          }
        />

        {/* Teacher Routes */}
        <Route
          path="/teacher/dashboard"
          element={
            <ProtectedRoute allowedRoles={[UserRole.TEACHER]}>
              <TeacherDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/classes"
          element={
            <ProtectedRoute allowedRoles={[UserRole.TEACHER]}>
              <TeacherClassesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/class/:classId"
          element={
            <ProtectedRoute allowedRoles={[UserRole.TEACHER]}>
              <TeacherClassDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/student/:studentId"
          element={
            <ProtectedRoute allowedRoles={[UserRole.TEACHER]}>
              <StudentDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/students"
          element={
            <ProtectedRoute allowedRoles={[UserRole.TEACHER]}>
              <div>Students Page (Coming Soon)</div>
            </ProtectedRoute>
          }
        />

        {/* Organization Admin Routes (scoped to their org) */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
              <UserManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/requests"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
              <div>Content Requests Page (Coming Soon)</div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/schools"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
              <div>Schools Management Page (Coming Soon)</div>
            </ProtectedRoute>
          }
        />

        {/* Super Admin Routes (full system access) */}
        <Route
          path="/super-admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={[UserRole.SUPER_ADMIN]}>
              <SuperAdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/super-admin/organizations"
          element={
            <ProtectedRoute allowedRoles={[UserRole.SUPER_ADMIN]}>
              <div>All Organizations Page (Coming Soon)</div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/super-admin/settings"
          element={
            <ProtectedRoute allowedRoles={[UserRole.SUPER_ADMIN]}>
              <div>System Settings Page (Coming Soon)</div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/super-admin/monitoring"
          element={
            <ProtectedRoute allowedRoles={[UserRole.SUPER_ADMIN]}>
              <RequestMonitoring />
            </ProtectedRoute>
          }
        />
        <Route
          path="/super-admin/metrics"
          element={
            <ProtectedRoute allowedRoles={[UserRole.SUPER_ADMIN]}>
              <SystemMetricsDashboard />
            </ProtectedRoute>
          }
        />

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
        {/* React Query DevTools - only in development */}
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
