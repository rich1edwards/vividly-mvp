/**
 * Related Videos Sidebar Component
 *
 * Production-ready sidebar component for displaying related videos
 * Features:
 * - Algorithm-based related video suggestions (same topic/subject)
 * - Up Next autoplay suggestion
 * - Request similar content action
 * - Collapsible on mobile
 * - Smooth scroll animations
 * - Accessibility (keyboard navigation, ARIA labels)
 */

import React, { useMemo } from 'react'
import type { GeneratedContent } from '../types'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Button } from './ui/Button'
import { PlayCircle, Plus, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface RelatedVideosSidebarProps {
  currentVideo: GeneratedContent
  allVideos: GeneratedContent[]
  onVideoSelect: (cacheKey: string) => void
  onRequestSimilar?: () => void
  className?: string
  collapsed?: boolean
  onToggleCollapse?: () => void
}

/**
 * Calculate similarity score between two videos
 */
const calculateSimilarity = (video1: GeneratedContent, video2: GeneratedContent): number => {
  let score = 0

  // Same topic: +50 points
  if (video1.topic && video2.topic && video1.topic === video2.topic) {
    score += 50
  }

  // Same subject: +30 points
  if (video1.subject && video2.subject && video1.subject === video2.subject) {
    score += 30
  }

  // Shared interests: +10 points per interest
  const interests1 = new Set(video1.interests || [])
  const interests2 = new Set(video2.interests || [])
  const sharedInterests = [...interests1].filter(i => interests2.has(i))
  score += sharedInterests.length * 10

  // Recency bonus: videos from last 7 days get +5 points
  const created = new Date(video2.created_at)
  const daysSince = (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24)
  if (daysSince < 7) {
    score += 5
  }

  return score
}

/**
 * Format date to relative time
 */
const formatRelativeTime = (isoDate: string): string => {
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/**
 * Related Videos Sidebar Component
 */
export const RelatedVideosSidebar: React.FC<RelatedVideosSidebarProps> = ({
  currentVideo,
  allVideos,
  onVideoSelect,
  onRequestSimilar,
  className = '',
  collapsed = false,
  onToggleCollapse
}) => {

  /**
   * Calculate related videos using similarity algorithm
   */
  const relatedVideos = useMemo(() => {
    if (!allVideos || allVideos.length === 0) return []

    // Filter out current video and only show completed videos
    const candidates = allVideos.filter(
      v => v.cache_key !== currentVideo.cache_key && v.status === 'completed'
    )

    // Calculate similarity scores
    const scored = candidates.map(video => ({
      video,
      score: calculateSimilarity(currentVideo, video)
    }))

    // Sort by score (highest first) and take top 5
    return scored
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
      .map(s => s.video)
  }, [currentVideo, allVideos])

  /**
   * Get "Up Next" suggestion (highest scored video)
   */
  const upNext = relatedVideos.length > 0 ? relatedVideos[0] : null

  if (collapsed && onToggleCollapse) {
    return (
      <button
        onClick={onToggleCollapse}
        className={cn(
          'fixed right-0 top-1/2 -translate-y-1/2 z-40',
          'bg-vividly-blue text-white p-3 rounded-l-lg shadow-lg',
          'hover:bg-vividly-blue-600 transition-all',
          'focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:ring-offset-2',
          className
        )}
        aria-label="Show related videos"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Up Next Section */}
      {upNext && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Up Next</CardTitle>
              {onToggleCollapse && (
                <button
                  onClick={onToggleCollapse}
                  className="lg:hidden p-1 hover:bg-gray-100 rounded transition-colors"
                  aria-label="Hide related videos"
                >
                  <ChevronRight className="w-5 h-5 rotate-180" />
                </button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <button
              onClick={() => onVideoSelect(upNext.cache_key)}
              className="w-full text-left group focus:outline-none focus:ring-2 focus:ring-vividly-blue rounded-lg"
            >
              {/* Thumbnail */}
              <div className="relative aspect-video bg-gray-200 rounded-lg overflow-hidden mb-3">
                {upNext.thumbnail_url ? (
                  <img
                    src={upNext.thumbnail_url}
                    alt={upNext.query}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-vividly-blue-100 to-vividly-purple-100">
                    <PlayCircle className="w-12 h-12 text-vividly-blue-400" />
                  </div>
                )}
                {/* Play button overlay */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-300 flex items-center justify-center">
                  <PlayCircle className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </div>
                {/* Duration badge */}
                {upNext.duration && (
                  <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                    {Math.floor(upNext.duration / 60)}:{String(upNext.duration % 60).padStart(2, '0')}
                  </div>
                )}
              </div>

              {/* Video info */}
              <h3 className="font-semibold text-sm line-clamp-2 mb-1 group-hover:text-vividly-blue transition-colors">
                {upNext.query}
              </h3>
              <p className="text-xs text-muted-foreground">
                {formatRelativeTime(upNext.created_at)}
                {upNext.views !== undefined && ` • ${upNext.views} views`}
              </p>
            </button>
          </CardContent>
        </Card>
      )}

      {/* Related Videos List */}
      {relatedVideos.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Related Videos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {relatedVideos.slice(1).map((video) => (
              <button
                key={video.cache_key}
                onClick={() => onVideoSelect(video.cache_key)}
                className="w-full flex gap-3 group text-left focus:outline-none focus:ring-2 focus:ring-vividly-blue rounded-lg p-2 -m-2"
              >
                {/* Thumbnail */}
                <div className="relative w-32 aspect-video bg-gray-200 rounded overflow-hidden flex-shrink-0">
                  {video.thumbnail_url ? (
                    <img
                      src={video.thumbnail_url}
                      alt={video.query}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-vividly-blue-100 to-vividly-purple-100">
                      <PlayCircle className="w-6 h-6 text-vividly-blue-400" />
                    </div>
                  )}
                  {video.duration && (
                    <div className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded">
                      {Math.floor(video.duration / 60)}:{String(video.duration % 60).padStart(2, '0')}
                    </div>
                  )}
                </div>

                {/* Video info */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm line-clamp-2 mb-1 group-hover:text-vividly-blue transition-colors">
                    {video.query}
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    {formatRelativeTime(video.created_at)}
                  </p>
                  {video.views !== undefined && (
                    <p className="text-xs text-muted-foreground">
                      {video.views} views
                    </p>
                  )}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Request Similar Content Action */}
      {onRequestSimilar && (
        <Card>
          <CardContent className="pt-6">
            <Button
              variant="tertiary"
              fullWidth
              onClick={onRequestSimilar}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Request Similar Content
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {relatedVideos.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <div className="text-muted-foreground text-sm space-y-2">
              <p>No related videos yet</p>
              <p className="text-xs">
                Watch more videos to see recommendations
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default RelatedVideosSidebar
