/**
 * Teacher Class Dashboard Page (Phase 2.2)
 *
 * Main dashboard for teachers to view and manage a specific class.
 * Features:
 * - Class header with quick actions (edit, archive)
 * - Metric cards (students, requests, completion, active)
 * - Tab navigation (students, requests, library, analytics)
 * - Real-time updates via WebSocket notifications
 * - Responsive design for desktop and mobile
 *
 * Uses:
 * - StatsCard component (Phase 2.1)
 * - DataTable component (Phase 2.1)
 * - React Query for server state management
 * - useNotifications for real-time updates
 */

import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  Users,
  FileText,
  TrendingUp,
  Archive,
  Edit,
  ArrowLeft,
  RefreshCw,
} from 'lucide-react'
import { teacherApi } from '../../api/teacher'
import { useNotifications } from '../../hooks/useNotifications'
import { useToast } from '../../hooks/useToast'
import { StatsCard } from '../../components/StatsCard'
import { EditClassModal } from '../../components/EditClassModal'
import { StudentRosterTable } from '../../components/StudentRosterTable'
import { BulkContentRequestModal } from '../../components/BulkContentRequestModal'

/**
 * Tab navigation options
 */
type TabType = 'students' | 'requests' | 'library' | 'analytics'

interface Tab {
  id: TabType
  label: string
  icon: React.ElementType
  badge?: number
  disabled?: boolean
}

/**
 * Teacher Class Dashboard Component
 */
export const TeacherClassDashboard: React.FC = () => {
  const { classId } = useParams<{ classId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { notifications } = useNotifications()

  const [activeTab, setActiveTab] = useState<TabType>('students')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isBulkRequestModalOpen, setIsBulkRequestModalOpen] = useState(false)
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([])

  // Fetch class details
  const {
    data: classData,
    isLoading: classLoading,
    error: classError,
  } = useQuery({
    queryKey: ['class', classId],
    queryFn: () => teacherApi.getClass(classId!),
    enabled: !!classId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Fetch class roster (for metrics)
  const {
    data: rosterData,
    isLoading: rosterLoading,
    refetch: refetchRoster,
  } = useQuery({
    queryKey: ['class-roster', classId],
    queryFn: () => teacherApi.getRoster(classId!),
    enabled: !!classId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  // Archive class mutation
  const archiveClassMutation = useMutation({
    mutationFn: () => teacherApi.archiveClass(classId!),
    onSuccess: (data) => {
      toast({
        title: 'Class Archived',
        description: `${data.name} has been archived successfully.`,
        variant: 'success',
      })
      navigate('/teacher/classes')
    },
    onError: (error: any) => {
      toast({
        title: 'Archive Failed',
        description: error.response?.data?.detail || 'Failed to archive class',
        variant: 'error',
      })
    },
  })

  // Real-time updates: Monitor notifications and invalidate cache
  useEffect(() => {
    if (!classId || notifications.length === 0) return

    // Get the most recent notification
    const latestNotification = notifications[0]

    // Check if it's relevant to this class (metadata might contain class_id)
    if (latestNotification.metadata?.class_id === classId) {
      // Invalidate queries for real-time updates
      queryClient.invalidateQueries({ queryKey: ['class-roster', classId] })
      queryClient.invalidateQueries({ queryKey: ['class', classId] })
    }
  }, [notifications, classId, queryClient])

  // Loading state
  if (classLoading || rosterLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading class data...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (classError || !classData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load class data</p>
          <button
            onClick={() => navigate('/teacher/classes')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Classes
          </button>
        </div>
      </div>
    )
  }

  // Calculate metrics from roster data
  const totalStudents = rosterData?.total_students || 0
  const activeStudents = rosterData?.students.filter(
    (s) => s.progress_summary && s.progress_summary.last_active
  ).length || 0

  // Calculate total requests from student progress summaries
  const totalRequests = rosterData?.students.reduce((sum, student) => {
    return sum + (student.progress_summary?.videos_requested || 0)
  }, 0) || 0

  // Calculate completion rate (videos watched / videos requested)
  const totalWatched = rosterData?.students.reduce((sum, student) => {
    return sum + (student.progress_summary?.videos_watched || 0)
  }, 0) || 0
  const completionRate = totalRequests > 0
    ? Math.round((totalWatched / totalRequests) * 100)
    : 0

  // Tab configuration
  const tabs: Tab[] = [
    {
      id: 'students',
      label: 'Students',
      icon: Users,
      badge: totalStudents,
    },
    {
      id: 'requests',
      label: 'Content Requests',
      icon: FileText,
      badge: totalRequests,
      disabled: true, // Phase 2.3 - Coming soon
    },
    {
      id: 'library',
      label: 'Class Library',
      icon: BookOpen,
      disabled: true, // Phase 2.4 - Coming soon
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: TrendingUp,
      disabled: true, // Phase 2.5 - Coming soon
    },
  ]

  // Handle archive class
  const handleArchiveClass = () => {
    if (confirm(`Are you sure you want to archive "${classData.name}"? This action can be undone.`)) {
      archiveClassMutation.mutate()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Back button */}
          <button
            onClick={() => navigate('/teacher/classes')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Classes
          </button>

          {/* Class header */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{classData.name}</h1>
              <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                {classData.subject && (
                  <span className="flex items-center">
                    <BookOpen className="w-4 h-4 mr-1" />
                    {classData.subject}
                  </span>
                )}
                <span className="flex items-center">
                  <Users className="w-4 h-4 mr-1" />
                  {totalStudents} students
                </span>
                <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                  {classData.class_code}
                </span>
              </div>
              {classData.description && (
                <p className="mt-3 text-gray-600 max-w-3xl">{classData.description}</p>
              )}
            </div>

            {/* Quick actions */}
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={() => setIsEditModalOpen(true)}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={handleArchiveClass}
                disabled={archiveClassMutation.isPending}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
              >
                <Archive className="w-4 h-4" />
                {archiveClassMutation.isPending ? 'Archiving...' : 'Archive'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Students"
            value={totalStudents.toString()}
            icon={Users}
            trend={
              totalStudents > 0
                ? { value: totalStudents, direction: 'up' as const, label: 'enrolled' }
                : undefined
            }
          />
          <StatsCard
            title="Content Requests"
            value={totalRequests.toString()}
            icon={FileText}
            trend={
              totalRequests > 0
                ? { value: totalRequests, direction: 'up' as const, label: 'total' }
                : undefined
            }
          />
          <StatsCard
            title="Completion Rate"
            value={`${completionRate}%`}
            icon={TrendingUp}
            trend={{
              value: completionRate,
              direction: completionRate >= 70 ? ('up' as const) : completionRate >= 40 ? ('neutral' as const) : ('down' as const),
              label: completionRate >= 70 ? 'Good' : completionRate >= 40 ? 'Moderate' : 'Low',
              isPercentage: true
            }}
          />
          <StatsCard
            title="Active Students (30d)"
            value={activeStudents.toString()}
            icon={Users}
            trend={
              activeStudents > 0
                ? { value: activeStudents, direction: 'up' as const, label: 'active' }
                : undefined
            }
          />
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => !tab.disabled && setActiveTab(tab.id)}
                    disabled={tab.disabled}
                    className={`
                      flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm
                      ${
                        isActive
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                      }
                      ${tab.disabled ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                    {tab.badge !== undefined && (
                      <span
                        className={`
                        ml-2 px-2 py-0.5 text-xs rounded-full
                        ${isActive ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'}
                      `}
                      >
                        {tab.badge}
                      </span>
                    )}
                    {tab.disabled && (
                      <span className="ml-2 text-xs text-gray-400">(Coming Soon)</span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'students' && rosterData && (
              <StudentRosterTable
                classId={classId!}
                className={rosterData.class_name}
                students={rosterData.students}
                totalStudents={rosterData.total_students}
                isLoading={rosterLoading}
                onRefresh={refetchRoster}
                onRemoveStudent={(studentId) => {
                  // TODO: Implement remove student mutation
                  console.log('Remove student:', studentId)
                }}
                onSendAnnouncement={(studentIds) => {
                  // TODO: Implement send announcement
                  console.log('Send announcement to:', studentIds)
                }}
                onAssignContent={(studentIds) => {
                  setSelectedStudentIds(studentIds)
                  setIsBulkRequestModalOpen(true)
                }}
              />
            )}
            {activeTab === 'requests' && (
              <div className="text-center py-12 text-gray-500">
                Content requests view coming in Phase 2.3
              </div>
            )}
            {activeTab === 'library' && (
              <div className="text-center py-12 text-gray-500">
                Class library coming in Phase 2.4
              </div>
            )}
            {activeTab === 'analytics' && (
              <div className="text-center py-12 text-gray-500">
                Analytics dashboard coming in Phase 2.5
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Class Modal */}
      <EditClassModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        classData={classData}
      />

      {/* Bulk Content Request Modal */}
      {rosterData && (
        <BulkContentRequestModal
          isOpen={isBulkRequestModalOpen}
          onClose={() => {
            setIsBulkRequestModalOpen(false)
            setSelectedStudentIds([])
          }}
          classId={classId!}
          students={rosterData.students}
          preSelectedStudentIds={selectedStudentIds}
          onSuccess={(response) => {
            toast({
              title: 'Success',
              description: `Created ${response.successful} content request${
                response.successful > 1 ? 's' : ''
              }`,
              variant: 'success',
            })
            // Refresh roster data to show updated metrics
            refetchRoster()
            setIsBulkRequestModalOpen(false)
            setSelectedStudentIds([])
          }}
        />
      )}
    </div>
  )
}

export default TeacherClassDashboard
