/**
 * Video Player Page
 *
 * Video playback page with Plyr.js integration
 */

import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { CenteredLoading } from '../../components/ui/Loading'
import { useToast } from '../../hooks/useToast'
import { contentApi } from '../../api/content'
import type { GeneratedContent } from '../../types'
import Plyr from 'plyr'
import 'plyr/dist/plyr.css'

export const VideoPlayerPage: React.FC = () => {
  const { cacheKey } = useParams<{ cacheKey: string }>()
  const navigate = useNavigate()
  const { error: showError } = useToast()
  const videoRef = useRef<HTMLVideoElement>(null)
  const playerRef = useRef<Plyr | null>(null)

  const [content, setContent] = useState<GeneratedContent | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (cacheKey) {
      loadContent(cacheKey)
    }

    // Cleanup Plyr instance on unmount
    return () => {
      if (playerRef.current) {
        playerRef.current.destroy()
      }
    }
  }, [cacheKey])

  useEffect(() => {
    // Initialize Plyr when video source is loaded
    if (videoRef.current && content?.video_url && !playerRef.current) {
      playerRef.current = new Plyr(videoRef.current, {
        controls: [
          'play-large',
          'play',
          'progress',
          'current-time',
          'duration',
          'mute',
          'volume',
          'settings',
          'fullscreen'
        ],
        settings: ['quality', 'speed'],
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
        quality: { default: 720, options: [1080, 720, 480, 360] }
      })
    }
  }, [content])

  const loadContent = async (key: string) => {
    try {
      setIsLoading(true)
      const data = await contentApi.getContent(key)
      setContent(data)
    } catch (error: any) {
      showError('Failed to load video', error.response?.data?.detail || 'Please try again')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <DashboardLayout>
        <CenteredLoading message="Loading video..." />
      </DashboardLayout>
    )
  }

  if (!content) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
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
          <h2 className="text-2xl font-bold text-foreground mb-2">Video Not Found</h2>
          <p className="text-muted-foreground mb-6">
            This video may have been removed or the link is invalid
          </p>
          <Button onClick={() => navigate('/student/videos')}>
            Back to My Videos
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link to="/student/dashboard" className="hover:text-foreground transition-colors">
            Dashboard
          </Link>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <Link to="/student/videos" className="hover:text-foreground transition-colors">
            My Videos
          </Link>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-foreground font-medium">Video Player</span>
        </nav>

        {/* Video Player */}
        <Card>
          <CardContent className="p-0">
            <video
              ref={videoRef}
              className="w-full"
              crossOrigin="anonymous"
              playsInline
            >
              <source src={content.video_url} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </CardContent>
        </Card>

        {/* Video Information */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <CardTitle className="text-2xl mb-2">{content.query}</CardTitle>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>
                        {new Date(content.created_at).toLocaleDateString('en-US', {
                          month: 'long',
                          day: 'numeric',
                          year: 'numeric'
                        })}
                      </span>
                      <span>•</span>
                      <span className="capitalize">{content.status}</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              {(content.topic || content.subject) && (
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {content.topic && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full bg-vividly-blue-100 text-vividly-blue-700 text-sm font-medium">
                        {content.topic}
                      </span>
                    )}
                    {content.subject && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full bg-vividly-purple-100 text-vividly-purple-700 text-sm font-medium">
                        {content.subject}
                      </span>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>

            {/* Transcript */}
            {content.transcript && (
              <Card>
                <CardHeader>
                  <CardTitle>Transcript</CardTitle>
                  <CardDescription>Full text of the video content</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none text-foreground">
                    {content.transcript.split('\n').map((paragraph, index) => (
                      <p key={index} className="mb-4 last:mb-0">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="primary"
                  fullWidth
                  onClick={() => navigate('/student/content/request')}
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  }
                >
                  Request New Content
                </Button>
                <Button
                  variant="tertiary"
                  fullWidth
                  onClick={() => navigate('/student/videos')}
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                  }
                >
                  Back to Videos
                </Button>
              </CardContent>
            </Card>

            {/* Metadata */}
            <Card>
              <CardHeader>
                <CardTitle>Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <div className="text-muted-foreground mb-1">Cache Key</div>
                  <div className="font-mono text-xs bg-muted p-2 rounded break-all">
                    {content.cache_key}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1">Created</div>
                  <div className="font-medium">
                    {new Date(content.created_at).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
                {content.completed_at && (
                  <div>
                    <div className="text-muted-foreground mb-1">Completed</div>
                    <div className="font-medium">
                      {new Date(content.completed_at).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default VideoPlayerPage
