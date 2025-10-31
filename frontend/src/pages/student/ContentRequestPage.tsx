/**
 * Student Content Request Page
 *
 * Core feature for students to request AI-generated learning content
 */

import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useToast } from '../../hooks/useToast'
import { contentApi } from '../../api/content'
import type { Interest, ContentResponse } from '../../types'

export const ContentRequestPage: React.FC = () => {
  const navigate = useNavigate()
  const { success, error: showError } = useToast()

  // State
  const [interests, setInterests] = useState<Interest[]>([])
  const [studentInterests, setStudentInterests] = useState<Interest[]>([])
  const [query, setQuery] = useState('')
  const [topic, setTopic] = useState('')
  const [subject, setSubject] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingInterests, setIsLoadingInterests] = useState(true)
  const [showInterestModal, setShowInterestModal] = useState(false)
  const [showClarificationModal, setShowClarificationModal] = useState(false)
  const [clarificationData, setClarificationData] = useState<{
    requestId: string
    message: string
    suggestions: string[]
  } | null>(null)
  const [pollingInterval, setPollingInterval] = useState<number | null>(null)

  // Load interests on mount
  useEffect(() => {
    loadInterests()
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [])

  const loadInterests = async () => {
    try {
      setIsLoadingInterests(true)
      const [allInterests, selected] = await Promise.all([
        contentApi.getInterests(),
        contentApi.getStudentInterests()
      ])
      setInterests(allInterests)
      setStudentInterests(selected)
    } catch (error) {
      showError('Failed to load interests', 'Please try again')
    } finally {
      setIsLoadingInterests(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) {
      showError('Query required', 'Please enter your learning question')
      return
    }

    if (studentInterests.length === 0) {
      showError('Interests required', 'Please select at least one interest')
      setShowInterestModal(true)
      return
    }

    try {
      setIsLoading(true)
      const response = await contentApi.generateContent({
        query: query.trim(),
        topic: topic.trim() || undefined,
        subject: subject || undefined
      })

      handleContentResponse(response)
    } catch (error: any) {
      showError('Request failed', error.response?.data?.detail || 'Please try again')
      setIsLoading(false)
    }
  }

  const handleContentResponse = (response: ContentResponse) => {
    if (response.status === 'needs_clarification' && response.clarification_request) {
      setClarificationData({
        requestId: response.clarification_request.request_id,
        message: response.clarification_request.message,
        suggestions: response.clarification_request.suggestions || []
      })
      setShowClarificationModal(true)
      setIsLoading(false)
    } else if (response.status === 'processing') {
      // Start polling for status
      success('Content generation started', 'Your video is being created')
      startPolling(response.cache_key!)
    } else if (response.status === 'completed') {
      success('Content ready!', 'Your video is ready to watch')
      setIsLoading(false)
      navigate(`/student/videos/${response.cache_key}`)
    } else if (response.status === 'failed') {
      showError('Generation failed', response.message || 'Please try a different query')
      setIsLoading(false)
    }
  }

  const startPolling = (cacheKey: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await contentApi.getContentStatus(cacheKey)

        if (response.status === 'completed') {
          clearInterval(interval)
          setPollingInterval(null)
          setIsLoading(false)
          success('Content ready!', 'Your video is ready to watch')
          navigate(`/student/videos/${cacheKey}`)
        } else if (response.status === 'failed') {
          clearInterval(interval)
          setPollingInterval(null)
          setIsLoading(false)
          showError('Generation failed', response.message || 'Please try again')
        }
      } catch (error) {
        clearInterval(interval)
        setPollingInterval(null)
        setIsLoading(false)
        showError('Status check failed', 'Please refresh the page')
      }
    }, 3000) // Poll every 3 seconds

    setPollingInterval(interval)
  }

  const handleClarificationSubmit = async (clarifiedQuery: string) => {
    if (!clarificationData) return

    try {
      setIsLoading(true)
      setShowClarificationModal(false)

      const response = await contentApi.respondToClarification({
        request_id: clarificationData.requestId,
        clarified_query: clarifiedQuery,
        topic: topic.trim() || undefined
      })

      handleContentResponse(response)
    } catch (error: any) {
      showError('Request failed', error.response?.data?.detail || 'Please try again')
      setIsLoading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            Request Learning Content
          </h1>
          <p className="text-muted-foreground mt-2">
            Ask a question and get a personalized video explanation
          </p>
        </div>

        {/* Interests Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Your Interests</CardTitle>
                <CardDescription>
                  {studentInterests.length === 0
                    ? 'Select 1-5 interests to personalize your content'
                    : `${studentInterests.length} interest${studentInterests.length > 1 ? 's' : ''} selected`}
                </CardDescription>
              </div>
              <Button
                variant="tertiary"
                size="sm"
                onClick={() => setShowInterestModal(true)}
                disabled={isLoadingInterests}
              >
                Manage Interests
              </Button>
            </div>
          </CardHeader>
          {studentInterests.length > 0 && (
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {studentInterests.map((interest) => (
                  <span
                    key={interest.interest_id}
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-vividly-blue-100 text-vividly-blue-700 text-sm font-medium"
                  >
                    {interest.name}
                  </span>
                ))}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Content Request Form */}
        <Card>
          <CardHeader>
            <CardTitle>What would you like to learn?</CardTitle>
            <CardDescription>
              Ask any question and we'll create a personalized video explanation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Query Input */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Your Question <span className="text-vividly-red-500">*</span>
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Example: How does photosynthesis work? Why do we have seasons? What is the Pythagorean theorem?"
                  className="w-full min-h-[120px] px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-y"
                  disabled={isLoading}
                  required
                />
                <p className="text-sm text-muted-foreground mt-2">
                  Be as specific as possible for the best results
                </p>
              </div>

              {/* Optional Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Topic (Optional)"
                  placeholder="e.g., Biology, Math, History"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  disabled={isLoading}
                  helperText="Help us categorize your content"
                />

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Subject (Optional)
                  </label>
                  <select
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50"
                    disabled={isLoading}
                  >
                    <option value="">Select a subject</option>
                    <option value="mathematics">Mathematics</option>
                    <option value="science">Science</option>
                    <option value="english">English</option>
                    <option value="history">History</option>
                    <option value="geography">Geography</option>
                    <option value="computer_science">Computer Science</option>
                    <option value="art">Art</option>
                    <option value="music">Music</option>
                    <option value="physical_education">Physical Education</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  {isLoading ? 'Generating your personalized content...' : 'Ready to create your video?'}
                </p>
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  isLoading={isLoading}
                  disabled={isLoading || studentInterests.length === 0}
                >
                  Generate Content
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Help Tips */}
        <Card variant="outlined">
          <CardContent className="pt-6">
            <h3 className="font-semibold text-foreground mb-3">Tips for great content:</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-vividly-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Ask specific questions rather than broad topics</span>
              </li>
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-vividly-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Include context about what you already know</span>
              </li>
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-vividly-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Your selected interests help personalize the explanation</span>
              </li>
              <li className="flex items-start gap-2">
                <svg className="w-5 h-5 text-vividly-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Generation typically takes 30-60 seconds</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Interest Selection Modal */}
      {showInterestModal && (
        <InterestModal
          interests={interests}
          selectedInterests={studentInterests}
          onClose={() => setShowInterestModal(false)}
          onSave={async (selected) => {
            try {
              const updated = await contentApi.updateStudentInterests(
                selected.map(i => i.interest_id)
              )
              setStudentInterests(updated)
              setShowInterestModal(false)
              success('Interests updated', 'Your preferences have been saved')
            } catch (error) {
              showError('Update failed', 'Please try again')
            }
          }}
        />
      )}

      {/* Clarification Modal */}
      {showClarificationModal && clarificationData && (
        <ClarificationModal
          message={clarificationData.message}
          suggestions={clarificationData.suggestions}
          onSubmit={handleClarificationSubmit}
          onClose={() => {
            setShowClarificationModal(false)
            setIsLoading(false)
          }}
        />
      )}
    </DashboardLayout>
  )
}

interface InterestModalProps {
  interests: Interest[]
  selectedInterests: Interest[]
  onClose: () => void
  onSave: (selected: Interest[]) => void
}

const InterestModal: React.FC<InterestModalProps> = ({
  interests,
  selectedInterests,
  onClose,
  onSave
}) => {
  const [selected, setSelected] = useState<Interest[]>(selectedInterests)

  const toggleInterest = (interest: Interest) => {
    if (selected.find(i => i.interest_id === interest.interest_id)) {
      setSelected(selected.filter(i => i.interest_id !== interest.interest_id))
    } else if (selected.length < 5) {
      setSelected([...selected, interest])
    }
  }

  const isSelected = (interest: Interest) => {
    return selected.some(i => i.interest_id === interest.interest_id)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <CardHeader>
          <CardTitle>Select Your Interests</CardTitle>
          <CardDescription>
            Choose 1-5 interests to personalize your learning content ({selected.length}/5 selected)
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {interests.map((interest) => {
              const selected = isSelected(interest)
              return (
                <button
                  key={interest.interest_id}
                  onClick={() => toggleInterest(interest)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    selected
                      ? 'border-vividly-blue bg-vividly-blue-50 text-vividly-blue-700'
                      : 'border-border hover:border-vividly-blue-200 hover:bg-muted'
                  }`}
                >
                  <div className="font-medium">{interest.name}</div>
                  {interest.description && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {interest.description}
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </CardContent>
        <div className="p-6 border-t border-border flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => onSave(selected)}
            disabled={selected.length === 0}
          >
            Save Interests
          </Button>
        </div>
      </Card>
    </div>
  )
}

interface ClarificationModalProps {
  message: string
  suggestions: string[]
  onSubmit: (clarifiedQuery: string) => void
  onClose: () => void
}

const ClarificationModal: React.FC<ClarificationModalProps> = ({
  message,
  suggestions,
  onSubmit,
  onClose
}) => {
  const [clarifiedQuery, setClarifiedQuery] = useState('')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Clarify Your Question</CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {suggestions.length > 0 && (
            <div>
              <p className="text-sm font-medium text-foreground mb-2">
                Did you mean:
              </p>
              <div className="space-y-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setClarifiedQuery(suggestion)}
                    className="w-full p-3 text-left rounded-lg border border-border hover:border-vividly-blue hover:bg-vividly-blue-50 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Or provide more details:
            </label>
            <textarea
              value={clarifiedQuery}
              onChange={(e) => setClarifiedQuery(e.target.value)}
              placeholder="Clarify your question..."
              className="w-full min-h-[100px] px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-y"
            />
          </div>
        </CardContent>
        <div className="p-6 border-t border-border flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => onSubmit(clarifiedQuery)}
            disabled={!clarifiedQuery.trim()}
          >
            Submit
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default ContentRequestPage
