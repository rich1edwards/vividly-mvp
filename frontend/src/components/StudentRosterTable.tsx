/**
 * StudentRosterTable Component
 *
 * Reusable table component for displaying student roster with advanced features.
 * Uses DataTable component (TanStack Table) for sorting, filtering, and bulk actions.
 *
 * Features:
 * - Sortable columns (all 7 columns)
 * - Global search/filter
 * - Bulk selection with actions
 * - Row actions (View details, Remove from class)
 * - Progress data display with color coding
 * - Mobile responsive
 * - Keyboard accessible
 * - CSV export functionality
 */

import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Eye, Trash2, RefreshCw, Mail, UserPlus } from 'lucide-react'
import { DataTable } from './DataTable'
import { Button } from './ui/Button'
import type { StudentInRoster } from '../types/teacher'

interface StudentRosterTableProps {
  /**
   * Class ID for the roster
   */
  classId: string
  /**
   * Class name for display
   */
  className: string
  /**
   * Array of students in the roster
   */
  students: StudentInRoster[]
  /**
   * Total student count
   */
  totalStudents: number
  /**
   * Loading state
   */
  isLoading?: boolean
  /**
   * Callback to refresh roster data
   */
  onRefresh?: () => void
  /**
   * Callback when student is removed
   */
  onRemoveStudent?: (studentId: string) => void
  /**
   * Callback for bulk action: send announcement
   */
  onSendAnnouncement?: (studentIds: string[]) => void
  /**
   * Callback for bulk action: assign content
   */
  onAssignContent?: (studentIds: string[]) => void
}

/**
 * Format relative date (e.g., "2h ago", "3d ago")
 */
const formatRelativeDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)

  if (diffDay > 30) {
    return date.toLocaleDateString()
  } else if (diffDay > 0) {
    return `${diffDay}d ago`
  } else if (diffHr > 0) {
    return `${diffHr}h ago`
  } else if (diffMin > 0) {
    return `${diffMin}m ago`
  } else {
    return 'Just now'
  }
}

/**
 * StudentRosterTable Component
 */
export const StudentRosterTable: React.FC<StudentRosterTableProps> = ({
  className,
  students,
  totalStudents,
  isLoading = false,
  onRefresh,
  onRemoveStudent,
  onSendAnnouncement,
  onAssignContent,
}) => {
  const navigate = useNavigate()

  // Define table columns using TanStack Table's ColumnDef
  const columns: ColumnDef<StudentInRoster>[] = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Student',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium text-gray-900">
              {row.original.first_name} {row.original.last_name}
            </span>
            <span className="text-sm text-gray-500">{row.original.email}</span>
          </div>
        ),
        enableSorting: true,
        sortingFn: (rowA, rowB) => {
          const nameA = `${rowA.original.first_name} ${rowA.original.last_name}`.toLowerCase()
          const nameB = `${rowB.original.first_name} ${rowB.original.last_name}`.toLowerCase()
          return nameA.localeCompare(nameB)
        },
        filterFn: (row, _, filterValue) => {
          const searchTerm = String(filterValue).toLowerCase()
          const fullName = `${row.original.first_name} ${row.original.last_name}`.toLowerCase()
          const email = row.original.email.toLowerCase()
          return fullName.includes(searchTerm) || email.includes(searchTerm)
        },
      },
      {
        accessorKey: 'grade_level',
        header: 'Grade',
        cell: ({ row }) => (
          <span className="text-gray-900">
            {row.original.grade_level ? `Grade ${row.original.grade_level}` : '-'}
          </span>
        ),
        enableSorting: true,
      },
      {
        accessorKey: 'videos_requested',
        header: 'Videos Requested',
        cell: ({ row }) => (
          <span className="text-gray-900">
            {row.original.progress_summary?.videos_requested || 0}
          </span>
        ),
        enableSorting: true,
        sortingFn: (rowA, rowB) => {
          const reqA = rowA.original.progress_summary?.videos_requested || 0
          const reqB = rowB.original.progress_summary?.videos_requested || 0
          return reqA - reqB
        },
      },
      {
        accessorKey: 'videos_watched',
        header: 'Videos Watched',
        cell: ({ row }) => (
          <span className="text-gray-900">
            {row.original.progress_summary?.videos_watched || 0}
          </span>
        ),
        enableSorting: true,
        sortingFn: (rowA, rowB) => {
          const watchA = rowA.original.progress_summary?.videos_watched || 0
          const watchB = rowB.original.progress_summary?.videos_watched || 0
          return watchA - watchB
        },
      },
      {
        accessorKey: 'completion_rate',
        header: 'Completion',
        cell: ({ row }) => {
          const requested = row.original.progress_summary?.videos_requested || 0
          const watched = row.original.progress_summary?.videos_watched || 0
          const rate = requested > 0 ? Math.round((watched / requested) * 100) : 0

          let colorClass = 'text-gray-500'
          if (rate >= 80) colorClass = 'text-green-600'
          else if (rate >= 50) colorClass = 'text-yellow-600'
          else if (rate > 0) colorClass = 'text-red-600'

          return <span className={`font-medium ${colorClass}`}>{rate}%</span>
        },
        enableSorting: true,
        sortingFn: (rowA, rowB) => {
          const rateA =
            (rowA.original.progress_summary?.videos_requested || 0) > 0
              ? ((rowA.original.progress_summary?.videos_watched || 0) /
                  (rowA.original.progress_summary?.videos_requested || 0)) *
                100
              : 0
          const rateB =
            (rowB.original.progress_summary?.videos_requested || 0) > 0
              ? ((rowB.original.progress_summary?.videos_watched || 0) /
                  (rowB.original.progress_summary?.videos_requested || 0)) *
                100
              : 0
          return rateA - rateB
        },
      },
      {
        accessorKey: 'last_active',
        header: 'Last Active',
        cell: ({ row }) => (
          <span className="text-gray-600">
            {row.original.progress_summary?.last_active
              ? formatRelativeDate(row.original.progress_summary.last_active)
              : 'Never'}
          </span>
        ),
        enableSorting: true,
        sortingFn: (rowA, rowB) => {
          const dateA = rowA.original.progress_summary?.last_active
            ? new Date(rowA.original.progress_summary.last_active).getTime()
            : 0
          const dateB = rowB.original.progress_summary?.last_active
            ? new Date(rowB.original.progress_summary.last_active).getTime()
            : 0
          return dateB - dateA // Most recent first
        },
      },
      {
        accessorKey: 'enrolled_at',
        header: 'Enrolled',
        cell: ({ row }) => (
          <span className="text-gray-600">{formatRelativeDate(row.original.enrolled_at)}</span>
        ),
        enableSorting: true,
        sortingFn: (rowA, rowB) => {
          const dateA = new Date(rowA.original.enrolled_at).getTime()
          const dateB = new Date(rowB.original.enrolled_at).getTime()
          return dateB - dateA // Most recent first
        },
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/teacher/student/${row.original.user_id}`)}
              aria-label={`View ${row.original.first_name} ${row.original.last_name} details`}
            >
              <Eye className="w-4 h-4 mr-1" />
              View
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (
                  confirm(
                    `Remove ${row.original.first_name} ${row.original.last_name} from ${className}?`
                  )
                ) {
                  onRemoveStudent?.(row.original.user_id)
                }
              }}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
              aria-label={`Remove ${row.original.first_name} ${row.original.last_name} from class`}
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Remove
            </Button>
          </div>
        ),
        enableSorting: false,
      },
    ],
    [className, navigate, onRemoveStudent]
  )

  // Bulk actions component
  const renderBulkActions = (selectedRows: StudentInRoster[]) => {
    const selectedIds = selectedRows.map((student) => student.user_id)

    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600 mr-2">
          {selectedRows.length} {selectedRows.length === 1 ? 'student' : 'students'} selected
        </span>
        {onSendAnnouncement && (
          <Button
            variant="tertiary"
            size="sm"
            onClick={() => onSendAnnouncement(selectedIds)}
          >
            <Mail className="w-4 h-4 mr-2" />
            Send Announcement
          </Button>
        )}
        {onAssignContent && (
          <Button
            variant="tertiary"
            size="sm"
            onClick={() => onAssignContent(selectedIds)}
          >
            <UserPlus className="w-4 h-4 mr-2" />
            Assign Content
          </Button>
        )}
      </div>
    )
  }

  // Empty state
  const emptyState = (
    <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      <UserPlus className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      <p className="text-gray-600 font-medium mb-2">No students enrolled yet</p>
      <p className="text-sm text-gray-500 mb-4">
        Share the class code{' '}
        <code className="bg-gray-200 px-2 py-1 rounded font-mono">{className}</code> with
        students to get started
      </p>
      {onRefresh && (
        <Button onClick={onRefresh} variant="primary">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      )}
    </div>
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Class Roster ({totalStudents} {totalStudents === 1 ? 'student' : 'students'})
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Manage students, view progress, and perform bulk actions
          </p>
        </div>
        {onRefresh && (
          <Button
            variant="tertiary"
            onClick={onRefresh}
            disabled={isLoading}
            aria-label="Refresh roster"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        )}
      </div>

      {/* DataTable */}
      <DataTable
        data={students}
        columns={columns}
        enableRowSelection
        enableSorting
        enableGlobalFilter
        enablePagination
        enableExport
        exportFilename={`${className.replace(/\s+/g, '_')}_roster.csv`}
        bulkActions={renderBulkActions}
        loading={isLoading}
        emptyState={emptyState}
        pageSizeOptions={[10, 25, 50]}
        initialPageSize={10}
        stickyHeader
      />
    </div>
  )
}

export default StudentRosterTable
