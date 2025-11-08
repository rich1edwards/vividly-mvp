/**
 * Content Status Tracker Component - Phase 1.1.1 Enhanced
 *
 * Real-time status tracker for async content generation with 7-stage pipeline visualization.
 * Features:
 * - 7-stage horizontal stepper (desktop) / vertical stepper (mobile)
 * - Real-time progress updates every 3 seconds
 * - Cancel request functionality with confirmation
 * - Celebration animation on completion
 * - Enhanced accessibility (WCAG AA compliant)
 * - ETA calculations based on current stage
 * - Progress percentage per stage
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { contentApi } from '../api/content'
import type { ContentRequestStatus } from '../types'
import { Button } from './ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/Card'
import { VideoPlayer } from './VideoPlayer'
import {
  FileText,
  Brain,
  Target,
  Database,
  Sparkles,
  Volume2,
  Video,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  XCircle,
  PartyPopper
} from 'lucide-react'

const POLL_INTERVAL_MS = 3000 // 3 seconds

// 7-Stage Pipeline Configuration
interface PipelineStage {
  id: string
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  bgColor: string
  borderColor: string
  estimatedSeconds: number // For ETA calculation
}

const PIPELINE_STAGES: PipelineStage[] = [
  {
    id: 'request_received',
    label: 'Request Received',
    description: 'Your request has been queued',
    icon: FileText,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    estimatedSeconds: 5
  },
  {
    id: 'nlu_extraction',
    label: 'Understanding Query',
    description: 'AI is analyzing your question',
    icon: Brain,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    estimatedSeconds: 15
  },
  {
    id: 'interest_matching',
    label: 'Personalizing',
    description: 'Matching to your interests',
    icon: Target,
    color: 'text-pink-600',
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
    estimatedSeconds: 10
  },
  {
    id: 'rag_retrieval',
    label: 'Gathering Knowledge',
    description: 'Retrieving educational content',
    icon: Database,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    estimatedSeconds: 20
  },
  {
    id: 'script_generation',
    label: 'Writing Script',
    description: 'Creating personalized script',
    icon: Sparkles,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    estimatedSeconds: 30
  },
  {
    id: 'tts_generation',
    label: 'Generating Audio',
    description: 'Creating voice narration',
    icon: Volume2,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    estimatedSeconds: 40
  },
  {
    id: 'video_generation',
    label: 'Rendering Video',
    description: 'Finalizing your video',
    icon: Video,
    color: 'text-vividly-blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    estimatedSeconds: 50
  }
]

export const ContentStatusTracker: React.FC = () => {
  const { requestId } = useParams<{ requestId: string }>()
  const navigate = useNavigate()

  // Status state
  const [status, setStatus] = useState<ContentRequestStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pollCount, setPollCount] = useState(0)

  // UI state
  const [showCelebration, setShowCelebration] = useState(false)
  const [showCancelConfirm, setShowCancelConfirm] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)

  // Polling control
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)
  const previousStatusRef = useRef<string | null>(null)

  // Get current stage index from status
  const getCurrentStageIndex = useCallback((): number => {
    if (!status) return 0

    // Map current_stage from status to pipeline stage index
    if (status.current_stage) {
      const stageIndex = PIPELINE_STAGES.findIndex(
        stage => stage.id === status.current_stage
      )
      if (stageIndex !== -1) return stageIndex
    }

    // Fallback: map status to stage
    switch (status.status) {
      case 'pending':
        return 0
      case 'validating':
        return 1
      case 'generating':
        // Use progress percentage to estimate stage
        if (status.progress_percentage < 20) return 2
        if (status.progress_percentage < 40) return 3
        if (status.progress_percentage < 60) return 4
        if (status.progress_percentage < 80) return 5
        return 6
      case 'completed':
        return PIPELINE_STAGES.length
      case 'failed':
        return -1
      default:
        return 0
    }
  }, [status])

  // Calculate ETA based on current stage
  const calculateETA = useCallback((): string | null => {
    if (!status || status.status === 'completed' || status.status === 'failed') return null

    const currentIndex = getCurrentStageIndex()
    if (currentIndex < 0 || currentIndex >= PIPELINE_STAGES.length) return null

    // Sum remaining stage times
    let remainingSeconds = 0
    for (let i = currentIndex; i < PIPELINE_STAGES.length; i++) {
      remainingSeconds += PIPELINE_STAGES[i].estimatedSeconds
    }

    // Factor in current stage progress
    const currentStageProgress = status.progress_percentage % 14.3 // Rough estimate per stage
    const currentStageRemaining =
      PIPELINE_STAGES[currentIndex].estimatedSeconds * (1 - currentStageProgress / 14.3)
    remainingSeconds = remainingSeconds - PIPELINE_STAGES[currentIndex].estimatedSeconds + currentStageRemaining

    const minutes = Math.ceil(remainingSeconds / 60)
    return minutes > 0 ? `~${minutes} min` : '< 1 min'
  }, [status, getCurrentStageIndex])

  // Fetch status
  const fetchStatus = useCallback(async () => {
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
        setPollCount(prev => prev + 1)

        // Trigger celebration animation on completion
        if (
          data.status === 'completed' &&
          previousStatusRef.current &&
          previousStatusRef.current !== 'completed'
        ) {
          setShowCelebration(true)
          setTimeout(() => setShowCelebration(false), 5000) // Hide after 5 seconds
        }

        previousStatusRef.current = data.status

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
  }, [requestId])

  const startPolling = useCallback(() => {
    fetchStatus()
    pollIntervalRef.current = setInterval(() => {
      fetchStatus()
    }, POLL_INTERVAL_MS)
  }, [fetchStatus])

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  // Cancel request
  const handleCancelRequest = async () => {
    if (!requestId) return

    setIsCancelling(true)
    try {
      await contentApi.cancelRequest(requestId)
      setShowCancelConfirm(false)
      navigate('/content/new', {
        state: { message: 'Request cancelled successfully' }
      })
    } catch (err: any) {
      console.error('Failed to cancel request:', err)
      setError(err.response?.data?.detail || 'Failed to cancel request. It may have already completed.')
    } finally {
      setIsCancelling(false)
    }
  }

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

  // Start polling on mount
  useEffect(() => {
    mountedRef.current = true
    startPolling()

    return () => {
      mountedRef.current = false
      stopPolling()
    }
  }, [requestId, startPolling, stopPolling])

  // Loading state
  if (isLoading && !status) {
    return (
      <Card variant="elevated" padding="lg">
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12" role="status" aria-live="polite">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vividly-blue mb-4" aria-hidden="true" />
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
          <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4" role="alert">
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

  const currentStageIndex = getCurrentStageIndex()
  const eta = calculateETA()
  const canCancel = status.status !== 'completed' && status.status !== 'failed'

  return (
    <div className="space-y-6">
      {/* Celebration Animation */}
      {showCelebration && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          <div className="animate-bounce">
            <PartyPopper className="w-24 h-24 text-vividly-blue animate-pulse" aria-hidden="true" />
          </div>
          <p className="sr-only">Your video is complete!</p>
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      {showCancelConfirm && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="cancel-dialog-title"
        >
          <Card variant="elevated" padding="lg" className="max-w-md">
            <CardHeader>
              <CardTitle id="cancel-dialog-title">Cancel Request?</CardTitle>
              <CardDescription>
                Are you sure you want to cancel this content generation request? This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardFooter className="flex gap-3">
              <Button
                variant="tertiary"
                onClick={() => setShowCancelConfirm(false)}
                fullWidth
                disabled={isCancelling}
              >
                Keep Processing
              </Button>
              <Button
                variant="primary"
                onClick={handleCancelRequest}
                fullWidth
                isLoading={isCancelling}
                className="bg-vividly-red hover:bg-vividly-red/90"
              >
                {isCancelling ? 'Cancelling...' : 'Yes, Cancel'}
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* Status Card */}
      <Card variant="elevated" padding="lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Content Generation Progress</CardTitle>
              <CardDescription>
                {status.status === 'completed'
                  ? 'Your video is ready!'
                  : status.status === 'failed'
                  ? 'Generation failed'
                  : 'Generating your personalized learning video'}
              </CardDescription>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Request ID</p>
              <p className="text-xs font-mono">{status.id.slice(0, 8)}...</p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 7-Stage Pipeline Stepper - Horizontal (Desktop) */}
          <div className="hidden md:block" role="progressbar" aria-valuenow={status.progress_percentage} aria-valuemin={0} aria-valuemax={100} aria-label="Content generation progress">
            <div className="flex items-center justify-between">
              {PIPELINE_STAGES.map((stage, index) => {
                const isComplete = index < currentStageIndex
                const isCurrent = index === currentStageIndex
                const isFailed = status.status === 'failed'

                const StageIcon = stage.icon

                return (
                  <div key={stage.id} className="flex items-center flex-1">
                    <div className="flex flex-col items-center flex-1">
                      {/* Stage Icon */}
                      <div
                        className={`
                          relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300
                          ${isComplete ? 'bg-green-500 text-white' : ''}
                          ${isCurrent && !isFailed ? `${stage.bgColor} ${stage.borderColor} border-2` : ''}
                          ${!isComplete && !isCurrent ? 'bg-gray-100 text-gray-400' : ''}
                          ${isFailed && isCurrent ? 'bg-vividly-red/20 border-2 border-vividly-red' : ''}
                        `}
                        aria-label={`${stage.label}: ${isComplete ? 'complete' : isCurrent ? 'in progress' : 'pending'}`}
                      >
                        {isComplete ? (
                          <CheckCircle2 className="w-6 h-6" aria-hidden="true" />
                        ) : isCurrent && !isFailed ? (
                          <Loader2 className={`w-6 h-6 ${stage.color} animate-spin`} aria-hidden="true" />
                        ) : isFailed && isCurrent ? (
                          <XCircle className="w-6 h-6 text-vividly-red" aria-hidden="true" />
                        ) : (
                          <StageIcon className="w-6 h-6" aria-hidden="true" />
                        )}
                      </div>

                      {/* Stage Label */}
                      <div className="mt-2 text-center">
                        <p
                          className={`text-xs font-medium ${
                            isCurrent ? stage.color : isComplete ? 'text-green-600' : 'text-gray-500'
                          }`}
                        >
                          {stage.label}
                        </p>
                        {isCurrent && (
                          <p className="text-xs text-muted-foreground mt-1">{stage.description}</p>
                        )}
                      </div>
                    </div>

                    {/* Connector Line */}
                    {index < PIPELINE_STAGES.length - 1 && (
                      <div
                        className={`h-1 flex-1 mx-2 transition-all duration-300 ${
                          index < currentStageIndex ? 'bg-green-500' : 'bg-gray-200'
                        }`}
                        aria-hidden="true"
                      />
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* 7-Stage Pipeline Stepper - Vertical (Mobile) */}
          <div className="md:hidden space-y-4" role="progressbar" aria-valuenow={status.progress_percentage} aria-valuemin={0} aria-valuemax={100} aria-label="Content generation progress">
            {PIPELINE_STAGES.map((stage, index) => {
              const isComplete = index < currentStageIndex
              const isCurrent = index === currentStageIndex
              const isFailed = status.status === 'failed'

              const StageIcon = stage.icon

              return (
                <div key={stage.id} className="flex items-start gap-3">
                  {/* Stage Icon */}
                  <div
                    className={`
                      flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
                      ${isComplete ? 'bg-green-500 text-white' : ''}
                      ${isCurrent && !isFailed ? `${stage.bgColor} ${stage.borderColor} border-2` : ''}
                      ${!isComplete && !isCurrent ? 'bg-gray-100 text-gray-400' : ''}
                      ${isFailed && isCurrent ? 'bg-vividly-red/20 border-2 border-vividly-red' : ''}
                    `}
                    aria-label={`${stage.label}: ${isComplete ? 'complete' : isCurrent ? 'in progress' : 'pending'}`}
                  >
                    {isComplete ? (
                      <CheckCircle2 className="w-5 h-5" aria-hidden="true" />
                    ) : isCurrent && !isFailed ? (
                      <Loader2 className={`w-5 h-5 ${stage.color} animate-spin`} aria-hidden="true" />
                    ) : isFailed && isCurrent ? (
                      <XCircle className="w-5 h-5 text-vividly-red" aria-hidden="true" />
                    ) : (
                      <StageIcon className="w-5 h-5" aria-hidden="true" />
                    )}
                  </div>

                  {/* Stage Details */}
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        isCurrent ? stage.color : isComplete ? 'text-green-600' : 'text-gray-500'
                      }`}
                    >
                      {stage.label}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">{stage.description}</p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Overall Progress Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm font-medium text-vividly-blue">{status.progress_percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-vividly-blue h-full transition-all duration-500 ease-out rounded-full"
                style={{ width: `${status.progress_percentage}%` }}
                role="progressbar"
                aria-valuenow={status.progress_percentage}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
          </div>

          {/* Metadata Grid */}
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
            {eta && (
              <div>
                <p className="text-muted-foreground">Estimated Time Remaining</p>
                <p className="font-medium flex items-center gap-1">
                  <Clock className="w-3 h-3" aria-hidden="true" />
                  {eta}
                </p>
              </div>
            )}
          </div>

          {/* Polling Indicator */}
          {canCancel && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground" role="status" aria-live="polite">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" aria-hidden="true" />
              <span>Auto-refreshing every 3 seconds (Poll #{pollCount})</span>
            </div>
          )}

          {/* Error Display */}
          {status.status === 'failed' && status.error_message && (
            <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4" role="alert">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-vividly-red flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <p className="text-sm font-medium text-vividly-red mb-1">Error Details</p>
                  <p className="text-sm text-vividly-red">{status.error_message}</p>
                  {status.error_stage && (
                    <p className="text-xs text-vividly-red mt-2">Failed at stage: {status.error_stage}</p>
                  )}
                  {status.retry_count > 0 && (
                    <p className="text-xs text-vividly-red mt-1">Retried {status.retry_count} time(s)</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>

        {/* Actions */}
        <CardFooter className="flex gap-3">
          {canCancel && (
            <Button
              variant="tertiary"
              onClick={() => setShowCancelConfirm(true)}
              className="text-vividly-red border-vividly-red hover:bg-vividly-red/10"
              aria-label="Cancel content generation request"
            >
              Cancel Request
            </Button>
          )}
          {status.status === 'failed' && (
            <Button variant="primary" onClick={() => navigate('/content/new')} fullWidth>
              Try Again with New Request
            </Button>
          )}
        </CardFooter>
      </Card>

      {/* Video Player (Completed State) */}
      {status.status === 'completed' && status.video_url && (
        <Card variant="elevated" padding="lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PartyPopper className="w-6 h-6 text-vividly-blue" aria-hidden="true" />
              Your Personalized Video
            </CardTitle>
            <CardDescription>
              Video generated successfully! Watch your personalized learning content below.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <VideoPlayer
              sources={[
                {
                  src: status.video_url,
                  type: 'video/mp4',
                  size: 720
                }
              ]}
              poster={status.thumbnail_url || undefined}
              contentId={status.id}
              studentId={status.student_id}
            />

            {/* Script Display */}
            {status.script_text && (
              <div className="mt-6">
                <h4 className="text-sm font-medium mb-2">Video Script</h4>
                <div className="bg-muted rounded-lg p-4 text-sm">
                  <pre className="whitespace-pre-wrap font-sans">{status.script_text}</pre>
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
