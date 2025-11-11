/**
 * Student Profile Page
 *
 * Profile page for students to view and manage their account settings and interests
 */

import React, { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { useAuthStore } from '../../store/authStore'
import { interestsApi, type Interest } from '../../api/interests'

export const StudentProfile: React.FC = () => {
  const { user } = useAuthStore()
  const [interests, setInterests] = useState<Interest[]>([])
  const [allInterests, setAllInterests] = useState<Interest[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    loadInterests()
  }, [])

  const loadInterests = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [myInterests, availableInterests] = await Promise.all([
        interestsApi.getMy(),
        interestsApi.getAll()
      ])
      setInterests(myInterests.interests)
      setAllInterests(availableInterests)
      setSelectedIds(myInterests.interests.map((i) => i.interest_id))
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load interests')
      console.error('Failed to load interests:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInterestToggle = (interestId: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(interestId)) {
        return prev.filter((id) => id !== interestId)
      } else {
        if (prev.length >= 5) {
          return prev
        }
        return [...prev, interestId]
      }
    })
  }

  const handleSave = async () => {
    if (selectedIds.length < 2 || selectedIds.length > 5) {
      setError('Please select between 2-5 interests')
      return
    }

    try {
      setIsSaving(true)
      setError(null)
      setSuccessMessage(null)
      const response = await interestsApi.setMy(selectedIds)
      setInterests(response.interests)
      setIsEditing(false)
      setSuccessMessage('Interests updated successfully!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save interests')
      console.error('Failed to save interests:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setSelectedIds(interests.map((i) => i.interest_id))
    setIsEditing(false)
    setError(null)
  }

  // Group interests by category
  const groupedInterests = Array.isArray(allInterests)
    ? allInterests.reduce((acc, interest) => {
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

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">Profile</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account information and interests
          </p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMessage}
          </div>
        )}

        {/* User Information */}
        <Card>
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Your account details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">First Name</label>
                  <p className="mt-1 text-foreground">{user?.first_name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Last Name</label>
                  <p className="mt-1 text-foreground">{user?.last_name}</p>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Email</label>
                <p className="mt-1 text-foreground">{user?.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Role</label>
                <p className="mt-1 text-foreground capitalize">
                  {user?.role.replace('_', ' ')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Interests Section */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>My Interests</CardTitle>
                <CardDescription>
                  Your learning interests help us personalize your content (2-5 required)
                </CardDescription>
              </div>
              {!isEditing && (
                <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>
                  <svg
                    className="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                    />
                  </svg>
                  Edit
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Selection Counter (only when editing) */}
            {isEditing && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <span className="font-semibold">{selectedIds.length} of 5 selected</span>
                  {selectedIds.length < 2 && (
                    <span className="text-blue-600 ml-2">
                      (Please select at least {2 - selectedIds.length} more)
                    </span>
                  )}
                  {selectedIds.length >= 2 && selectedIds.length <= 5 && (
                    <span className="text-green-600 ml-2">✓ Valid selection</span>
                  )}
                </p>
              </div>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vividly-blue-600"></div>
              </div>
            )}

            {/* Display Mode */}
            {!isLoading && !isEditing && (
              <div className="flex flex-wrap gap-2">
                {interests.map((interest) => {
                  const category = interest.category || 'other'
                  const colors = categoryColors[category] || categoryColors.other
                  return (
                    <div
                      key={interest.interest_id}
                      className={`px-4 py-2 rounded-lg ${colors.bg} ${colors.text} ${colors.border} border`}
                    >
                      {interest.name}
                    </div>
                  )
                })}
                {interests.length === 0 && (
                  <p className="text-muted-foreground">No interests selected</p>
                )}
              </div>
            )}

            {/* Edit Mode */}
            {!isLoading && isEditing && (
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
                            disabled={!isSelected && selectedIds.length >= 5}
                            className={`
                              p-3 rounded-lg border-2 text-left transition-all duration-200
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
                              <div className="flex-1">
                                <p
                                  className={`font-medium text-sm ${isSelected ? colors.text : 'text-foreground'}`}
                                >
                                  {interest.name}
                                </p>
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
          </CardContent>
          {isEditing && (
            <CardFooter className="border-t border-border flex justify-end gap-3">
              <Button variant="secondary" onClick={handleCancel} disabled={isSaving}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSave}
                disabled={selectedIds.length < 2 || selectedIds.length > 5 || isSaving}
              >
                {isSaving ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </span>
                ) : (
                  'Save Changes'
                )}
              </Button>
            </CardFooter>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}

export default StudentProfile
