/**
 * Authentication Types
 *
 * TypeScript interfaces for authentication-related data structures
 */

export enum UserRole {
  STUDENT = 'student',
  TEACHER = 'teacher',
  ADMIN = 'admin',                    // Organization/School Admin (scoped to their org)
  SUPER_ADMIN = 'super_admin'         // Vividly Platform Admin (full system access)
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended'
}

export interface User {
  user_id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  status: UserStatus
  grade_level?: number                // For students
  school_id?: string                  // School/org affiliation
  organization_id?: string            // For admins - their managed organization
  created_at: string
  updated_at: string
}

// Helper to check if user has admin privileges
export const isAdmin = (role: UserRole): boolean => {
  return role === UserRole.ADMIN || role === UserRole.SUPER_ADMIN
}

// Helper to check if user is super admin
export const isSuperAdmin = (role: UserRole): boolean => {
  return role === UserRole.SUPER_ADMIN
}

// Helper to check if user is organization admin
export const isOrgAdmin = (role: UserRole): boolean => {
  return role === UserRole.ADMIN
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
  role: UserRole
  grade_level?: number
  school_id?: string
}

export interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}
