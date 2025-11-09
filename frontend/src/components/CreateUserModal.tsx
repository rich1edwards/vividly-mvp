/**
 * Create User Modal (Phase 3.2)
 *
 * Modal form for creating new users
 * Features:
 * - React Hook Form validation
 * - Role-specific fields (grade level for students, subjects for teachers)
 * - Email invitation option
 * - School and organization assignment
 * - Real-time validation feedback
 * - Accessible form design (WCAG AA)
 */

import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { X, UserPlus, Mail, AlertCircle } from 'lucide-react'
import { adminApi, UserCreate, UserResponse } from '../api/admin'
import { useToast } from '../hooks/useToast'

interface CreateUserModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (user: UserResponse) => void
}

interface FormData extends UserCreate {
  // Form-specific fields
}

/**
 * CreateUserModal Component
 */
export const CreateUserModal: React.FC<CreateUserModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      send_invitation: true,
      role: 'student',
    },
  })

  // Watch role to conditionally show fields
  const selectedRole = watch('role')

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      reset()
    }
  }, [isOpen, reset])

  // Create user mutation
  const createUserMutation = useMutation({
    mutationFn: (data: UserCreate) => adminApi.createUser(data),
    onSuccess: (user) => {
      onSuccess(user)
      reset()
    },
    onError: (error: any) => {
      toast({
        title: 'Creation Failed',
        description: error.response?.data?.detail || 'Failed to create user',
        variant: 'error',
      })
    },
  })

  // Handle form submission
  const onSubmit = (data: FormData) => {
    createUserMutation.mutate(data)
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-user-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <UserPlus className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 id="create-user-modal-title" className="text-xl font-semibold text-gray-900">
                Create New User
              </h2>
              <p className="text-sm text-gray-600">Add a new user to the system</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* First Name */}
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
                  First Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="first_name"
                  type="text"
                  {...register('first_name', {
                    required: 'First name is required',
                    minLength: { value: 1, message: 'First name is required' },
                    maxLength: { value: 100, message: 'First name is too long' },
                  })}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.first_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="John"
                />
                {errors.first_name && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.first_name.message}
                  </p>
                )}
              </div>

              {/* Last Name */}
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="last_name"
                  type="text"
                  {...register('last_name', {
                    required: 'Last name is required',
                    minLength: { value: 1, message: 'Last name is required' },
                    maxLength: { value: 100, message: 'Last name is too long' },
                  })}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.last_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Doe"
                />
                {errors.last_name && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.last_name.message}
                  </p>
                )}
              </div>

              {/* Email */}
              <div className="md:col-span-2">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  id="email"
                  type="email"
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address',
                    },
                  })}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.email ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="john.doe@example.com"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.email.message}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Role and Details */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Role and Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Role */}
              <div>
                <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2">
                  Role <span className="text-red-500">*</span>
                </label>
                <select
                  id="role"
                  {...register('role', { required: 'Role is required' })}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.role ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Admin</option>
                </select>
                {errors.role && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.role.message}
                  </p>
                )}
              </div>

              {/* Grade Level (for students) */}
              {selectedRole === 'student' && (
                <div>
                  <label
                    htmlFor="grade_level"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Grade Level
                  </label>
                  <select
                    id="grade_level"
                    {...register('grade_level', {
                      valueAsNumber: true,
                      validate: (value) => {
                        if (selectedRole === 'student' && value) {
                          return (
                            (value >= 9 && value <= 12) || 'Grade level must be between 9 and 12'
                          )
                        }
                        return true
                      },
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select grade...</option>
                    <option value="9">9th Grade</option>
                    <option value="10">10th Grade</option>
                    <option value="11">11th Grade</option>
                    <option value="12">12th Grade</option>
                  </select>
                  {errors.grade_level && (
                    <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {errors.grade_level.message}
                    </p>
                  )}
                </div>
              )}

              {/* School ID */}
              <div className={selectedRole === 'student' ? '' : 'md:col-span-2'}>
                <label htmlFor="school_id" className="block text-sm font-medium text-gray-700 mb-2">
                  School ID
                </label>
                <input
                  id="school_id"
                  type="text"
                  {...register('school_id')}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="school_hillsboro_hs"
                />
                <p className="mt-1 text-xs text-gray-500">Optional - Assign user to a school</p>
              </div>

              {/* Organization ID */}
              <div className="md:col-span-2">
                <label
                  htmlFor="organization_id"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Organization ID
                </label>
                <input
                  id="organization_id"
                  type="text"
                  {...register('organization_id')}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="org_mnps"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Optional - Assign user to an organization
                </p>
              </div>
            </div>
          </div>

          {/* Invitation Settings */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Invitation Settings</h3>
            <div className="flex items-start gap-3">
              <input
                id="send_invitation"
                type="checkbox"
                {...register('send_invitation')}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <div>
                <label htmlFor="send_invitation" className="font-medium text-gray-900 cursor-pointer">
                  Send welcome email invitation
                </label>
                <p className="text-sm text-gray-600 mt-1">
                  User will receive an email with login instructions and password setup link
                </p>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting || createUserMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || createUserMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {createUserMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Create User
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
