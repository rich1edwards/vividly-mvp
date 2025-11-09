/**
 * Student Detail Page (Phase 2.3.1)
 *
 * Comprehensive student detail view for teachers
 * Features:
 * - Student header with profile info and interests
 * - Metric cards (content requests, videos watched, avg watch time, favorite topics)
 * - Activity timeline with infinite scroll
 * - Student video library
 * - Quick actions (Request Content for Student)
 * - Real-time updates via WebSocket notifications
 */

import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  BookOpen,
  Clock,
  FileText,
  Heart,
  Mail,
  RefreshCw,
  Sparkles,
  User,
  Video,
} from 'lucide-react'
import { teacherApi } from '../../api/teacher'
import { useNotifications } from '../../hooks/useNotifications'
import { StatsCard } from '../../components/StatsCard'
import { ActivityTimeline } from '../../components/ActivityTimeline'
import type { StudentDetail } from '../../types/teacher'

/**
 * Format seconds to readable time (e.g., "5m 30s", "1h 15m")
 */
const formatWatchTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
  }
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
}

/**
 * StudentDetailPage Component
 */
export const StudentDetailPage: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>()
  const navigate = useNavigate()
  const { notifications } = useNotifications()
  const [activeTab, setActiveTab] = useState<'timeline' | 'library'>('timeline')

  // Fetch student details
  const {
    data: studentData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['student-detail', studentId],
    queryFn: () => teacherApi.getStudentDetail(studentId!),
    enabled: !!studentId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  // Real-time updates: Monitor notifications for student activity
  React.useEffect(() => {
    if (!studentId || notifications.length === 0) return

    const latestNotification = notifications[0]

    // Check if notification relates to this student
    if (
      latestNotification.metadata?.student_id === studentId ||
      latestNotification.metadata?.user_id === studentId
    ) {
      refetch()
    }
  }, [notifications, studentId, refetch])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading student details...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !studentData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load student details</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const student = studentData

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Back button */}
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </button>

          {/* Student Header */}
          <div className="flex items-start gap-6">
            {/* Profile Picture */}
            <div className="flex-shrink-0">
              {student.profile_picture ? (
                <img
                  src={student.profile_picture}
                  alt={`${student.first_name} ${student.last_name}`}
                  className="w-24 h-24 rounded-full object-cover border-4 border-blue-100"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center border-4 border-blue-100">
                  <User className="w-12 h-12 text-white" />
                </div>
              )}
            </div>

            {/* Student Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">
                {student.first_name} {student.last_name}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-600">
                <span className="flex items-center">
                  <Mail className="w-4 h-4 mr-1" />
                  {student.email}
                </span>
                {student.grade_level && (
                  <span className="flex items-center">
                    <BookOpen className="w-4 h-4 mr-1" />
                    Grade {student.grade_level}
                  </span>
                )}
                <span className="flex items-center">
                  Joined {new Date(student.joined_at).toLocaleDateString()}
                </span>
              </div>

              {/* Interests */}
              {student.interests.length > 0 && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Heart className="w-4 h-4 text-pink-500" />
                    <span className="text-sm font-medium text-gray-700">Interests</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {student.interests.map((interest, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-pink-50 text-pink-700 text-sm rounded-full border border-pink-200"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Classes */}
              {student.classes.length > 0 && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <BookOpen className="w-4 h-4 text-blue-500" />
                    <span className="text-sm font-medium text-gray-700">Enrolled Classes</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {student.classes.map((cls) => (
                      <button
                        key={cls.class_id}
                        onClick={() => navigate(`/teacher/class/${cls.class_id}`)}
                        className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-lg border border-blue-200 hover:bg-blue-100 transition-colors"
                      >
                        {cls.class_name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col gap-2">
              <button
                onClick={() => {
                  // TODO: Implement request content for student modal (Phase 2.4)
                  console.log('Request content for student:', studentId)
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 whitespace-nowrap"
              >
                <Sparkles className="w-4 h-4" />
                Request Content
              </button>
              <button
                onClick={() => refetch()}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Content Requests"
            value={student.metrics.content_requests.toString()}
            icon={FileText}
            trend={
              student.metrics.content_requests > 0
                ? {
                    value: student.metrics.content_requests,
                    direction: 'up' as const,
                    label: 'total',
                  }
                : undefined
            }
          />
          <StatsCard
            title="Videos Watched"
            value={student.metrics.videos_watched.toString()}
            icon={Video}
            trend={
              student.metrics.videos_watched > 0
                ? {
                    value: student.metrics.videos_watched,
                    direction: 'up' as const,
                    label: 'completed',
                  }
                : undefined
            }
          />
          <StatsCard
            title="Avg Watch Time"
            value={formatWatchTime(student.metrics.avg_watch_time)}
            icon={Clock}
            trend={
              student.metrics.avg_watch_time > 0
                ? {
                    value: Math.round(student.metrics.avg_watch_time / 60),
                    direction: 'neutral' as const,
                    label: 'minutes',
                  }
                : undefined
            }
          />
          <StatsCard
            title="Favorite Topics"
            value={student.metrics.favorite_topics.length.toString()}
            icon={Heart}
            subtitle={
              student.metrics.favorite_topics.length > 0
                ? student.metrics.favorite_topics.slice(0, 2).join(', ')
                : 'No favorites yet'
            }
          />
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('timeline')}
                className={`
                  flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm
                  ${
                    activeTab === 'timeline'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }
                `}
              >
                <Clock className="w-4 h-4" />
                Activity Timeline
              </button>
              <button
                onClick={() => setActiveTab('library')}
                className={`
                  flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm
                  ${
                    activeTab === 'library'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }
                `}
              >
                <Video className="w-4 h-4" />
                Video Library
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'timeline' && (
              <ActivityTimeline
                activities={student.activity_timeline}
                studentName={`${student.first_name} ${student.last_name}`}
              />
            )}
            {activeTab === 'library' && (
              <div className="text-center py-12 text-gray-500">
                <Video className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="font-medium mb-2">Video Library</p>
                <p className="text-sm">
                  Video library view coming in next iteration
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default StudentDetailPage
