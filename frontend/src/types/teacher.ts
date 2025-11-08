/**
 * Teacher API Types (Phase 2.2)
 *
 * TypeScript types matching backend schemas for teacher-related features.
 * Based on backend/app/schemas/teacher.py
 *
 * Updated: 2025-01-08 (Phase 2.2)
 */

// ============================================================================
// Class Types (matches backend ClassResponse)
// ============================================================================

export interface ClassResponse {
  class_id: string
  teacher_id: string
  name: string
  subject?: string
  class_code: string
  description?: string
  grade_levels?: number[]
  school_id?: string
  organization_id?: string
  created_at: string
  updated_at: string
  archived: boolean
}

export interface ClassSummary {
  class_id: string
  name: string
  subject?: string
  class_code: string
  student_count: number
  archived: boolean
  created_at: string
}

export interface UpdateClassRequest {
  name?: string
  subject?: string
  description?: string
  grade_levels?: number[]
}

// Legacy type for backwards compatibility
export interface Class extends ClassResponse {}

// ============================================================================
// Student & Roster Types (matches backend schemas)
// ============================================================================

export interface StudentInRoster {
  user_id: string
  email: string
  first_name: string
  last_name: string
  grade_level?: number
  enrolled_at: string
  progress_summary?: {
    videos_requested?: number
    videos_watched?: number
    avg_watch_time?: number
    last_active?: string
  }
}

export interface RosterResponse {
  class_id: string
  class_name: string
  total_students: number
  students: StudentInRoster[]
}

// Legacy type for backwards compatibility
export interface StudentInClass extends StudentInRoster {}
export interface ClassRoster {
  class_id: string
  students: StudentInClass[]
}

// ============================================================================
// Dashboard Types (matches backend TeacherDashboard)
// ============================================================================

export interface TeacherDashboard {
  teacher_id: string
  total_classes: number
  active_classes: number
  total_students: number
  pending_requests: number
  classes: ClassSummary[]
  recent_activity?: Activity[]
}

export interface Activity {
  activity_id: string
  type: 'content_request' | 'video_completion' | 'student_joined' | 'interest_change'
  user_id: string
  user_name: string
  class_id?: string
  class_name?: string
  description: string
  timestamp: string
  metadata?: Record<string, any>
}

// Legacy type for backwards compatibility
export interface TeacherDashboardStats extends Omit<TeacherDashboard, 'teacher_id' | 'active_classes' | 'pending_requests'> {
  total_content_requests: number
  active_students_today: number
  recent_classes: Class[]
  recent_student_activity: Array<{
    student_name: string
    class_name: string
    activity: string
    timestamp: string
  }>
}

// ============================================================================
// Class Metrics Types (for dashboard cards)
// ============================================================================

export interface ClassMetrics {
  class_id: string
  total_students: number
  content_requests_this_week: number
  avg_completion_rate: number
  active_now: number
  recent_requests: ContentRequestSummary[]
}

export interface ContentRequestSummary {
  request_id: string
  student_name: string
  student_id: string
  query: string
  status: 'pending' | 'generating' | 'completed' | 'failed'
  created_at: string
  estimated_completion?: string
}

// ============================================================================
// Student Account Request Types
// ============================================================================

export interface StudentAccountRequestCreate {
  student_email: string
  student_first_name: string
  student_last_name: string
  grade_level: number
  class_id?: string
  notes?: string
}

export interface BulkStudentAccountRequest {
  students: StudentAccountRequestCreate[]
}

export interface StudentAccountRequestResponse {
  request_id: string
  requested_by: string
  student_email: string
  student_first_name: string
  student_last_name: string
  grade_level: number
  class_id?: string
  status: 'pending' | 'approved' | 'rejected'
  requested_at: string
  processed_at?: string
  created_user_id?: string
}

// ============================================================================
// Student Detail Types
// ============================================================================

export interface StudentDetail {
  user_id: string
  email: string
  first_name: string
  last_name: string
  grade_level?: number
  profile_picture?: string
  interests: string[]
  joined_at: string
  classes: {
    class_id: string
    class_name: string
    enrolled_at: string
  }[]
  metrics: {
    content_requests: number
    videos_watched: number
    avg_watch_time: number // seconds
    favorite_topics: string[]
  }
  activity_timeline: StudentActivity[]
}

export interface StudentActivity {
  activity_id: string
  type: 'content_request' | 'video_completion' | 'interest_change' | 'login'
  description: string
  timestamp: string
  metadata?: Record<string, any>
}

// Legacy type for backwards compatibility
export interface StudentProgress {
  user_id: string
  student_name: string
  total_content: number
  completed_content: number
  total_watch_time: number
  average_score?: number
  last_activity: string
  interests: string[]
}

// ============================================================================
// Bulk Content Request Types
// ============================================================================

export interface BulkContentRequest {
  student_ids: string[]
  query: string
  topic?: string
  subject?: string
  schedule?: {
    generate_now: boolean
    scheduled_for?: string
  }
  notify_students: boolean
}

export interface BulkContentRequestResponse {
  batch_id: string
  total_requests: number
  successful: number
  failed: number
  request_ids: string[]
  failures?: {
    student_id: string
    student_name: string
    error: string
  }[]
}

// ============================================================================
// Analytics Types
// ============================================================================

export interface ClassAnalytics {
  class_id: string
  class_name?: string
  date_range: {
    start: string
    end: string
  }
  content_requests_over_time: {
    date: string
    count: number
  }[]
  videos_by_topic: {
    topic: string
    count: number
  }[]
  completion_rates: {
    completed: number
    in_progress: number
    not_started: number
  }
  student_engagement_trend: {
    date: string
    active_students: number
    avg_watch_time: number
  }[]
  top_students: {
    user_id: string
    name: string
    videos_watched: number
    engagement_score: number
  }[]
  // Legacy fields for backwards compatibility
  total_students?: number
  active_students?: number
  total_content_requests?: number
  total_videos_watched?: number
  average_engagement?: number
  top_topics?: Array<{ topic: string; count: number }>
  recent_activity?: Array<{
    student_name: string
    activity: string
    timestamp: string
  }>
}

// ============================================================================
// UI State Types (for frontend state management)
// ============================================================================

export interface TeacherDashboardState {
  selectedClassId?: string
  selectedTab: 'students' | 'requests' | 'library' | 'analytics'
  filters: {
    searchQuery: string
    statusFilter?: 'all' | 'active' | 'pending' | 'completed'
    dateRange?: {
      start: Date
      end: Date
    }
  }
  selectedStudents: string[]
  loading: boolean
  error?: string
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface ApiResponse<T> {
  data: T
  message?: string
  timestamp: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
