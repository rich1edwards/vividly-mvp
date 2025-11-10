/**
 * Super Admin API Client
 *
 * API client for super admin operations:
 * - System-wide metrics and analytics
 * - Request monitoring
 * - Organization overview
 * - Cache statistics
 * - Content delivery analytics
 * - Notification metrics
 */

import apiClient from './client'

/**
 * System Metrics Types
 */
export interface SystemMetrics {
  total_requests: number
  active_requests: number
  completed_requests: number
  failed_requests: number
  avg_confidence: {
    nlu: number
    matching: number
    rag: number
    script: number
    tts: number
    video: number
  }
  stage_distribution: {
    [stage: string]: number
  }
}

export interface AdminStats {
  total_users: number
  total_students: number
  total_teachers: number
  total_admins: number
  active_users_today: number
  total_classes: number
  total_content: number
}

export interface CacheStats {
  total_keys: number
  total_size_mb: number
  hit_rate: number
  miss_rate: number
  eviction_count: number
  memory_usage_percent: number
  keys_by_type: {
    [type: string]: number
  }
}

export interface DeliveryStats {
  total_deliveries: number
  successful_deliveries: number
  failed_deliveries: number
  avg_delivery_time_ms: number
  deliveries_by_status: {
    [status: string]: number
  }
}

export interface ContentAnalytics {
  total_content: number
  content_by_type: {
    video: number
    audio: number
    text: number
  }
  content_by_status: {
    pending: number
    processing: number
    completed: number
    failed: number
  }
  avg_generation_time_seconds: number
  popular_topics: Array<{
    topic: string
    count: number
  }>
}

export interface NotificationMetrics {
  total_sent: number
  total_delivered: number
  total_failed: number
  delivery_rate: number
  notifications_by_type: {
    [type: string]: number
  }
  recent_notifications: Array<{
    notification_id: string
    user_id: string
    type: string
    status: string
    created_at: string
  }>
}

/**
 * Request Monitoring Types
 */
export interface ActiveRequest {
  request_id: string
  student_id: string
  student_email: string
  current_stage: string
  status: string
  elapsed_seconds: number
  confidence_scores: {
    [stage: string]: number
  }
  created_at: string
  updated_at: string
}

export interface RequestFlow {
  found: boolean
  request_id: string
  events: Array<{
    stage: string
    status: string
    confidence: number
    timestamp: string
    metadata?: Record<string, any>
  }>
}

/**
 * Time Series Data Types (for charts)
 */
export interface TimeSeriesDataPoint {
  timestamp: string
  value: number
  label?: string
}

export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string
    fill?: boolean
  }>
}

/**
 * Super Admin API Client
 */
export const superAdminApi = {
  /**
   * Get comprehensive system metrics
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await apiClient.get('/api/v1/monitoring/metrics')
    return response.data
  },

  /**
   * Get admin statistics
   */
  async getAdminStats(): Promise<AdminStats> {
    const response = await apiClient.get('/api/v1/admin/stats')
    return response.data
  },

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<CacheStats> {
    const response = await apiClient.get('/api/v1/cache/stats')
    return response.data
  },

  /**
   * Get content delivery statistics
   */
  async getDeliveryStats(): Promise<DeliveryStats> {
    const response = await apiClient.get('/api/v1/content/delivery/stats')
    return response.data
  },

  /**
   * Get content analytics
   */
  async getContentAnalytics(params?: {
    start_date?: string
    end_date?: string
  }): Promise<ContentAnalytics> {
    const response = await apiClient.get('/api/v1/content/analytics', { params })
    return response.data
  },

  /**
   * Get notification metrics
   */
  async getNotificationMetrics(): Promise<NotificationMetrics> {
    const response = await apiClient.get('/api/v1/notifications/metrics')
    return response.data
  },

  /**
   * Get all active requests
   */
  async getActiveRequests(params?: {
    student_id?: string
    limit?: number
  }): Promise<ActiveRequest[]> {
    const response = await apiClient.get('/api/v1/monitoring/requests', { params })
    return response.data
  },

  /**
   * Get request flow details
   */
  async getRequestFlow(requestId: string): Promise<RequestFlow> {
    const response = await apiClient.get(`/api/v1/monitoring/requests/${requestId}`)
    return response.data
  },

  /**
   * Search requests by student
   */
  async searchRequests(params: {
    student_email?: string
    student_id?: string
    limit?: number
  }): Promise<ActiveRequest[]> {
    const response = await apiClient.get('/api/v1/monitoring/search', { params })
    return response.data
  },

  /**
   * Health check for monitoring service
   */
  async monitoringHealthCheck(): Promise<{ status: string; service: string }> {
    const response = await apiClient.get('/api/v1/monitoring/health')
    return response.data
  },

  /**
   * Aggregate all metrics (helper function for dashboard)
   */
  async getAllMetrics(): Promise<{
    system: SystemMetrics
    admin: AdminStats
    cache: CacheStats
    delivery: DeliveryStats
    content: ContentAnalytics
    notifications: NotificationMetrics
  }> {
    const [system, admin, cache, delivery, content, notifications] = await Promise.all([
      this.getSystemMetrics(),
      this.getAdminStats(),
      this.getCacheStats(),
      this.getDeliveryStats(),
      this.getContentAnalytics(),
      this.getNotificationMetrics(),
    ])

    return {
      system,
      admin,
      cache,
      delivery,
      content,
      notifications,
    }
  },
}
