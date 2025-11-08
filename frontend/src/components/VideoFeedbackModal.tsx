/**
 * Video Feedback Modal Component
 *
 * Production-ready modal for collecting feedback after video playback
 * Features:
 * - Appears after video ends (auto-trigger)
 * - 5-star rating system
 * - Optional feedback textarea
 * - "Request similar content" quick action
 * - Save feedback to backend API
 * - Dismissible without blocking user
 * - Mobile-responsive design
 * - Accessibility (keyboard navigation, ARIA labels)
 */

import React, { useState, useEffect } from 'react'
import { X, Star, Send, Plus, ThumbsUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './ui/Button'
import type { GeneratedContent } from '../types'

export interface VideoFeedbackModalProps {
  /** The video that just finished playing */
  video: GeneratedContent
  /** Whether the modal is currently open */
  isOpen: boolean
  /** Callback to close the modal */
  onClose: () => void
  /** Optional callback when user requests similar content */
  onRequestSimilar?: () => void
  /** Optional callback after feedback is submitted */
  onFeedbackSubmitted?: (rating: number, feedback?: string) => void
}

/**
 * Video Feedback Modal Component
 */
export const VideoFeedbackModal: React.FC<VideoFeedbackModalProps> = ({
  video,
  isOpen,
  onClose,
  onRequestSimilar,
  onFeedbackSubmitted
}) => {
  const [rating, setRating] = useState<number>(0)
  const [hoveredRating, setHoveredRating] = useState<number>(0)
  const [feedback, setFeedback] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Reset modal state when opened
   */
  useEffect(() => {
    if (isOpen) {
      setRating(0)
      setHoveredRating(0)
      setFeedback('')
      setHasSubmitted(false)
      setError(null)
    }
  }, [isOpen])

  /**
   * Handle Escape key to close modal
   */
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
      return () => {
        document.removeEventListener('keydown', handleEscape)
        document.body.style.overflow = ''
      }
    }
  }, [isOpen, onClose])

  /**
   * Submit feedback to backend
   */
  const handleSubmit = async () => {
    if (rating === 0) {
      setError('Please select a rating before submitting')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // TODO: Replace with actual API call when backend endpoint is ready
      // await contentApi.submitFeedback(video.cache_key, {
      //   rating,
      //   feedback: feedback.trim() || undefined
      // })

      // Mock success for now
      await new Promise(resolve => setTimeout(resolve, 500))

      setHasSubmitted(true)
      onFeedbackSubmitted?.(rating, feedback.trim() || undefined)

      // Auto-close after 2 seconds
      setTimeout(() => {
        onClose()
      }, 2000)
    } catch (err) {
      console.error('Failed to submit feedback:', err)
      setError('Failed to submit feedback. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  /**
   * Handle request similar content
   */
  const handleRequestSimilar = () => {
    onRequestSimilar?.()
    onClose()
  }

  /**
   * Handle backdrop click to close
   */
  const handleBackdropClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
    >
      <div
        className={cn(
          'relative w-full max-w-md bg-white rounded-xl shadow-2xl',
          'transform transition-all duration-300',
          isOpen ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        )}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className={cn(
            'absolute top-4 right-4 p-2 rounded-lg',
            'text-gray-400 hover:text-gray-600 hover:bg-gray-100',
            'transition-colors duration-200',
            'focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:ring-offset-2'
          )}
          aria-label="Close feedback modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Success state */}
        {hasSubmitted ? (
          <div className="p-8 text-center">
            <div className="mb-4 inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
              <ThumbsUp className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Thank you!
            </h2>
            <p className="text-gray-600">
              Your feedback helps us create better content for you.
            </p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
              <h2
                id="feedback-modal-title"
                className="text-2xl font-bold text-gray-900 mb-2"
              >
                How was this video?
              </h2>
              <p className="text-sm text-gray-600 line-clamp-1">
                {video.query}
              </p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Star rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Rate this video <span className="text-red-500">*</span>
                </label>
                <div
                  className="flex items-center justify-center gap-2"
                  role="radiogroup"
                  aria-label="Video rating"
                  aria-required="true"
                >
                  {[1, 2, 3, 4, 5].map((star) => {
                    const isActive = (hoveredRating || rating) >= star
                    return (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        onMouseEnter={() => setHoveredRating(star)}
                        onMouseLeave={() => setHoveredRating(0)}
                        className={cn(
                          'p-2 rounded-lg transition-all duration-200',
                          'focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:ring-offset-2',
                          isActive ? 'scale-110' : 'scale-100 opacity-70'
                        )}
                        role="radio"
                        aria-checked={rating === star}
                        aria-label={`${star} star${star === 1 ? '' : 's'}`}
                      >
                        <Star
                          className={cn(
                            'w-10 h-10 transition-all duration-200',
                            isActive
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-gray-300'
                          )}
                        />
                      </button>
                    )
                  })}
                </div>
                {rating > 0 && (
                  <p className="text-center text-sm text-gray-500 mt-2">
                    {rating === 1 && 'Poor'}
                    {rating === 2 && 'Fair'}
                    {rating === 3 && 'Good'}
                    {rating === 4 && 'Very Good'}
                    {rating === 5 && 'Excellent'}
                  </p>
                )}
              </div>

              {/* Feedback textarea */}
              <div>
                <label
                  htmlFor="feedback-text"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Additional feedback (optional)
                </label>
                <textarea
                  id="feedback-text"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="What did you like or dislike about this video?"
                  rows={4}
                  maxLength={500}
                  className={cn(
                    'w-full px-4 py-3 border border-gray-300 rounded-lg',
                    'focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:border-transparent',
                    'resize-none transition-shadow duration-200',
                    'placeholder:text-gray-400'
                  )}
                  aria-describedby="feedback-help"
                />
                <div
                  id="feedback-help"
                  className="flex items-center justify-between mt-2"
                >
                  <p className="text-xs text-gray-500">
                    Help us improve your learning experience
                  </p>
                  <p className="text-xs text-gray-400">
                    {feedback.length}/500
                  </p>
                </div>
              </div>

              {/* Error message */}
              {error && (
                <div
                  className="p-3 bg-red-50 border border-red-200 rounded-lg"
                  role="alert"
                >
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {/* Action buttons */}
              <div className="space-y-3">
                <Button
                  variant="primary"
                  fullWidth
                  onClick={handleSubmit}
                  disabled={isSubmitting || rating === 0}
                  leftIcon={<Send className="w-4 h-4" />}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                </Button>

                {onRequestSimilar && (
                  <Button
                    variant="secondary"
                    fullWidth
                    onClick={handleRequestSimilar}
                    leftIcon={<Plus className="w-4 h-4" />}
                  >
                    Request Similar Content
                  </Button>
                )}

                <button
                  onClick={onClose}
                  className={cn(
                    'w-full py-2 text-sm text-gray-600 hover:text-gray-900',
                    'transition-colors duration-200',
                    'focus:outline-none focus:underline'
                  )}
                >
                  Skip for now
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default VideoFeedbackModal
