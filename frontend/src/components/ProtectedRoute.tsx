/**
 * ProtectedRoute Component
 *
 * Role-based access control wrapper for routes
 * Handles authentication and authorization
 */

import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { PageLoading } from '../components/ui/Loading'
import { UserRole } from '../types'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: UserRole[]
  requireAuth?: boolean
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  requireAuth = true
}) => {
  const location = useLocation()
  const { isAuthenticated, isLoading, user, checkAuth } = useAuthStore()

  // Check authentication status on mount
  useEffect(() => {
    if (!user && isAuthenticated) {
      checkAuth()
    }
  }, [user, isAuthenticated, checkAuth])

  // Show loading while checking authentication
  if (isLoading) {
    return <PageLoading message="Verifying authentication..." />
  }

  // Redirect to login if authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />
  }

  // Check role-based access if allowedRoles is specified
  if (allowedRoles && allowedRoles.length > 0) {
    if (!user) {
      return <Navigate to="/auth/login" state={{ from: location }} replace />
    }

    // Check if user's role is in the allowed roles
    if (!allowedRoles.includes(user.role)) {
      // Redirect to appropriate dashboard based on actual role
      const redirectPath = getRoleBasedRedirect(user.role)
      return <Navigate to={redirectPath} replace />
    }
  }

  return <>{children}</>
}

/**
 * Get redirect path based on user role
 */
function getRoleBasedRedirect(role: UserRole): string {
  switch (role) {
    case UserRole.STUDENT:
      return '/student/dashboard'
    case UserRole.TEACHER:
      return '/teacher/dashboard'
    case UserRole.ADMIN:
      return '/admin/dashboard'
    case UserRole.SUPER_ADMIN:
      return '/super-admin/dashboard'
    default:
      return '/'
  }
}

/**
 * Unauthorized Access Page Component
 */
export const UnauthorizedPage: React.FC = () => {
  const { user } = useAuthStore()

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="h-16 w-16 rounded-full bg-vividly-red-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-vividly-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>

        <div>
          <h1 className="text-2xl font-bold text-foreground mb-2">Access Denied</h1>
          <p className="text-muted-foreground">
            You don't have permission to access this page.
          </p>
        </div>

        {user && (
          <div className="p-4 rounded-lg bg-muted">
            <p className="text-sm text-muted-foreground">
              You are logged in as <span className="font-medium">{user.email}</span> (
              {user.role})
            </p>
          </div>
        )}

        <div className="space-y-2">
          <a
            href={user ? getRoleBasedRedirect(user.role) : '/'}
            className="inline-block w-full px-4 py-2 bg-vividly-blue text-white rounded-lg hover:bg-vividly-blue-600 transition-colors"
          >
            Go to Dashboard
          </a>
          <a
            href="/"
            className="inline-block w-full px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
          >
            Go to Home
          </a>
        </div>
      </div>
    </div>
  )
}

export default ProtectedRoute
