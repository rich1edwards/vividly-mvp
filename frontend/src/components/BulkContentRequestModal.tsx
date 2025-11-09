/**
 * BulkContentRequestModal Component (Phase 2.4.1)
 *
 * Modal for teachers to request content for multiple students at once
 * Features:
 * - Student multi-select with search and filtering
 * - Content request form (query, topic, subject)
 * - Scheduling options (generate now or schedule for later)
 * - Notification toggle
 * - Progress indicator during submission
 * - Success/failure summary with detailed results
 * - Form validation
 * - Interest-based filtering
 */

import React, { useState, useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import {
  X,
  Users,
  Search,
  CheckSquare,
  Square,
  Loader2,
  Send,
  Calendar,
  Bell,
  BellOff,
  Sparkles,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { teacherApi } from '../api/teacher'
import { useToast } from '../hooks/useToast'
import type {
  StudentInRoster,
  BulkContentRequest,
  BulkContentRequestResponse,
} from '../types/teacher'

interface BulkContentRequestModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean
  /**
   * Callback to close the modal
   */
  onClose: () => void
  /**
   * Class ID for the bulk request
   */
  classId: string
  /**
   * Available students to select from
   */
  students: StudentInRoster[]
  /**
   * Pre-selected student IDs (optional)
   */
  preSelectedStudentIds?: string[]
  /**
   * Callback when request completes successfully
   */
  onSuccess?: (response: BulkContentRequestResponse) => void
}

interface FormData {
  query: string
  topic: string
  subject: string
  generateNow: boolean
  scheduledFor: string
  notifyStudents: boolean
}

/**
 * BulkContentRequestModal Component
 */
export const BulkContentRequestModal: React.FC<BulkContentRequestModalProps> = ({
  isOpen,
  onClose,
  classId,
  students,
  preSelectedStudentIds = [],
  onSuccess,
}) => {
  const { toast } = useToast()
  const [selectedStudentIds, setSelectedStudentIds] = useState<Set<string>>(
    new Set(preSelectedStudentIds)
  )
  const [searchQuery, setSearchQuery] = useState('')
  const [filterByInterest, setFilterByInterest] = useState('')
  const [showResults, setShowResults] = useState(false)
  const [requestResponse, setRequestResponse] = useState<BulkContentRequestResponse | null>(
    null
  )

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<FormData>({
    defaultValues: {
      query: '',
      topic: '',
      subject: '',
      generateNow: true,
      scheduledFor: '',
      notifyStudents: true,
    },
  })

  const generateNow = watch('generateNow')

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedStudentIds(new Set(preSelectedStudentIds))
      setSearchQuery('')
      setFilterByInterest('')
      setShowResults(false)
      setRequestResponse(null)
      reset()
    }
  }, [isOpen, preSelectedStudentIds, reset])

  // Bulk content request mutation
  const bulkRequestMutation = useMutation({
    mutationFn: (data: BulkContentRequest) =>
      teacherApi.bulkContentRequest(classId, data),
    onSuccess: (response) => {
      setRequestResponse(response)
      setShowResults(true)

      if (response.failed === 0) {
        toast({
          title: 'Content Requested Successfully',
          description: `Created ${response.successful} content request${
            response.successful > 1 ? 's' : ''
          } for ${response.successful} student${response.successful > 1 ? 's' : ''}.`,
          variant: 'success',
        })
      } else {
        toast({
          title: 'Partial Success',
          description: `${response.successful} successful, ${response.failed} failed. Check details below.`,
          variant: 'warning',
        })
      }

      if (onSuccess) {
        onSuccess(response)
      }
    },
    onError: (error: any) => {
      toast({
        title: 'Request Failed',
        description: error.response?.data?.detail || 'Failed to create bulk content request',
        variant: 'error',
      })
    },
  })

  // Get all unique interests from students
  const allInterests = useMemo(() => {
    const interestsSet = new Set<string>()
    students.forEach((student) => {
      // Assuming students have interests array in metadata or profile
      // This would come from the backend - for now, return empty array
    })
    return Array.from(interestsSet).sort()
  }, [students])

  // Filter students based on search and interest filter
  const filteredStudents = useMemo(() => {
    return students.filter((student) => {
      const fullName = `${student.first_name} ${student.last_name}`.toLowerCase()
      const email = student.email.toLowerCase()
      const matchesSearch =
        searchQuery === '' ||
        fullName.includes(searchQuery.toLowerCase()) ||
        email.includes(searchQuery.toLowerCase())

      // Interest filtering would go here if available
      const matchesInterest = filterByInterest === '' // || student.interests?.includes(filterByInterest)

      return matchesSearch && matchesInterest
    })
  }, [students, searchQuery, filterByInterest])

  // Toggle student selection
  const toggleStudent = (studentId: string) => {
    const newSelected = new Set(selectedStudentIds)
    if (newSelected.has(studentId)) {
      newSelected.delete(studentId)
    } else {
      if (newSelected.size >= 30) {
        toast({
          title: 'Selection Limit Reached',
          description: 'You can select up to 30 students at once.',
          variant: 'warning',
        })
        return
      }
      newSelected.add(studentId)
    }
    setSelectedStudentIds(newSelected)
  }

  // Select all filtered students
  const selectAll = () => {
    const newSelected = new Set(selectedStudentIds)
    filteredStudents.forEach((student) => {
      if (newSelected.size < 30) {
        newSelected.add(student.user_id)
      }
    })
    setSelectedStudentIds(newSelected)
  }

  // Deselect all students
  const deselectAll = () => {
    setSelectedStudentIds(new Set())
  }

  // Handle form submission
  const onSubmit = (data: FormData) => {
    if (selectedStudentIds.size === 0) {
      toast({
        title: 'No Students Selected',
        description: 'Please select at least one student.',
        variant: 'error',
      })
      return
    }

    const requestData: BulkContentRequest = {
      student_ids: Array.from(selectedStudentIds),
      query: data.query,
      topic: data.topic || undefined,
      subject: data.subject || undefined,
      schedule: {
        generate_now: data.generateNow,
        scheduled_for: data.generateNow ? undefined : data.scheduledFor,
      },
      notify_students: data.notifyStudents,
    }

    bulkRequestMutation.mutate(requestData)
  }

  // Close modal and reset
  const handleClose = () => {
    if (!bulkRequestMutation.isPending) {
      onClose()
    }
  }

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

  // Show results screen
  if (showResults && requestResponse) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={handleClose}
          aria-hidden="true"
        />
        <div
          className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          role="dialog"
          aria-modal="true"
        >
          <div className="p-6">
            {/* Success Header */}
            <div className="flex items-center justify-center mb-6">
              {requestResponse.failed === 0 ? (
                <CheckCircle className="w-16 h-16 text-green-600" />
              ) : (
                <AlertCircle className="w-16 h-16 text-yellow-600" />
              )}
            </div>

            {/* Summary */}
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {requestResponse.failed === 0 ? 'Requests Created!' : 'Partial Success'}
              </h2>
              <p className="text-gray-600">
                {requestResponse.successful} of {requestResponse.total_requests} requests created
                successfully
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">
                  {requestResponse.total_requests}
                </p>
                <p className="text-sm text-gray-600">Total</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {requestResponse.successful}
                </p>
                <p className="text-sm text-gray-600">Successful</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-600">{requestResponse.failed}</p>
                <p className="text-sm text-gray-600">Failed</p>
              </div>
            </div>

            {/* Failures List */}
            {requestResponse.failures && requestResponse.failures.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Failed Requests</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {requestResponse.failures.map((failure, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg"
                    >
                      <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{failure.student_name}</p>
                        <p className="text-sm text-gray-600">{failure.error}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Close Button */}
            <button
              onClick={handleClose}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Main form
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => !bulkRequestMutation.isPending && handleClose()}
        aria-hidden="true"
      />
      <div
        className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-semibold text-gray-900">Bulk Content Request</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={bulkRequestMutation.isPending}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Student Selection */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-gray-700">
                Select Students <span className="text-red-500">*</span>
                <span className="ml-2 text-xs text-gray-500">
                  ({selectedStudentIds.size} / 30 selected)
                </span>
              </label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={selectAll}
                  disabled={filteredStudents.length === 0}
                  className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
                >
                  Select All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  type="button"
                  onClick={deselectAll}
                  disabled={selectedStudentIds.size === 0}
                  className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
                >
                  Deselect All
                </button>
              </div>
            </div>

            {/* Search and Filter */}
            <div className="flex gap-3 mb-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search students..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Student List */}
            <div className="border border-gray-300 rounded-lg max-h-60 overflow-y-auto">
              {filteredStudents.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                  <p>No students found</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {filteredStudents.map((student) => {
                    const isSelected = selectedStudentIds.has(student.user_id)
                    return (
                      <label
                        key={student.user_id}
                        className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer"
                      >
                        <div className="flex-shrink-0">
                          {isSelected ? (
                            <CheckSquare className="w-5 h-5 text-blue-600" />
                          ) : (
                            <Square className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleStudent(student.user_id)}
                          className="sr-only"
                        />
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">
                            {student.first_name} {student.last_name}
                          </p>
                          <p className="text-sm text-gray-500">{student.email}</p>
                        </div>
                        {student.grade_level && (
                          <span className="text-sm text-gray-500">
                            Grade {student.grade_level}
                          </span>
                        )}
                      </label>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Content Query */}
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Content Request <span className="text-red-500">*</span>
            </label>
            <textarea
              id="query"
              {...register('query', {
                required: 'Content request is required',
                minLength: {
                  value: 10,
                  message: 'Request must be at least 10 characters',
                },
              })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Describe what content you want to generate for these students..."
              disabled={bulkRequestMutation.isPending}
            />
            {errors.query && (
              <p className="mt-1 text-sm text-red-600">{errors.query.message}</p>
            )}
          </div>

          {/* Topic and Subject */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
                Topic (Optional)
              </label>
              <input
                id="topic"
                type="text"
                {...register('topic')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Photosynthesis"
                disabled={bulkRequestMutation.isPending}
              />
            </div>
            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
                Subject (Optional)
              </label>
              <input
                id="subject"
                type="text"
                {...register('subject')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Biology"
                disabled={bulkRequestMutation.isPending}
              />
            </div>
          </div>

          {/* Scheduling */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              <Calendar className="inline w-4 h-4 mr-1" />
              Scheduling
            </label>
            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  {...register('generateNow')}
                  value="true"
                  checked={generateNow}
                  className="w-4 h-4 text-blue-600"
                  disabled={bulkRequestMutation.isPending}
                />
                <span className="text-sm text-gray-700">Generate now</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  {...register('generateNow')}
                  value="false"
                  checked={!generateNow}
                  className="w-4 h-4 text-blue-600"
                  disabled={bulkRequestMutation.isPending}
                />
                <span className="text-sm text-gray-700">Schedule for later</span>
              </label>
              {!generateNow && (
                <div className="ml-7">
                  <input
                    type="datetime-local"
                    {...register('scheduledFor', {
                      required: !generateNow ? 'Scheduled date is required' : false,
                    })}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={bulkRequestMutation.isPending}
                  />
                  {errors.scheduledFor && (
                    <p className="mt-1 text-sm text-red-600">{errors.scheduledFor.message}</p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Notifications */}
          <div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('notifyStudents')}
                className="w-4 h-4 text-blue-600 rounded"
                disabled={bulkRequestMutation.isPending}
              />
              <span className="text-sm font-medium text-gray-700">
                {watch('notifyStudents') ? (
                  <>
                    <Bell className="inline w-4 h-4 mr-1 text-blue-600" />
                    Notify students when content is ready
                  </>
                ) : (
                  <>
                    <BellOff className="inline w-4 h-4 mr-1 text-gray-400" />
                    Don't notify students
                  </>
                )}
              </span>
            </label>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              disabled={bulkRequestMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={bulkRequestMutation.isPending || selectedStudentIds.size === 0}
              className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {bulkRequestMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating Requests...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Create Requests ({selectedStudentIds.size})
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default BulkContentRequestModal
