import apiClient from './client'
import { ENDPOINTS } from './config'

export interface PipelineEvent {
  request_id: string
  student_id: string
  stage: string
  status: string
  confidence_score: number | null
  metadata: Record<string, any>
  error: string | null
  timestamp: string
}

export interface RequestFlow {
  request_id: string
  found: boolean
  student_id?: string
  current_stage?: string
  status?: string
  events?: PipelineEvent[]
  started_at?: string
  elapsed_seconds?: number
  total_stages?: number
  metadata?: Record<string, any>
}

export interface SystemMetrics {
  total_requests: number
  active_requests: number
  completed_requests: number
  failed_requests: number
  stage_counts: Record<string, number>
  avg_confidence_scores: Record<string, number>
  cache_size: number
  timestamp: string
}

export const monitoringApi = {
  // Get all active requests
  async getActiveRequests(studentId?: string, limit: number = 100): Promise<RequestFlow[]> {
    const params = new URLSearchParams()
    if (studentId) params.append('student_id', studentId)
    params.append('limit', limit.toString())

    const response = await apiClient.get<RequestFlow[]>(
      `${ENDPOINTS.MONITORING}/requests?${params.toString()}`
    )
    return response.data
  },

  // Get specific request flow
  async getRequestFlow(requestId: string): Promise<RequestFlow> {
    const response = await apiClient.get<RequestFlow>(
      `${ENDPOINTS.MONITORING}/requests/${requestId}`
    )
    return response.data
  },

  // Search by student email or ID
  async searchRequests(
    studentEmail?: string,
    studentId?: string,
    limit: number = 50
  ): Promise<RequestFlow[]> {
    const params = new URLSearchParams()
    if (studentEmail) params.append('student_email', studentEmail)
    if (studentId) params.append('student_id', studentId)
    params.append('limit', limit.toString())

    const response = await apiClient.get<RequestFlow[]>(
      `${ENDPOINTS.MONITORING}/search?${params.toString()}`
    )
    return response.data
  },

  // Get system metrics
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await apiClient.get<SystemMetrics>(`${ENDPOINTS.MONITORING}/metrics`)
    return response.data
  },
}
