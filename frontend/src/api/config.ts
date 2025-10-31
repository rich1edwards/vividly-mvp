/**
 * API Configuration
 *
 * Centralized API configuration and constants
 */

// API Base URL - defaults to localhost for development
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// API Version
export const API_VERSION = 'v1'

// Full API URL
export const API_URL = `${API_BASE_URL}/api/${API_VERSION}`

// Token storage keys
export const ACCESS_TOKEN_KEY = 'vividly_access_token'
export const REFRESH_TOKEN_KEY = 'vividly_refresh_token'
export const USER_KEY = 'vividly_user'

// Request timeout (milliseconds)
export const REQUEST_TIMEOUT = 30000

// API Endpoints
export const ENDPOINTS = {
  // Auth
  AUTH_LOGIN: '/auth/login',
  AUTH_REGISTER: '/auth/register',
  AUTH_REFRESH: '/auth/refresh',
  AUTH_LOGOUT: '/auth/logout',
  AUTH_ME: '/auth/me',

  // Students
  STUDENT_INTERESTS: '/students/interests',
  STUDENT_PROFILE: '/students/profile',
  STUDENT_PROGRESS: '/students/progress',
  STUDENT_ACTIVITY: '/students/activity',

  // Content
  CONTENT_GENERATE: '/content/generate',
  CONTENT_STATUS: (cacheKey: string) => `/content/status/${cacheKey}`,
  CONTENT_VIDEO: (cacheKey: string) => `/content/video/${cacheKey}`,
  CONTENT_HISTORY: '/content/history',

  // Topics
  TOPICS_LIST: '/topics',
  TOPICS_BY_SUBJECT: (subject: string) => `/topics/subject/${subject}`,

  // Teachers
  TEACHER_CLASSES: '/teachers/classes',
  TEACHER_CLASS_DETAIL: (classId: string) => `/teachers/classes/${classId}`,
  TEACHER_CLASS_ROSTER: (classId: string) => `/teachers/classes/${classId}/roster`,
  TEACHER_STUDENTS: '/teachers/students',

  // Admin
  ADMIN_USERS: '/admin/users',
  ADMIN_REQUESTS: '/admin/requests',
  ADMIN_ANALYTICS: '/admin/analytics'
} as const
