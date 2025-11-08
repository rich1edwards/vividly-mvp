/**
 * Similar Content Banner Component
 *
 * Phase 1.2.2: Similar Content Detection
 *
 * Displays a banner when similar existing content is found before generating new content.
 * Helps students discover relevant existing videos and reduces duplicate generation.
 *
 * Features:
 * - Shows top 3 similar videos with thumbnails
 * - Different styling for high (>=60) vs medium (40-59) similarity
 * - "Watch Existing Video" action for each item
 * - "Generate New Version Anyway" action to proceed
 * - Dismissible with X button
 * - Mobile-responsive design
 * - Full accessibility (ARIA labels, keyboard navigation)
 */

import React from 'react'
import { X, AlertTriangle, Info, Play, Clock, Eye, Star } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { SimilarContentItem } from '../api/content'

export interface SimilarContentBannerProps {
  similarContent: SimilarContentItem[]
  hasHighSimilarity: boolean
  onGenerateAnyway: () => void
  onDismiss: () => void
}

/**
 * Format duration from seconds to MM:SS
 */
const formatDuration = (seconds: number | undefined): string => {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * Format number with k/M suffixes
 */
const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}k`
  return num.toString()
}

/**
 * SimilarContentBanner Component
 */
export const SimilarContentBanner: React.FC<SimilarContentBannerProps> = ({
  similarContent,
  hasHighSimilarity,
  onGenerateAnyway,
  onDismiss
}) => {
  const navigate = useNavigate()

  // Determine banner styling based on similarity level
  const isHighSimilarity = hasHighSimilarity
  const bgColor = isHighSimilarity ? 'bg-amber-50' : 'bg-blue-50'
  const borderColor = isHighSimilarity ? 'border-amber-200' : 'border-blue-200'
  const iconColor = isHighSimilarity ? 'text-amber-600' : 'text-blue-600'
  const Icon = isHighSimilarity ? AlertTriangle : Info

  // Show top 3 similar videos
  const displayedContent = similarContent.slice(0, 3)

  const handleWatchVideo = (cacheKey: string) => {
    navigate(`/student/watch/${cacheKey}`)
  }

  const handleKeyDown = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      action()
    }
  }

  return (
    <div
      className={`rounded-lg border-2 ${borderColor} ${bgColor} p-4 mb-6`}
      role="alert"
      aria-live="polite"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icon className={`h-5 w-5 ${iconColor}`} aria-hidden="true" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {isHighSimilarity
                ? 'Very Similar Content Found!'
                : 'Similar Content Available'}
            </h3>
            <p className="text-sm text-gray-600">
              {isHighSimilarity
                ? 'We found existing videos that are very similar to what you requested. Watching these might save you time!'
                : 'We found some related videos that might interest you.'}
            </p>
          </div>
        </div>
        <button
          onClick={onDismiss}
          onKeyDown={(e) => handleKeyDown(e, onDismiss)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Dismiss similar content banner"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Similar Videos Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {displayedContent.map((item) => (
          <div
            key={item.content_id}
            className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
          >
            {/* Thumbnail */}
            <div className="relative aspect-video bg-gray-200">
              {item.thumbnail_url ? (
                <img
                  src={item.thumbnail_url}
                  alt={`Thumbnail for ${item.title}`}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-400 to-purple-500">
                  <Play className="h-12 w-12 text-white opacity-50" />
                </div>
              )}

              {/* Duration Badge */}
              {item.duration_seconds && (
                <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                  {formatDuration(item.duration_seconds)}
                </div>
              )}

              {/* Similarity Score Badge */}
              <div
                className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-semibold ${
                  item.similarity_level === 'high'
                    ? 'bg-amber-500 text-white'
                    : 'bg-blue-500 text-white'
                }`}
              >
                {item.similarity_score}% Match
              </div>

              {/* Own Content Badge */}
              {item.is_own_content && (
                <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded font-semibold">
                  Your Video
                </div>
              )}
            </div>

            {/* Content Info */}
            <div className="p-3">
              <h4 className="font-semibold text-sm text-gray-900 mb-1 line-clamp-2">
                {item.title}
              </h4>

              {item.description && (
                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                  {item.description}
                </p>
              )}

              {/* Metadata */}
              <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                <div className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  <span>{formatNumber(item.views)}</span>
                </div>
                {item.average_rating && (
                  <div className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-current text-yellow-400" />
                    <span>{item.average_rating.toFixed(1)}</span>
                  </div>
                )}
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              {/* Watch Button */}
              <button
                onClick={() => handleWatchVideo(item.cache_key)}
                onKeyDown={(e) => handleKeyDown(e, () => handleWatchVideo(item.cache_key))}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                aria-label={`Watch ${item.title}`}
              >
                <Play className="h-4 w-4" />
                Watch This Video
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          Found {similarContent.length} similar video{similarContent.length !== 1 ? 's' : ''}.
          {isHighSimilarity && ' These videos cover very similar content.'}
        </div>
        <button
          onClick={onGenerateAnyway}
          onKeyDown={(e) => handleKeyDown(e, onGenerateAnyway)}
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
            isHighSimilarity
              ? 'bg-white border-2 border-amber-500 text-amber-700 hover:bg-amber-50'
              : 'bg-white border-2 border-blue-500 text-blue-700 hover:bg-blue-50'
          }`}
          aria-label="Generate new content anyway"
        >
          Generate New Version Anyway
        </button>
      </div>
    </div>
  )
}

export default SimilarContentBanner
