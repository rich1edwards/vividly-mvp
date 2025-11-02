/**
 * Content Status Tracker Component
 *
 * Real-time status tracker for async content generation.
 * - Polls backend every 3 seconds for progress updates
 * - Displays progress bar and current stage
 * - Shows video player when complete
 * - Handles errors with retry options
 */

import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { contentApi } from '../api/content'
import type { ContentRequestStatus } from '../types'
import { Button } from './ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/Card'
import { VideoPlayer } from './VideoPlayer'

const POLL_INTERVAL_MS = 3000 // 3 seconds

interface StatusConfig {
  label: string
  color: string
  icon: JSX.Element
  description: string
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  pending: {
    label: 'Pending',
    color: 'text-gray-600',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    description: 'Your request is in the queue'
  },
  validating: {
    label: 'Validating',
    color: 'text-blue-600',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    description: 'Validating your request'
  },
  generating: {
    label: 'Generating',
    color: 'text-vividly-blue',
    icon: (
      <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    description: 'Creating your personalized video'
  },
  completed: {
    label: 'Complete',
    color: 'text-green-600',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    description: 'Your video is ready!'
  },
  failed: {
    label: 'Failed',
    color: 'text-vividly-red',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    description: 'Something went wrong'
  }
}

export const ContentStatusTracker: React.FC = () => {
  const { requestId } = useParams<{ requestId: string }>()
  const navigate = useNavigate()

  // Status state
  const [status, setStatus] = useState<ContentRequestStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pollCount, setPollCount] = useState(0)

  // Polling control
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // Fetch status
  const fetchStatus = async () => {
    if (!requestId) {
      setError('Invalid request ID')
      setIsLoading(false)
      return
    }

    try {
      const data = await contentApi.getRequestStatus(requestId)

      if (mountedRef.current) {
        setStatus(data)
        setError(null)
        setPollCount((prev) => prev + 1)

        // Stop polling if terminal state reached
        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling()
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch status:', err)

      if (mountedRef.current) {
        if (err.response?.status === 404) {
          setError('Request not found. It may have been deleted.')
          stopPolling()
        } else if (err.response?.status === 403) {
          setError('You do not have permission to view this request.')
          stopPolling()
        } else {
          setError('Failed to load status. Retrying...')
          // Continue polling - transient error
        }
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false)
      }
    }
  }

  const startPolling = () => {
    // Initial fetch
    fetchStatus()

    // Set up polling interval
    pollIntervalRef.current = setInterval(() => {
      fetchStatus()
    }, POLL_INTERVAL_MS)
  }

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }

  // Start polling on mount
  useEffect(() => {
    mountedRef.current = true
    startPolling()

    // Cleanup on unmount
    return () => {
      mountedRef.current = false
      stopPolling()
    }
  }, [requestId])

  // Retry handler for failed requests
  const handleRetry = () => {
    navigate('/content/new')
  }

  // Get status configuration
  const statusConfig = status ? STATUS_CONFIG[status.status] : STATUS_CONFIG.pending

  // Format time
  const formatTime = (isoString: string | null) => {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    return date.toLocaleTimeString()
  }

  // Calculate elapsed time
  const getElapsedTime = () => {
    if (!status?.started_at) return null
    const start = new Date(status.started_at).getTime()
    const now = new Date().getTime()
    const elapsed = Math.floor((now - start) / 1000) // seconds
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    return `${minutes}m ${seconds}s`
  }

  // Loading state
  if (isLoading && !status) {
    return (
      <Card variant="elevated" padding="lg">
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vividly-blue mb-4" />
            <p className="text-muted-foreground">Loading status...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Error state (terminal)
  if (error && !status) {
    return (
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <CardTitle className="text-vividly-red">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4">
            <p className="text-sm text-vividly-red">{error}</p>
          </div>
        </CardContent>
        <CardFooter>
          <Button variant="primary" onClick={() => navigate('/content/new')} fullWidth>
            Create New Request
          </Button>
        </CardFooter>
      </Card>
    )
  }

  if (!status) return null

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={statusConfig.color}>
                {statusConfig.icon}
              </div>
              <div>
                <CardTitle>{statusConfig.label}</CardTitle>
                <CardDescription>{statusConfig.description}</CardDescription>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Request ID</p>
              <p className="text-xs font-mono">{status.id.slice(0, 8)}...</p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">
                {status.current_stage || 'Processing...'}
              </span>
              <span className="text-sm font-medium text-vividly-blue">
                {status.progress_percentage}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-vividly-blue h-full transition-all duration-500 ease-out rounded-full"
                style={{ width: `${status.progress_percentage}%` }}
              />
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Topic</p>
              <p className="font-medium">{status.topic}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Grade Level</p>
              <p className="font-medium">{status.grade_level}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium">{formatTime(status.created_at)}</p>
            </div>
            {status.started_at && (
              <div>
                <p className="text-muted-foreground">Elapsed Time</p>
                <p className="font-medium">{getElapsedTime()}</p>
              </div>
            )}
          </div>

          {/* Polling Indicator */}
          {status.status !== 'completed' && status.status !== 'failed' && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>Auto-refreshing every 3 seconds (Poll #{pollCount})</span>
            </div>
          )}

          {/* Error Display */}
          {status.status === 'failed' && status.error_message && (
            <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4">
              <p className="text-sm font-medium text-vividly-red mb-1">Error Details</p>
              <p className="text-sm text-vividly-red">{status.error_message}</p>
              {status.error_stage && (
                <p className="text-xs text-vividly-red mt-2">
                  Failed at stage: {status.error_stage}
                </p>
              )}
              {status.retry_count > 0 && (
                <p className="text-xs text-vividly-red mt-1">
                  Retried {status.retry_count} time(s)
                </p>
              )}
            </div>
          )}
        </CardContent>

        {/* Actions */}
        {status.status === 'failed' && (
          <CardFooter>
            <Button variant="primary" onClick={handleRetry} fullWidth>
              Try Again with New Request
            </Button>
          </CardFooter>
        )}
      </Card>

      {/* Video Player (Completed State) */}
      {status.status === 'completed' && status.video_url && (
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle>Your Personalized Video</CardTitle>
            <CardDescription>
              Video generated successfully! Watch your personalized learning content below.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <VideoPlayer
              videoUrl={status.video_url}
              thumbnailUrl={status.thumbnail_url || undefined}
              title={status.topic}
            />

            {/* Script Display */}
            {status.script_text && (
              <div className="mt-6">
                <h4 className="text-sm font-medium mb-2">Video Script</h4>
                <div className="bg-muted rounded-lg p-4 text-sm">
                  <pre className="whitespace-pre-wrap font-sans">
                    {status.script_text}
                  </pre>
                </div>
              </div>
            )}
          </CardContent>
          <CardFooter className="flex gap-3">
            <Button variant="tertiary" onClick={() => navigate('/content/history')} fullWidth>
              View History
            </Button>
            <Button variant="primary" onClick={() => navigate('/content/new')} fullWidth>
              Create Another Video
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}
