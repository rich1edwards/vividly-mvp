/**
 * ActivityTimeline Component (Phase 2.3.1)
 *
 * Displays a student's activity timeline with infinite scroll
 * Activity types:
 * - content_request: Student requested new content
 * - video_completion: Student completed watching a video
 * - interest_change: Student updated their interests
 * - login: Student logged into the platform
 *
 * Features:
 * - Chronological display (newest first)
 * - Infinite scroll with pagination
 * - Activity-specific icons and colors
 * - Relative timestamps
 * - Empty state
 * - Loading skeleton
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  FileText,
  Video,
  Heart,
  LogIn,
  Clock,
  ChevronDown,
} from 'lucide-react'
import type { StudentActivity } from '../types/teacher'

interface ActivityTimelineProps {
  /**
   * Array of student activities
   */
  activities: StudentActivity[]
  /**
   * Student name for empty state message
   */
  studentName: string
  /**
   * Enable infinite scroll pagination
   */
  enableInfiniteScroll?: boolean
  /**
   * Items per page for pagination
   */
  itemsPerPage?: number
}

/**
 * Format relative timestamp (e.g., "2h ago", "3d ago", "Just now")
 */
const formatRelativeTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)
  const diffWeek = Math.floor(diffDay / 7)
  const diffMonth = Math.floor(diffDay / 30)

  if (diffSec < 60) return 'Just now'
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHr < 24) return `${diffHr}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  if (diffWeek < 4) return `${diffWeek}w ago`
  if (diffMonth < 12) return `${diffMonth}mo ago`
  return date.toLocaleDateString()
}

/**
 * Get activity icon and color based on type
 */
const getActivityStyle = (type: StudentActivity['type']) => {
  switch (type) {
    case 'content_request':
      return {
        icon: FileText,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
      }
    case 'video_completion':
      return {
        icon: Video,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
      }
    case 'interest_change':
      return {
        icon: Heart,
        color: 'text-pink-600',
        bgColor: 'bg-pink-50',
        borderColor: 'border-pink-200',
      }
    case 'login':
      return {
        icon: LogIn,
        color: 'text-gray-600',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200',
      }
    default:
      return {
        icon: Clock,
        color: 'text-gray-600',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200',
      }
  }
}

/**
 * ActivityTimeline Component
 */
export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  activities,
  studentName,
  enableInfiniteScroll = true,
  itemsPerPage = 20,
}) => {
  const [visibleCount, setVisibleCount] = useState(itemsPerPage)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const observerRef = useRef<IntersectionObserver | null>(null)
  const loadMoreRef = useRef<HTMLDivElement>(null)

  // Get visible activities based on pagination
  const visibleActivities = activities.slice(0, visibleCount)
  const hasMore = visibleCount < activities.length

  // Load more activities
  const loadMore = useCallback(() => {
    if (!hasMore || isLoadingMore) return

    setIsLoadingMore(true)
    // Simulate API delay for smooth UX
    setTimeout(() => {
      setVisibleCount((prev) => Math.min(prev + itemsPerPage, activities.length))
      setIsLoadingMore(false)
    }, 300)
  }, [hasMore, isLoadingMore, itemsPerPage, activities.length])

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    if (!enableInfiniteScroll || !loadMoreRef.current) return

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
          loadMore()
        }
      },
      { threshold: 0.1 }
    )

    observerRef.current.observe(loadMoreRef.current)

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [enableInfiniteScroll, hasMore, isLoadingMore, loadMore])

  // Empty state
  if (activities.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600 font-medium mb-2">No Activity Yet</p>
        <p className="text-sm text-gray-500">
          {studentName} hasn't performed any actions yet.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Activity Items */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

        {/* Activity List */}
        <div className="space-y-4">
          {visibleActivities.map((activity, index) => {
            const style = getActivityStyle(activity.type)
            const Icon = style.icon

            return (
              <div key={activity.activity_id} className="relative pl-14">
                {/* Activity Icon */}
                <div
                  className={`absolute left-0 w-12 h-12 rounded-full flex items-center justify-center ${style.bgColor} border-2 ${style.borderColor}`}
                >
                  <Icon className={`w-5 h-5 ${style.color}`} />
                </div>

                {/* Activity Content */}
                <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {activity.description}
                      </p>
                      {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                        <div className="mt-2 space-y-1">
                          {activity.metadata.topic && (
                            <p className="text-xs text-gray-600">
                              <span className="font-medium">Topic:</span>{' '}
                              {activity.metadata.topic}
                            </p>
                          )}
                          {activity.metadata.subject && (
                            <p className="text-xs text-gray-600">
                              <span className="font-medium">Subject:</span>{' '}
                              {activity.metadata.subject}
                            </p>
                          )}
                          {activity.metadata.video_title && (
                            <p className="text-xs text-gray-600">
                              <span className="font-medium">Video:</span>{' '}
                              {activity.metadata.video_title}
                            </p>
                          )}
                          {activity.metadata.interests_added &&
                            activity.metadata.interests_added.length > 0 && (
                              <p className="text-xs text-gray-600">
                                <span className="font-medium">Added:</span>{' '}
                                {activity.metadata.interests_added.join(', ')}
                              </p>
                            )}
                          {activity.metadata.interests_removed &&
                            activity.metadata.interests_removed.length > 0 && (
                              <p className="text-xs text-gray-600">
                                <span className="font-medium">Removed:</span>{' '}
                                {activity.metadata.interests_removed.join(', ')}
                              </p>
                            )}
                        </div>
                      )}
                    </div>
                    <div className="flex-shrink-0">
                      <time className="text-xs text-gray-500">
                        {formatRelativeTime(activity.timestamp)}
                      </time>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Load More Trigger (for infinite scroll) */}
      {enableInfiniteScroll && hasMore && (
        <div ref={loadMoreRef} className="py-4">
          {isLoadingMore && (
            <div className="text-center">
              <div className="inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-gray-500 mt-2">Loading more activities...</p>
            </div>
          )}
        </div>
      )}

      {/* Manual Load More Button (fallback) */}
      {!enableInfiniteScroll && hasMore && (
        <div className="text-center pt-4">
          <button
            onClick={loadMore}
            disabled={isLoadingMore}
            className="px-6 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
          >
            {isLoadingMore ? (
              <>
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Load More ({activities.length - visibleCount} remaining)
              </>
            )}
          </button>
        </div>
      )}

      {/* End of Timeline */}
      {!hasMore && activities.length > itemsPerPage && (
        <div className="text-center py-4 text-sm text-gray-500">
          End of activity timeline
        </div>
      )}
    </div>
  )
}

export default ActivityTimeline
