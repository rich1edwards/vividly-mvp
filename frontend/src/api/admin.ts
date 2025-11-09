/**
 * Admin API Client
 *
 * API client for admin operations:
 * - User management (list, create, update, delete)
 * - Bulk user uploads
 * - Account request approval/denial
 * - Dashboard statistics
 */

import { apiClient } from './client'

/**
 * User Management Types
 */
export interface UserCreate {
  email: string
  first_name: string
  last_name: string
  role: 'student' | 'teacher' | 'admin'
  grade_level?: number
  school_id?: string
  organization_id?: string
  send_invitation?: boolean
}

export interface UserUpdate {
  role?: 'student' | 'teacher' | 'admin'
  grade_level?: number
  subjects?: string[]
  first_name?: string
  last_name?: string
}

export interface UserResponse {
  user_id: string
  email: string
  first_name: string
  last_name: string
  role: string
  grade_level?: number
  school_id?: string
  organization_id?: string
  is_active: boolean
  created_at: string
  last_login_at?: string
}

export interface UserListResponse {
  users: UserResponse[]
  pagination: {
    has_more: boolean
    next_cursor?: string
    total?: number
  }
}

/**
 * Bulk Upload Types
 */
export interface BulkUploadResponse {
  upload_id: string
  total_rows: number
  successful: number
  failed: number
  duration_seconds: number
  results: {
    successful_users?: UserResponse[]
    failed_rows?: Array<{
      row_number: number
      data: Record<string, any>
      errors: string[]
    }>
  }
}

/**
 * Account Request Types
 */
export interface AccountRequest {
  request_id: string
  student_first_name: string
  student_last_name: string
  student_email: string
  grade_level: number
  class_id?: string
  class_name?: string
  requested_by_id: string
  requested_by_name: string
  requested_at: string
  notes?: string
  status: 'pending' | 'approved' | 'denied'
}

export interface RequestListResponse {
  requests: AccountRequest[]
  pagination: {
    has_more: boolean
    total?: number
  }
}

export interface ApproveRequestResponse {
  request_id: string
  status: string
  user_created: UserResponse
  approved_at: string
  approved_by: string
  invitation_sent: boolean
}

export interface DenyRequestRequest {
  reason: string
}

export interface DenyRequestResponse {
  request_id: string
  status: string
  denied_at: string
  denied_by: string
  denial_reason: string
  teacher_notified: boolean
}

/**
 * Dashboard Stats Types
 */
export interface AdminStats {
  total_users: number
  total_students: number
  total_teachers: number
  total_admins: number
  active_users_today: number
  total_classes: number
  total_content: number
}

/**
 * Admin API Client
 */
export const adminApi = {
  /**
   * List users with filtering and pagination
   */
  async listUsers(params?: {
    role?: string
    school_id?: string
    search?: string
    limit?: number
    cursor?: string
  }): Promise<UserListResponse> {
    const response = await apiClient.get('/api/v1/admin/users', { params })
    return response.data
  },

  /**
   * Create a single user
   */
  async createUser(data: UserCreate): Promise<UserResponse> {
    const response = await apiClient.post('/api/v1/admin/users', data)
    return response.data
  },

  /**
   * Update user profile
   */
  async updateUser(userId: string, data: UserUpdate): Promise<UserResponse> {
    const response = await apiClient.put(`/api/v1/admin/users/${userId}`, data)
    return response.data
  },

  /**
   * Delete (deactivate) a user
   */
  async deleteUser(userId: string): Promise<void> {
    await apiClient.delete(`/api/v1/admin/users/${userId}`)
  },

  /**
   * Get admin dashboard statistics
   */
  async getStats(): Promise<AdminStats> {
    const response = await apiClient.get('/api/v1/admin/stats')
    return response.data
  },

  /**
   * Bulk upload users from CSV
   */
  async bulkUploadUsers(
    file: File,
    transactionMode: 'partial' | 'atomic' = 'partial'
  ): Promise<BulkUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('transaction_mode', transactionMode)

    const response = await apiClient.post('/api/v1/admin/users/bulk-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * List pending account requests
   */
  async listPendingRequests(params?: {
    school_id?: string
    teacher_id?: string
    limit?: number
  }): Promise<RequestListResponse> {
    const response = await apiClient.get('/api/v1/admin/requests', { params })
    return response.data
  },

  /**
   * Get account request details
   */
  async getRequestDetails(requestId: string): Promise<AccountRequest> {
    const response = await apiClient.get(`/api/v1/admin/requests/${requestId}`)
    return response.data
  },

  /**
   * Approve an account request
   */
  async approveRequest(requestId: string): Promise<ApproveRequestResponse> {
    const response = await apiClient.post(`/api/v1/admin/requests/${requestId}/approve`)
    return response.data
  },

  /**
   * Deny an account request
   */
  async denyRequest(
    requestId: string,
    data: DenyRequestRequest
  ): Promise<DenyRequestResponse> {
    const response = await apiClient.post(`/api/v1/admin/requests/${requestId}/deny`, data)
    return response.data
  },
}
