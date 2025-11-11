/**
 * Interest Selection Modal
 *
 * Modal for students to select 2-5 interests on first login
 */

import React, { useState, useEffect } from 'react'
import { interestsApi, type Interest } from '../api/interests'
import { Button } from './ui/Button'
import { Card } from './ui/Card'

interface InterestSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

export const InterestSelectionModal: React.FC<InterestSelectionModalProps> = ({
  isOpen,
  onClose: _onClose,
  onComplete
}) => {
  const [interests, setInterests] = useState<Interest[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch all available interests
  useEffect(() => {
    if (isOpen) {
      fetchInterests()
    }
  }, [isOpen])

  const fetchInterests = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await interestsApi.getAll()
      setInterests(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load interests')
      console.error('Failed to fetch interests:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInterestToggle = (interestId: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(interestId)) {
        return prev.filter((id) => id !== interestId)
      } else {
        // Allow up to 5 selections
        if (prev.length >= 5) {
          return prev
        }
        return [...prev, interestId]
      }
    })
  }

  const handleSubmit = async () => {
    if (selectedIds.length < 2 || selectedIds.length > 5) {
      setError('Please select between 2-5 interests')
      return
    }

    try {
      setIsSaving(true)
      setError(null)
      await interestsApi.setMy(selectedIds)
      onComplete()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save interests')
      console.error('Failed to save interests:', err)
    } finally {
      setIsSaving(false)
    }
  }

  // Group interests by category
  const groupedInterests = Array.isArray(interests)
    ? interests.reduce((acc, interest) => {
        const category = interest.category || 'other'
        if (!acc[category]) {
          acc[category] = []
        }
        acc[category].push(interest)
        return acc
      }, {} as Record<string, Interest[]>)
    : {}

  const categoryLabels: Record<string, string> = {
    sports: 'Sports & Athletics',
    arts: 'Arts & Creativity',
    technology: 'Technology & Innovation',
    science: 'Science & Discovery',
    lifestyle: 'Lifestyle & Wellness',
    other: 'Other Interests'
  }

  const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
    sports: {
      bg: 'bg-vividly-blue-50',
      text: 'text-vividly-blue-700',
      border: 'border-vividly-blue-300'
    },
    arts: {
      bg: 'bg-vividly-purple-50',
      text: 'text-vividly-purple-700',
      border: 'border-vividly-purple-300'
    },
    technology: {
      bg: 'bg-vividly-green-50',
      text: 'text-vividly-green-700',
      border: 'border-vividly-green-300'
    },
    science: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-300'
    },
    lifestyle: {
      bg: 'bg-orange-50',
      text: 'text-orange-700',
      border: 'border-orange-300'
    },
    other: {
      bg: 'bg-gray-50',
      text: 'text-gray-700',
      border: 'border-gray-300'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto m-4" padding="lg">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-display font-bold text-foreground mb-2">
            Welcome to Vividly!
          </h2>
          <p className="text-muted-foreground">
            To personalize your learning experience, please select 2-5 interests. We'll use these
            to make your educational content more engaging and relevant.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Selection Counter */}
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">{selectedIds.length} of 5 selected</span>
            {selectedIds.length < 2 && (
              <span className="text-blue-600 ml-2">
                (Please select at least {2 - selectedIds.length} more)
              </span>
            )}
            {selectedIds.length >= 2 && selectedIds.length <= 5 && (
              <span className="text-green-600 ml-2">✓ Ready to continue</span>
            )}
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vividly-blue-600"></div>
          </div>
        )}

        {/* Interests Grid */}
        {!isLoading && (
          <div className="space-y-6">
            {Object.entries(groupedInterests).map(([category, categoryInterests]) => (
              <div key={category}>
                <h3 className="text-lg font-semibold text-foreground mb-3">
                  {categoryLabels[category] || category}
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {categoryInterests.map((interest) => {
                    const isSelected = selectedIds.includes(interest.interest_id)
                    const colors = categoryColors[category] || categoryColors.other

                    return (
                      <button
                        key={interest.interest_id}
                        onClick={() => handleInterestToggle(interest.interest_id)}
                        disabled={
                          !isSelected && selectedIds.length >= 5
                        }
                        className={`
                          p-4 rounded-lg border-2 text-left transition-all duration-200
                          ${
                            isSelected
                              ? `${colors.bg} ${colors.border} ring-2 ring-offset-2 ${colors.border.replace('border-', 'ring-')}`
                              : 'bg-white border-gray-200 hover:border-gray-300'
                          }
                          ${
                            !isSelected && selectedIds.length >= 5
                              ? 'opacity-50 cursor-not-allowed'
                              : 'cursor-pointer hover:shadow-md'
                          }
                        `}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            {interest.icon && (
                              <span className="text-2xl leading-none flex-shrink-0">
                                {interest.icon}
                              </span>
                            )}
                            <div className="flex-1">
                              <p
                                className={`font-medium ${isSelected ? colors.text : 'text-foreground'}`}
                              >
                                {interest.name}
                              </p>
                              {interest.description && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  {interest.description}
                                </p>
                              )}
                            </div>
                          </div>
                          {isSelected && (
                            <svg
                              className={`w-5 h-5 ${colors.text} flex-shrink-0 ml-2`}
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                clipRule="evenodd"
                              />
                            </svg>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-border flex justify-end gap-3">
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={selectedIds.length < 2 || selectedIds.length > 5 || isSaving}
            className="min-w-[120px]"
          >
            {isSaving ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </span>
            ) : (
              'Continue'
            )}
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default InterestSelectionModal
