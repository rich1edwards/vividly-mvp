/**
 * Main App Component
 *
 * Application entry point with routing
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastProvider, ToastViewport } from './components/ui/Toast'
import { useToast } from './hooks/useToast'
import { Toast, ToastTitle, ToastDescription, ToastClose } from './components/ui/Toast'
import ProtectedRoute, { UnauthorizedPage } from './components/ProtectedRoute'
import { UserRole } from './types'

// Auth Pages
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'

// Student Pages
import StudentDashboard from './pages/student/StudentDashboard'
import StudentProfile from './pages/student/StudentProfile'
import ContentRequestPage from './pages/student/ContentRequestPage'
import StudentVideosPage from './pages/student/StudentVideosPage'
import VideoPlayerPage from './pages/student/VideoPlayerPage'

// Teacher Pages
import TeacherDashboard from './pages/TeacherDashboard'
import TeacherClassesPage from './pages/teacher/TeacherClassesPage'

// Admin Pages
import AdminDashboard from './pages/AdminDashboard'

// Super Admin Pages
import SuperAdminDashboard from './pages/SuperAdminDashboard'
import RequestMonitoring from './pages/super-admin/RequestMonitoring'

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
    <BrowserRouter>
      <ToastContainer />
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

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
