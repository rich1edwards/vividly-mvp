/**
 * Register Page
 *
 * User registration page with role selection
 */

import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '../components/ui/Card'
import { useToast } from '../hooks/useToast'
import { UserRole } from '../types'

const ROLE_OPTIONS = [
  {
    value: UserRole.STUDENT,
    label: 'Student',
    description: 'I want to learn with personalized video content',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
        />
      </svg>
    )
  },
  {
    value: UserRole.TEACHER,
    label: 'Teacher',
    description: 'I want to manage classes and track student progress',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />
      </svg>
    )
  }
]

const GRADE_LEVELS = Array.from({ length: 8 }, (_, i) => ({
  value: i + 6,
  label: `Grade ${i + 6}`
}))

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register, isAuthenticated, isLoading, user } = useAuthStore()
  const { error: showError, success } = useToast()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    role: UserRole.STUDENT,
    gradeLevel: 9
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      switch (user.role) {
        case 'student':
          navigate('/student/dashboard')
          break
        case 'teacher':
          navigate('/teacher/dashboard')
          break
        case 'admin':
          navigate('/admin/dashboard')
          break
        case 'super_admin':
          navigate('/super-admin/dashboard')
          break
        default:
          navigate('/')
      }
    }
  }, [isAuthenticated, user, navigate])

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number'
    }

    // Confirm password
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    // Name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required'
    }
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required'
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
      await register({
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
        role: formData.role,
        grade_level: formData.role === UserRole.STUDENT ? formData.gradeLevel : undefined
      })
      success('Registration successful', 'Welcome to Vividly!')
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || 'Registration failed. Please try again.'
      showError('Registration failed', errorMessage)
    }
  }

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-vividly-blue-50 via-vividly-purple-50 to-vividly-coral-50 p-4">
      <Card variant="elevated" padding="none" className="w-full max-w-2xl">
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
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                />
              </svg>
            </div>
          </div>
          <CardTitle className="text-center text-2xl">Join Vividly</CardTitle>
          <CardDescription className="text-center">
            Create your account to start your learning journey
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 pt-0">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Role Selection */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">
                I am a...
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {ROLE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateFormData('role', option.value)}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.role === option.value
                        ? 'border-vividly-blue bg-vividly-blue-50'
                        : 'border-border hover:border-vividly-blue-200'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`flex-shrink-0 ${
                          formData.role === option.value
                            ? 'text-vividly-blue'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {option.icon}
                      </div>
                      <div>
                        <div className="font-medium">{option.label}</div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {option.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Personal Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="First Name"
                type="text"
                placeholder="Alex"
                value={formData.firstName}
                onChange={(e) => updateFormData('firstName', e.target.value)}
                error={errors.firstName}
                disabled={isLoading}
              />

              <Input
                label="Last Name"
                type="text"
                placeholder="Chen"
                value={formData.lastName}
                onChange={(e) => updateFormData('lastName', e.target.value)}
                error={errors.lastName}
                disabled={isLoading}
              />
            </div>

            {/* Grade Level (Students only) */}
            {formData.role === UserRole.STUDENT && (
              <div className="space-y-1">
                <label className="block text-sm font-medium text-foreground">
                  Grade Level
                </label>
                <select
                  value={formData.gradeLevel}
                  onChange={(e) => updateFormData('gradeLevel', parseInt(e.target.value))}
                  className="flex w-full rounded-lg border border-input bg-background px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
                  disabled={isLoading}
                >
                  {GRADE_LEVELS.map((grade) => (
                    <option key={grade.value} value={grade.value}>
                      {grade.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Email */}
            <Input
              label="Email"
              type="email"
              placeholder="alex@school.edu"
              value={formData.email}
              onChange={(e) => updateFormData('email', e.target.value)}
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

            {/* Password */}
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => updateFormData('password', e.target.value)}
              error={errors.password}
              helperText="Must be 8+ characters with uppercase, lowercase, and number"
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

            {/* Confirm Password */}
            <Input
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={(e) => updateFormData('confirmPassword', e.target.value)}
              error={errors.confirmPassword}
              disabled={isLoading}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              }
            />

            <Button type="submit" variant="primary" fullWidth isLoading={isLoading}>
              Create Account
            </Button>
          </form>
        </CardContent>

        <CardFooter className="p-6 pt-0">
          <div className="text-center text-sm w-full">
            <span className="text-muted-foreground">Already have an account? </span>
            <Link
              to="/auth/login"
              className="text-vividly-blue hover:text-vividly-blue-700 font-medium"
            >
              Sign in
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}

export default RegisterPage
