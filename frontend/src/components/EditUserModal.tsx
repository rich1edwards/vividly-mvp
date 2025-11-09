/**
 * Edit User Modal (Phase 3.2)
 *
 * Modal form for editing existing users
 * Features:
 * - React Hook Form with pre-filled data
 * - Role changes with validation
 * - Grade level and subject updates
 * - Real-time validation feedback
 * - Accessible form design (WCAG AA)
 */

import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { X, Edit, AlertCircle } from 'lucide-react'
import { adminApi, UserUpdate, UserResponse } from '../api/admin'
import { useToast } from '../hooks/useToast'

interface EditUserModalProps {
  isOpen: boolean
  onClose: () => void
  user: UserResponse
  onSuccess: (user: UserResponse) => void
}

interface FormData extends UserUpdate {
  // Form-specific fields
}

/**
 * EditUserModal Component
 */
export const EditUserModal: React.FC<EditUserModalProps> = ({
  isOpen,
  onClose,
  user,
  onSuccess,
}) => {
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<FormData>({
    defaultValues: {
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role as 'student' | 'teacher' | 'admin',
      grade_level: user.grade_level,
      subjects: [],
    },
  })

  // Watch role to conditionally show fields
  const selectedRole = watch('role')

  // Reset form when user changes
  useEffect(() => {
    if (isOpen && user) {
      reset({
        first_name: user.first_name,
        last_name: user.last_name,
        role: user.role as 'student' | 'teacher' | 'admin',
        grade_level: user.grade_level,
        subjects: [],
      })
    }
  }, [isOpen, user, reset])

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: (data: UserUpdate) => adminApi.updateUser(user.user_id, data),
    onSuccess: (updatedUser) => {
      onSuccess(updatedUser)
      reset()
    },
    onError: (error: any) => {
      toast({
        title: 'Update Failed',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'error',
      })
    },
  })

  // Handle form submission
  const onSubmit = (data: FormData) => {
    // Only send fields that were actually changed
    const changedData: UserUpdate = {}

    if (data.first_name !== user.first_name) {
      changedData.first_name = data.first_name
    }
    if (data.last_name !== user.last_name) {
      changedData.last_name = data.last_name
    }
    if (data.role !== user.role) {
      changedData.role = data.role
    }
    if (data.grade_level !== user.grade_level) {
      changedData.grade_level = data.grade_level
    }
    if (data.subjects && data.subjects.length > 0) {
      changedData.subjects = data.subjects
    }

    updateUserMutation.mutate(changedData)
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-user-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Edit className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 id="edit-user-modal-title" className="text-xl font-semibold text-gray-900">
                Edit User
              </h2>
              <p className="text-sm text-gray-600">
                Update details for {user.first_name} {user.last_name}
              </p>
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
          {/* User Info (Read-only) */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Email:</span>
                <span className="ml-2 font-medium text-gray-900">{user.email}</span>
              </div>
              <div>
                <span className="text-gray-600">User ID:</span>
                <span className="ml-2 font-mono text-xs text-gray-900">{user.user_id}</span>
              </div>
              <div>
                <span className="text-gray-600">Created:</span>
                <span className="ml-2 text-gray-900">
                  {new Date(user.created_at).toLocaleDateString()}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Status:</span>
                <span
                  className={`ml-2 font-medium ${
                    user.is_active ? 'text-green-600' : 'text-gray-600'
                  }`}
                >
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>

          {/* Editable Information */}
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
                />
                {errors.last_name && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.last_name.message}
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
                {selectedRole !== user.role && (
                  <p className="mt-1 text-sm text-amber-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    Warning: Changing role will affect user permissions
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
            </div>
          </div>

          {/* Change Warning */}
          {isDirty && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Changes will take effect immediately. The user may need to log
                out and back in to see updated permissions.
              </p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting || updateUserMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || updateUserMutation.isPending || !isDirty}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {updateUserMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Edit className="w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
