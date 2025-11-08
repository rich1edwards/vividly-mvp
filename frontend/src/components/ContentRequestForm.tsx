/**
 * Content Request Form Component
 *
 * Form for students to request async video content generation.
 * - Submits request to backend (returns 202 Accepted)
 * - Navigates to status tracker for polling
 * - Supports grade level selection and optional interest override
 * - Phase 1.2.4: Dynamic estimated time display based on complexity
 */

import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { contentApi } from '../api/content'
import { interestsApi } from '../api/interests'
import type { User, Interest, AsyncContentRequest } from '../types'
import { Button } from './ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/Card'
import { InterestTagGrid } from './InterestTag'
import { calculateEstimatedTime, checkSystemLoad, getHighLoadWarning, type TimeEstimate } from '../utils/timeEstimation'
import { Clock, AlertTriangle } from 'lucide-react'

interface ContentRequestFormProps {
  user: User
  onRequestSubmitted?: (requestId: string) => void
}

export const ContentRequestForm: React.FC<ContentRequestFormProps> = ({
  user,
  onRequestSubmitted
}) => {
  const navigate = useNavigate()

  // Form state
  const [query, setQuery] = useState('')
  const [gradeLevel, setGradeLevel] = useState<number>(user.grade_level || 9)
  const [selectedInterest, setSelectedInterest] = useState<Interest | null>(null)

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Interests
  const [interests, setInterests] = useState<Interest[]>([])
  const [isLoadingInterests, setIsLoadingInterests] = useState(false)

  // Phase 1.2.4: Time estimation state
  const [isHighLoad, setIsHighLoad] = useState(false)

  // Load student's interests on mount
  useEffect(() => {
    fetchStudentInterests()
  }, [])

  // Phase 1.2.4: Check system load on mount
  useEffect(() => {
    const checkLoad = async () => {
      const highLoad = await checkSystemLoad()
      setIsHighLoad(highLoad)
    }
    checkLoad()
  }, [])

  // Phase 1.2.4: Calculate estimated time based on form state
  const timeEstimate: TimeEstimate = useMemo(() => {
    return calculateEstimatedTime({
      queryLength: query.trim().length,
      gradeLevel,
      hasInterest: selectedInterest !== null,
    })
  }, [query, gradeLevel, selectedInterest])

  const fetchStudentInterests = async () => {
    try {
      setIsLoadingInterests(true)
      const response = await interestsApi.getMy()
      setInterests(response.interests)

      // Auto-select first interest if available
      if (response.interests.length > 0 && !selectedInterest) {
        setSelectedInterest(response.interests[0])
      }
    } catch (err: any) {
      console.error('Failed to fetch interests:', err)
      // Non-critical error, don't block form
    } finally {
      setIsLoadingInterests(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    if (!query.trim()) {
      setError('Please enter a question or topic')
      return
    }

    if (query.trim().length < 10) {
      setError('Please enter a more detailed question (at least 10 characters)')
      return
    }

    if (query.trim().length > 500) {
      setError('Question is too long (max 500 characters)')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)

      // Build request
      const request: AsyncContentRequest = {
        student_id: user.user_id,
        student_query: query.trim(),
        grade_level: gradeLevel,
        ...(selectedInterest && { interest: selectedInterest.name })
      }

      // Submit async content request
      const response = await contentApi.generateContentAsync(request)

      // Callback for parent component
      if (onRequestSubmitted) {
        onRequestSubmitted(response.request_id)
      }

      // Navigate to status tracker
      navigate(`/content/request/${response.request_id}`)

    } catch (err: any) {
      console.error('Failed to submit content request:', err)

      // Handle specific error cases
      if (err.response?.status === 401) {
        setError('Session expired. Please log in again.')
      } else if (err.response?.status === 429) {
        setError('Too many requests. Please wait a moment and try again.')
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError('Failed to submit request. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const characterCount = query.length
  const isQueryValid = characterCount >= 10 && characterCount <= 500

  return (
    <Card variant="elevated" padding="lg">
      <CardHeader>
        <CardTitle>Generate Personalized Learning Video</CardTitle>
        <CardDescription>
          Ask any question or enter a topic you'd like to learn about.
          We'll create a personalized video tailored to your interests.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Query Input */}
          <div>
            <label htmlFor="query" className="block text-sm font-medium mb-2">
              What would you like to learn?
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Explain photosynthesis using basketball metaphors, or How do rockets work?"
              className={`
                w-full px-4 py-3 rounded-lg border resize-none
                focus:outline-none focus:ring-2 focus:ring-vividly-blue
                ${isQueryValid || query.length === 0
                  ? 'border-border'
                  : 'border-vividly-red'
                }
              `}
              rows={4}
              disabled={isSubmitting}
              maxLength={500}
            />
            <div className="flex justify-between items-center mt-1">
              <p className="text-xs text-muted-foreground">
                {characterCount < 10 && characterCount > 0 && (
                  <span className="text-vividly-red">At least 10 characters required</span>
                )}
                {characterCount >= 10 && (
                  <span className="text-green-600">Good length</span>
                )}
              </p>
              <p className={`text-xs ${characterCount > 500 ? 'text-vividly-red' : 'text-muted-foreground'}`}>
                {characterCount} / 500
              </p>
            </div>
          </div>

          {/* Grade Level Selector */}
          <div>
            <label htmlFor="gradeLevel" className="block text-sm font-medium mb-2">
              Grade Level
            </label>
            <select
              id="gradeLevel"
              value={gradeLevel}
              onChange={(e) => setGradeLevel(Number(e.target.value))}
              className="w-full px-4 py-3 rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-vividly-blue"
              disabled={isSubmitting}
            >
              <option value={9}>9th Grade (Freshman)</option>
              <option value={10}>10th Grade (Sophomore)</option>
              <option value={11}>11th Grade (Junior)</option>
              <option value={12}>12th Grade (Senior)</option>
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              Content will be tailored to this grade level
            </p>
          </div>

          {/* Interest Selector - Phase 1.2.3: Visual Interest Tags */}
          {interests.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium">
                  Connect to Your Interest (Optional)
                </label>
                {selectedInterest && (
                  <button
                    type="button"
                    onClick={() => setSelectedInterest(null)}
                    className="text-xs text-muted-foreground hover:text-foreground transition-colors underline"
                    disabled={isSubmitting || isLoadingInterests}
                  >
                    Clear selection
                  </button>
                )}
              </div>

              {isLoadingInterests ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-vividly-blue" />
                </div>
              ) : (
                <InterestTagGrid
                  interests={interests}
                  selectedInterest={selectedInterest}
                  onInterestSelect={(interest) => setSelectedInterest(interest)}
                  disabled={isSubmitting}
                  size="md"
                  maxColumns={3}
                />
              )}

              <p className="text-xs text-muted-foreground mt-3">
                {selectedInterest
                  ? `We'll use analogies and examples related to ${selectedInterest.name}`
                  : "Select an interest or we'll auto-select based on your profile"}
              </p>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4">
              <p className="text-sm text-vividly-red">{error}</p>
            </div>
          )}

          {/* Phase 1.2.4: Dynamic Estimated Time Display */}
          {query.trim().length >= 10 && (
            <div className={`rounded-lg p-4 border ${
              isHighLoad
                ? 'bg-amber-50 border-amber-200'
                : 'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex items-start gap-3">
                {isHighLoad ? (
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                ) : (
                  <Clock className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                )}
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    isHighLoad ? 'text-amber-900' : 'text-blue-900'
                  }`}>
                    {isHighLoad
                      ? getHighLoadWarning(timeEstimate.estimatedMinutes)
                      : `Estimated generation time: ${timeEstimate.displayText}`
                    }
                  </p>
                  <p className={`text-xs mt-1 ${
                    isHighLoad ? 'text-amber-700' : 'text-blue-700'
                  }`}>
                    {isHighLoad
                      ? 'Your request will be prioritized based on submission time.'
                      : "You'll be able to track progress in real-time. We'll notify you when it's ready!"
                    }
                  </p>
                  {!isHighLoad && timeEstimate.confidenceLevel !== 'high' && (
                    <p className="text-xs text-muted-foreground mt-1 italic">
                      Time estimate will improve as you provide more detail in your query.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </form>
      </CardContent>

      <CardFooter>
        <Button
          variant="primary"
          size="lg"
          fullWidth
          onClick={handleSubmit}
          isLoading={isSubmitting}
          disabled={!isQueryValid || isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Generate My Video'}
        </Button>
      </CardFooter>
    </Card>
  )
}
