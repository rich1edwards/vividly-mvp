/**
 * Login Page
 *
 * User authentication login page
 */

import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card'
import { useToast } from '../hooks/useToast'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login, isAuthenticated, isLoading, error: authError, user } = useAuthStore()
  const { error: showError, success } = useToast()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})

  // Redirect if already authenticated
  useEffect(() => {
    console.log('[Login] useEffect triggered', {
      isAuthenticated,
      user: user ? { id: user.user_id, email: user.email, role: user.role } : null
    })

    if (isAuthenticated && user) {
      console.log('[Login] User is authenticated, redirecting based on role:', user.role)
      // Redirect based on role
      switch (user.role) {
        case 'student':
          console.log('[Login] Navigating to /student/dashboard')
          navigate('/student/dashboard')
          break
        case 'teacher':
          console.log('[Login] Navigating to /teacher/dashboard')
          navigate('/teacher/dashboard')
          break
        case 'admin':
          // Organization Admin - access to their org only
          console.log('[Login] Navigating to /admin/dashboard')
          navigate('/admin/dashboard')
          break
        case 'super_admin':
          // Vividly Platform Admin - full system access
          console.log('[Login] Navigating to /super-admin/dashboard')
          navigate('/super-admin/dashboard')
          break
        default:
          console.log('[Login] Navigating to /')
          navigate('/')
      }
    } else {
      console.log('[Login] User not authenticated, staying on login page')
    }
  }, [isAuthenticated, user, navigate])

  const validateForm = (): boolean => {
    const newErrors: { email?: string; password?: string } = {}

    if (!email) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid'
    }

    if (!password) {
      newErrors.password = 'Password is required'
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      await login({ email, password })
      success('Login successful', 'Welcome back to Vividly!')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed. Please try again.'
      showError('Login failed', errorMessage)
    }
  }

  // Test user quick login (only in development mode)
  const quickLogin = async (testEmail: string, testPassword: string, roleName: string) => {
    setEmail(testEmail)
    setPassword(testPassword)
    // Auto-submit after state updates
    setTimeout(async () => {
      try {
        await login({ email: testEmail, password: testPassword })
        success('Test login successful', `Logged in as ${roleName}`)
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 'Test login failed.'
        showError('Test login failed', errorMessage)
      }
    }, 100)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-vividly-blue-50 via-vividly-purple-50 to-vividly-coral-50 p-4">
      <Card variant="elevated" padding="none" className="w-full max-w-md">
        <CardHeader className="p-6 pb-4">
          <div className="flex justify-center mb-4">
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-vividly-blue to-vividly-purple flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
          </div>
          <CardTitle className="text-center text-2xl">Welcome to Vividly</CardTitle>
          <CardDescription className="text-center">
            Sign in to your account to continue
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 pt-0">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="student@school.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              disabled={isLoading}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                  />
                </svg>
              }
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              disabled={isLoading}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              }
            />

            {authError && (
              <div className="p-3 rounded-lg bg-vividly-red-50 border border-vividly-red-200">
                <p className="text-sm text-vividly-red-700">{authError}</p>
              </div>
            )}

            <Button type="submit" variant="primary" fullWidth isLoading={isLoading}>
              Sign In
            </Button>
          </form>
        </CardContent>

        <CardFooter className="p-6 pt-0 flex-col gap-4">
          <div className="text-center text-sm">
            <Link
              to="/auth/forgot-password"
              className="text-vividly-blue hover:text-vividly-blue-700 font-medium"
            >
              Forgot your password?
            </Link>
          </div>

          <div className="relative w-full">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">Or</span>
            </div>
          </div>

          {/* Test User Quick Login (Development Mode Only) */}
          {import.meta.env.MODE === 'development' && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-xs font-semibold text-yellow-800 mb-3 flex items-center gap-1">
                <span>🧪</span>
                <span>Test Mode - Quick Login</span>
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant="tertiary"
                  size="sm"
                  onClick={() => quickLogin('student@vividly-test.com', 'Test123!Student', 'Student')}
                  disabled={isLoading}
                >
                  Student
                </Button>
                <Button
                  type="button"
                  variant="tertiary"
                  size="sm"
                  onClick={() => quickLogin('teacher@vividly-test.com', 'Test123!Teacher', 'Teacher')}
                  disabled={isLoading}
                >
                  Teacher
                </Button>
                <Button
                  type="button"
                  variant="tertiary"
                  size="sm"
                  onClick={() => quickLogin('admin@vividly-test.com', 'Test123!Admin', 'Admin')}
                  disabled={isLoading}
                >
                  Admin
                </Button>
                <Button
                  type="button"
                  variant="tertiary"
                  size="sm"
                  onClick={() => quickLogin('superadmin@vividly-test.com', 'Test123!SuperAdmin', 'Super Admin')}
                  disabled={isLoading}
                >
                  Super Admin
                </Button>
              </div>
            </div>
          )}

          <div className="text-center text-sm">
            <span className="text-muted-foreground">Don't have an account? </span>
            <Link
              to="/auth/register"
              className="text-vividly-blue hover:text-vividly-blue-700 font-medium"
            >
              Sign up
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}

export default LoginPage
