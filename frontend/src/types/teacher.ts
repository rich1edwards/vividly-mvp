/**
 * Teacher Types
 *
 * TypeScript interfaces for teacher, class, and student management
 */

export interface Class {
  class_id: string
  name: string
  subject: string
  grade_level: number
  teacher_id: string
  school_id: string
  description?: string
  student_count?: number
  created_at: string
  updated_at: string
}

export interface ClassRoster {
  class_id: string
  students: StudentInClass[]
}

export interface StudentInClass {
  user_id: string
  email: string
  first_name: string
  last_name: string
  grade_level?: number
  enrolled_at: string
  last_active?: string
  content_count?: number
  total_watch_time?: number
}

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

export interface ClassAnalytics {
  class_id: string
  class_name: string
  total_students: number
  active_students: number
  total_content_requests: number
  total_videos_watched: number
  average_engagement: number
  top_topics: Array<{ topic: string; count: number }>
  recent_activity: Array<{
    student_name: string
    activity: string
    timestamp: string
  }>
}

export interface TeacherDashboardStats {
  total_classes: number
  total_students: number
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
