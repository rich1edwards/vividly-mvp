/**
 * Student Videos Page
 *
 * Browse and manage student's content history
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout'
import { Card, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { CenteredLoading } from '../../components/ui/Loading'
import { useToast } from '../../hooks/useToast'
import { contentApi } from '../../api/content'
import type { GeneratedContent } from '../../types'

export const StudentVideosPage: React.FC = () => {
  const navigate = useNavigate()
  const { error: showError } = useToast()

  const [videos, setVideos] = useState<GeneratedContent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'processing' | 'failed'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadVideos()
  }, [])

  const loadVideos = async () => {
    try {
      setIsLoading(true)
      const data = await contentApi.getContentHistory()
      setVideos(data)
    } catch (error: any) {
      showError('Failed to load videos', error.response?.data?.detail || 'Please try again')
    } finally {
      setIsLoading(false)
    }
  }

  const filteredVideos = videos.filter((video) => {
    // Status filter
    if (filterStatus !== 'all' && video.status !== filterStatus) {
      return false
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        video.query.toLowerCase().includes(query) ||
        video.topic?.toLowerCase().includes(query) ||
        video.subject?.toLowerCase().includes(query)
      )
    }

    return true
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-vividly-green-100 text-vividly-green-700'
      case 'processing':
        return 'bg-vividly-blue-100 text-vividly-blue-700'
      case 'failed':
        return 'bg-vividly-red-100 text-vividly-red-700'
      default:
        return 'bg-muted text-muted-foreground'
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">My Videos</h1>
            <p className="text-muted-foreground mt-2">
              {videos.length} video{videos.length !== 1 ? 's' : ''} in your library
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => navigate('/student/content/request')}
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            }
          >
            Request Content
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search videos..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full h-10 pl-10 pr-4 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  <svg
                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
              </div>

              {/* Status Filter */}
              <div className="flex gap-2">
                {(['all', 'completed', 'processing', 'failed'] as const).map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilterStatus(status)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize ${
                      filterStatus === status
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Videos List */}
        {isLoading ? (
          <CenteredLoading message="Loading videos..." />
        ) : filteredVideos.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  {searchQuery || filterStatus !== 'all' ? 'No videos found' : 'No videos yet'}
                </h3>
                <p className="text-muted-foreground mb-6">
                  {searchQuery || filterStatus !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Request your first video to get started!'}
                </p>
                {!searchQuery && filterStatus === 'all' && (
                  <Button variant="primary" onClick={() => navigate('/student/content/request')}>
                    Request Content
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredVideos.map((video) => (
              <Card
                key={video.cache_key}
                variant="elevated"
                interactive
                onClick={() => {
                  if (video.status === 'completed') {
                    navigate(`/student/videos/${video.cache_key}`)
                  }
                }}
              >
                <div className="flex items-start gap-6 p-6">
                  {/* Thumbnail/Icon */}
                  <div className="flex-shrink-0">
                    <div className="w-32 h-24 rounded-lg bg-gradient-to-br from-vividly-blue to-vividly-purple flex items-center justify-center">
                      {video.status === 'completed' ? (
                        <svg
                          className="w-12 h-12 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      ) : video.status === 'processing' ? (
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                      ) : (
                        <svg
                          className="w-12 h-12 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      )}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <h3 className="text-lg font-semibold text-foreground line-clamp-2">
                        {video.query}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getStatusColor(
                          video.status || 'completed'
                        )}`}
                      >
                        {video.status || 'completed'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground mb-3">
                      <span>
                        {new Date(video.created_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric'
                        })}
                      </span>
                      {(video.topic || video.subject) && (
                        <>
                          <span>•</span>
                          <div className="flex gap-2">
                            {video.topic && (
                              <span className="px-2 py-0.5 rounded bg-vividly-blue-100 text-vividly-blue-700 text-xs">
                                {video.topic}
                              </span>
                            )}
                            {video.subject && (
                              <span className="px-2 py-0.5 rounded bg-vividly-purple-100 text-vividly-purple-700 text-xs">
                                {video.subject}
                              </span>
                            )}
                          </div>
                        </>
                      )}
                    </div>

                    {video.status === 'completed' && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/student/videos/${video.cache_key}`)
                        }}
                        leftIcon={
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                        }
                      >
                        Watch Video
                      </Button>
                    )}
                    {video.status === 'processing' && (
                      <p className="text-sm text-muted-foreground">
                        Your video is being generated. This usually takes 30-60 seconds.
                      </p>
                    )}
                    {video.status === 'failed' && (
                      <p className="text-sm text-vividly-red-600">
                        Generation failed. Please try requesting content again.
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

export default StudentVideosPage
