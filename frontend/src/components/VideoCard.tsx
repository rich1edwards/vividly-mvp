/**
 * Video Card Component
 *
 * Production-ready reusable card component for displaying video content
 * Features:
 * - Card layout with thumbnail and metadata
 * - Hover state with play button overlay
 * - Status badge (completed, processing, failed)
 * - View count display
 * - Skeleton loading state
 * - Click handler for navigation
 * - Responsive design (grid/list view support)
 * - Accessibility (keyboard navigation, ARIA labels, screen reader support)
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { GeneratedContent } from '../types'
import { Badge } from './ui/badge'
import { Skeleton } from './ui/skeleton'
import { cn } from '@/lib/utils'
import { Eye, Clock, Calendar } from 'lucide-react'
import { VideoThumbnail } from './VideoThumbnail'

export interface VideoCardProps {
  video: GeneratedContent
  layout?: 'grid' | 'list'
  onClick?: (cacheKey: string) => void
  className?: string
  loading?: boolean
}

/**
 * Get status configuration based on video status
 */
const getStatusConfig = (status?: 'processing' | 'completed' | 'failed') => {
  switch (status) {
    case 'processing':
      return {
        label: 'Processing',
        variant: 'secondary' as const,
        color: 'hsl(var(--stage-validating))'
      }
    case 'completed':
      return {
        label: 'Ready',
        variant: 'default' as const,
        color: 'hsl(var(--stage-completed))'
      }
    case 'failed':
      return {
        label: 'Failed',
        variant: 'destructive' as const,
        color: 'hsl(var(--stage-failed))'
      }
    default:
      return {
        label: 'Ready',
        variant: 'default' as const,
        color: 'hsl(var(--stage-completed))'
      }
  }
}

/**
 * Format duration from seconds to MM:SS
 */
const formatDuration = (seconds?: number): string => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * Format date to relative time or absolute date
 */
const formatDate = (isoDate: string): string => {
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Format view count with k/M suffixes
 */
const formatViews = (views?: number): string => {
  if (!views) return '0 views'
  if (views < 1000) return `${views} view${views === 1 ? '' : 's'}`
  if (views < 1000000) return `${(views / 1000).toFixed(1)}k views`
  return `${(views / 1000000).toFixed(1)}M views`
}

/**
 * Skeleton Loading Component
 */
export const VideoCardSkeleton: React.FC<{ layout?: 'grid' | 'list'; className?: string }> = ({
  layout = 'grid',
  className
}) => {
  const isGrid = layout === 'grid'

  return (
    <div
      className={cn(
        'rounded-lg border bg-card overflow-hidden',
        isGrid ? 'flex flex-col' : 'flex flex-row',
        className
      )}
      aria-busy="true"
      aria-label="Loading video card"
    >
      {/* Thumbnail Skeleton */}
      <Skeleton
        className={cn(
          'bg-muted',
          isGrid ? 'w-full aspect-video' : 'w-48 h-32 flex-shrink-0'
        )}
      />

      {/* Content Skeleton */}
      <div className={cn('p-4 flex-1 space-y-3', isGrid ? '' : 'flex flex-col justify-between')}>
        <div className="space-y-2">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <div className="flex items-center gap-4">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  )
}

/**
 * Main Video Card Component
 */
export const VideoCard: React.FC<VideoCardProps> = ({
  video,
  layout = 'grid',
  onClick,
  className,
  loading = false
}) => {
  const navigate = useNavigate()

  const isGrid = layout === 'grid'
  const statusConfig = getStatusConfig(video.status)

  // Loading state
  if (loading) {
    return <VideoCardSkeleton layout={layout} className={className} />
  }

  /**
   * Handle click - navigate to video player or call custom onClick
   */
  const handleClick = () => {
    if (onClick) {
      onClick(video.cache_key)
    } else if (video.video_url && video.status === 'completed') {
      navigate(`/video/${video.cache_key}`)
    }
  }

  /**
   * Handle keyboard navigation
   */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <article
      className={cn(
        'group relative rounded-lg border bg-card overflow-hidden transition-all duration-200',
        'hover:shadow-lg hover:border-primary/50',
        'focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2',
        isGrid ? 'flex flex-col' : 'flex flex-row',
        video.status === 'completed' ? 'cursor-pointer' : 'cursor-default opacity-75',
        className
      )}
      onClick={video.status === 'completed' ? handleClick : undefined}
      onKeyDown={video.status === 'completed' ? handleKeyDown : undefined}
      tabIndex={video.status === 'completed' ? 0 : -1}
      role="button"
      aria-label={`${video.topic || video.query} video${video.status === 'completed' ? ', click to play' : `, status: ${statusConfig.label}`}`}
      aria-disabled={video.status !== 'completed'}
    >
      {/* Thumbnail Section */}
      <div
        className={cn(
          'relative',
          isGrid ? 'w-full' : 'w-48 flex-shrink-0'
        )}
      >
        <VideoThumbnail
          src={video.thumbnail_url}
          videoTitle={video.topic || video.query}
          duration={video.duration ? formatDuration(video.duration) : undefined}
          showPlayButton={video.status === 'completed'}
          enableHover={video.status === 'completed'}
          priority={false}
          size={isGrid ? 'medium' : 'small'}
          className={cn(
            isGrid ? 'w-full' : 'w-48 h-32'
          )}
        />

        {/* Status Badge */}
        <div className="absolute top-2 right-2 z-10">
          <Badge variant={statusConfig.variant} className="shadow-sm">
            {statusConfig.label}
          </Badge>
        </div>
      </div>

      {/* Content Section */}
      <div
        className={cn(
          'p-4 flex-1',
          isGrid ? 'flex flex-col' : 'flex flex-col justify-between'
        )}
      >
        {/* Title and Subject */}
        <div className="space-y-1">
          <h3 className="font-display font-semibold text-base leading-tight line-clamp-2 group-hover:text-primary transition-colors">
            {video.topic || video.query}
          </h3>
          {video.subject && (
            <p className="text-sm text-muted-foreground">
              {video.subject}
            </p>
          )}
        </div>

        {/* Metadata */}
        <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          {/* Views */}
          {video.views !== undefined && (
            <div className="flex items-center gap-1" aria-label={formatViews(video.views)}>
              <Eye className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{formatViews(video.views)}</span>
            </div>
          )}

          {/* Duration */}
          {video.duration && (
            <div className="flex items-center gap-1" aria-label={`Duration: ${formatDuration(video.duration)}`}>
              <Clock className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{formatDuration(video.duration)}</span>
            </div>
          )}

          {/* Created Date */}
          <div className="flex items-center gap-1" aria-label={`Created: ${formatDate(video.created_at)}`}>
            <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{formatDate(video.created_at)}</span>
          </div>
        </div>

        {/* Interests Tags (if available) */}
        {video.interests && video.interests.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5" role="list" aria-label="Related interests">
            {video.interests.slice(0, 3).map((interest, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"
                role="listitem"
              >
                {interest}
              </span>
            ))}
            {video.interests.length > 3 && (
              <span
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground"
                aria-label={`${video.interests.length - 3} more interests`}
              >
                +{video.interests.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </article>
  )
}

// Export for use in other components
export default VideoCard
