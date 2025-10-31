/**
 * Content Types
 *
 * TypeScript interfaces for content generation and video-related data structures
 */

export interface Interest {
  interest_id: string
  name: string
  category: string
  description?: string
}

export interface Topic {
  topic_id: string
  name: string
  subject: string
  grade_level: number
  description?: string
}

export interface ContentRequest {
  request_id: string
  student_id: string
  query: string
  topic?: string
  interests: string[]
  status: ContentRequestStatus
  created_at: string
  updated_at: string
}

export enum ContentRequestStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  REQUIRES_CLARIFICATION = 'requires_clarification'
}

export interface ClarificationRequest {
  request_id: string
  reason: string
  message: string
  suggestions: string[]
}

export interface ContentResponse {
  cache_key?: string
  status: 'needs_clarification' | 'processing' | 'completed' | 'failed' | 'clarification_needed' | 'cached' | 'generating' | 'ready'
  clarification?: ClarificationRequest
  clarification_request?: ClarificationRequest
  estimated_time?: number
  video_url?: string
  script?: string
  audio_url?: string
  message?: string
}

export interface GeneratedContent {
  cache_key: string
  query: string
  topic?: string
  subject?: string
  interests: string[]
  script: string
  transcript?: string
  audio_url?: string
  video_url?: string
  thumbnail_url?: string
  duration?: number
  status?: 'processing' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  views?: number
}

export interface ContentMetadata {
  cache_key: string
  topic: string
  subject: string
  grade_level: number
  interests: string[]
  created_at: string
  last_accessed: string
  access_count: number
}
