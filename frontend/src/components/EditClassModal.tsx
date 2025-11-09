/**
 * EditClassModal Component
 *
 * Modal dialog for editing class details (name, subject, description, grade levels).
 * Uses React Hook Form for validation and React Query for mutations.
 *
 * Features:
 * - Form validation with error messages
 * - Optimistic UI updates
 * - Toast notifications on success/error
 * - Keyboard shortcuts (Escape to close)
 * - Mobile responsive design
 * - Accessibility compliant
 */

import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Loader2, Save } from 'lucide-react'
import { teacherApi } from '../api/teacher'
import { useToast } from '../hooks/useToast'
import type { ClassResponse, UpdateClassRequest } from '../types/teacher'

interface EditClassModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean
  /**
   * Callback to close the modal
   */
  onClose: () => void
  /**
   * Current class data to populate form
   */
  classData: ClassResponse
}

interface ClassFormData {
  name: string
  subject: string
  description: string
  grade_levels: number[]
}

/**
 * Grade level options (9-12)
 */
const GRADE_LEVELS = [9, 10, 11, 12]

/**
 * EditClassModal Component
 */
export const EditClassModal: React.FC<EditClassModalProps> = ({
  isOpen,
  onClose,
  classData,
}) => {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<ClassFormData>({
    defaultValues: {
      name: classData.name,
      subject: classData.subject || '',
      description: classData.description || '',
      grade_levels: classData.grade_levels || [],
    },
  })

  const selectedGradeLevels = watch('grade_levels')

  // Update form when classData changes
  useEffect(() => {
    if (isOpen) {
      reset({
        name: classData.name,
        subject: classData.subject || '',
        description: classData.description || '',
        grade_levels: classData.grade_levels || [],
      })
    }
  }, [isOpen, classData, reset])

  // Update class mutation
  const updateClassMutation = useMutation({
    mutationFn: (data: UpdateClassRequest) =>
      teacherApi.patchClass(classData.class_id, data),
    onSuccess: (updatedClass) => {
      toast({
        title: 'Class Updated',
        description: `${updatedClass.name} has been updated successfully.`,
        variant: 'success',
      })

      // Invalidate queries to refetch fresh data
      queryClient.invalidateQueries({ queryKey: ['class', classData.class_id] })
      queryClient.invalidateQueries({ queryKey: ['teacher-dashboard'] })

      onClose()
    },
    onError: (error: any) => {
      toast({
        title: 'Update Failed',
        description: error.response?.data?.detail || 'Failed to update class',
        variant: 'error',
      })
    },
  })

  // Handle form submission
  const onSubmit = (data: ClassFormData) => {
    const updateData: UpdateClassRequest = {
      name: data.name !== classData.name ? data.name : undefined,
      subject: data.subject !== classData.subject ? data.subject : undefined,
      description: data.description !== classData.description ? data.description : undefined,
      grade_levels:
        JSON.stringify(data.grade_levels) !== JSON.stringify(classData.grade_levels)
          ? data.grade_levels
          : undefined,
    }

    // Only send fields that changed
    const hasChanges = Object.values(updateData).some((val) => val !== undefined)

    if (!hasChanges) {
      toast({
        title: 'No Changes',
        description: 'No changes were made to the class.',
        variant: 'info',
      })
      onClose()
      return
    }

    updateClassMutation.mutate(updateData)
  }

  // Handle grade level checkbox change
  const handleGradeLevelChange = (grade: number) => {
    const current = selectedGradeLevels || []
    const updated = current.includes(grade)
      ? current.filter((g) => g !== grade)
      : [...current, grade].sort()
    setValue('grade_levels', updated)
  }

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !updateClassMutation.isPending) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose, updateClassMutation.isPending])

  // Prevent body scroll when modal open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => !updateClassMutation.isPending && onClose()}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-class-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2
            id="edit-class-modal-title"
            className="text-2xl font-semibold text-gray-900"
          >
            Edit Class
          </h2>
          <button
            onClick={onClose}
            disabled={updateClassMutation.isPending}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Class Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Class Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              {...register('name', {
                required: 'Class name is required',
                minLength: {
                  value: 1,
                  message: 'Class name must be at least 1 character',
                },
                maxLength: {
                  value: 255,
                  message: 'Class name must be less than 255 characters',
                },
              })}
              className={`
                w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.name ? 'border-red-500' : 'border-gray-300'}
              `}
              placeholder="e.g., AP Physics 1"
              disabled={updateClassMutation.isPending}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.name.message}
              </p>
            )}
          </div>

          {/* Subject */}
          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
              Subject
            </label>
            <input
              id="subject"
              type="text"
              {...register('subject', {
                maxLength: {
                  value: 100,
                  message: 'Subject must be less than 100 characters',
                },
              })}
              className={`
                w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.subject ? 'border-red-500' : 'border-gray-300'}
              `}
              placeholder="e.g., Physics"
              disabled={updateClassMutation.isPending}
            />
            {errors.subject && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.subject.message}
              </p>
            )}
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Description
            </label>
            <textarea
              id="description"
              {...register('description')}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Describe what students will learn in this class..."
              disabled={updateClassMutation.isPending}
            />
          </div>

          {/* Grade Levels */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Grade Levels
            </label>
            <div className="flex gap-4">
              {GRADE_LEVELS.map((grade) => (
                <label
                  key={grade}
                  className="flex items-center gap-2 cursor-pointer select-none"
                >
                  <input
                    type="checkbox"
                    checked={selectedGradeLevels?.includes(grade) || false}
                    onChange={() => handleGradeLevelChange(grade)}
                    disabled={updateClassMutation.isPending}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-700">Grade {grade}</span>
                </label>
              ))}
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Select one or more grade levels for this class
            </p>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={updateClassMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateClassMutation.isPending}
              className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {updateClassMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
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

export default EditClassModal
