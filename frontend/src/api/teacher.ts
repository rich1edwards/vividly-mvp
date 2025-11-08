/**
 * Teacher API Service (Phase 2.2)
 *
 * API methods for teacher class and student management
 * Updated: 2025-01-08 - Added Phase 2.2 endpoints
 */

import apiClient from './client'
import { ENDPOINTS } from './config'
import type {
  // New Phase 2.2 types
  TeacherDashboard,
  ClassResponse,
  ClassSummary,
  RosterResponse,
  StudentInRoster,
  UpdateClassRequest,
  ClassMetrics,
  StudentDetail,
  BulkContentRequest,
  BulkContentRequestResponse,
  // Legacy types (backwards compatibility)
  Class,
  ClassRoster,
  StudentInClass,
  StudentProgress,
  ClassAnalytics,
  TeacherDashboardStats
} from '../types'

export const teacherApi = {
  /**
   * Get all classes for the teacher
   */
  async getClasses(): Promise<Class[]> {
    const response = await apiClient.get<Class[]>(ENDPOINTS.TEACHER_CLASSES)
    return response.data
  },

  /**
   * Get details for a specific class
   */
  async getClassDetail(classId: string): Promise<Class> {
    const response = await apiClient.get<Class>(ENDPOINTS.TEACHER_CLASS_DETAIL(classId))
    return response.data
  },

  /**
   * Get roster for a specific class
   */
  async getClassRoster(classId: string): Promise<ClassRoster> {
    const response = await apiClient.get<ClassRoster>(
      ENDPOINTS.TEACHER_CLASS_ROSTER(classId)
    )
    return response.data
  },

  /**
   * Get all students across teacher's classes
   */
  async getStudents(): Promise<StudentInClass[]> {
    const response = await apiClient.get<StudentInClass[]>(ENDPOINTS.TEACHER_STUDENTS)
    return response.data
  },

  /**
   * Get student progress details
   */
  async getStudentProgress(studentId: string): Promise<StudentProgress> {
    const response = await apiClient.get<StudentProgress>(
      `/teachers/students/${studentId}/progress`
    )
    return response.data
  },

  /**
   * Get class analytics
   */
  async getClassAnalytics(classId: string): Promise<ClassAnalytics> {
    const response = await apiClient.get<ClassAnalytics>(
      `/teachers/classes/${classId}/analytics`
    )
    return response.data
  },

  /**
   * Get teacher dashboard stats
   */
  async getDashboardStats(): Promise<TeacherDashboardStats> {
    const response = await apiClient.get<TeacherDashboardStats>('/teachers/dashboard')
    return response.data
  },

  /**
   * Create a new class
   */
  async createClass(data: {
    name: string
    subject: string
    grade_level: number
    description?: string
  }): Promise<Class> {
    const response = await apiClient.post<Class>(ENDPOINTS.TEACHER_CLASSES, data)
    return response.data
  },

  /**
   * Update class details
   */
  async updateClass(
    classId: string,
    data: {
      name?: string
      subject?: string
      grade_level?: number
      description?: string
    }
  ): Promise<Class> {
    const response = await apiClient.put<Class>(
      ENDPOINTS.TEACHER_CLASS_DETAIL(classId),
      data
    )
    return response.data
  },

  /**
   * Delete a class
   */
  async deleteClass(classId: string): Promise<void> {
    await apiClient.delete(ENDPOINTS.TEACHER_CLASS_DETAIL(classId))
  },

  /**
   * Add students to a class
   */
  async addStudentsToClass(
    classId: string,
    studentIds: string[]
  ): Promise<ClassRoster> {
    const response = await apiClient.post<ClassRoster>(
      `${ENDPOINTS.TEACHER_CLASS_ROSTER(classId)}/add`,
      { student_ids: studentIds }
    )
    return response.data
  },

  /**
   * Remove student from class
   */
  async removeStudentFromClass(classId: string, studentId: string): Promise<void> {
    await apiClient.delete(`${ENDPOINTS.TEACHER_CLASS_ROSTER(classId)}/${studentId}`)
  },

  // ============================================================================
  // Phase 2.2: New Dashboard & Class Management APIs
  // ============================================================================

  /**
   * Get teacher dashboard data (Phase 2.2)
   * Matches backend GET /teachers/{teacher_id}/dashboard
   */
  async getTeacherDashboard(teacherId: string): Promise<TeacherDashboard> {
    const response = await apiClient.get<TeacherDashboard>(
      `/api/v1/teachers/${teacherId}/dashboard`
    )
    return response.data
  },

  /**
   * Get class details (Phase 2.2)
   * Matches backend GET /classes/{class_id}
   */
  async getClass(classId: string): Promise<ClassResponse> {
    const response = await apiClient.get<ClassResponse>(
      `/api/v1/classes/${classId}`
    )
    return response.data
  },

  /**
   * Update class (Phase 2.2)
   * Matches backend PATCH /classes/{class_id}
   */
  async patchClass(classId: string, data: UpdateClassRequest): Promise<ClassResponse> {
    const response = await apiClient.patch<ClassResponse>(
      `/api/v1/classes/${classId}`,
      data
    )
    return response.data
  },

  /**
   * Archive class (Phase 2.2)
   * Matches backend DELETE /classes/{class_id}
   */
  async archiveClass(classId: string): Promise<ClassResponse> {
    const response = await apiClient.delete<ClassResponse>(
      `/api/v1/classes/${classId}`
    )
    return response.data
  },

  /**
   * Get class roster (Phase 2.2)
   * Matches backend GET /classes/{class_id}/students
   */
  async getRoster(classId: string): Promise<RosterResponse> {
    const response = await apiClient.get<RosterResponse>(
      `/api/v1/classes/${classId}/students`
    )
    return response.data
  },

  /**
   * Get class metrics for dashboard cards (Phase 2.2)
   * NOTE: This endpoint needs to be implemented in backend
   */
  async getClassMetrics(classId: string): Promise<ClassMetrics> {
    const response = await apiClient.get<ClassMetrics>(
      `/api/v1/classes/${classId}/metrics`
    )
    return response.data
  },

  /**
   * Get student details (Phase 2.3)
   * NOTE: This endpoint needs to be implemented in backend
   */
  async getStudentDetail(studentId: string): Promise<StudentDetail> {
    const response = await apiClient.get<StudentDetail>(
      `/api/v1/students/${studentId}/detail`
    )
    return response.data
  },

  /**
   * Bulk content request for multiple students (Phase 2.4)
   * NOTE: This endpoint needs to be implemented in backend
   */
  async bulkContentRequest(
    classId: string,
    data: BulkContentRequest
  ): Promise<BulkContentRequestResponse> {
    const response = await apiClient.post<BulkContentRequestResponse>(
      `/api/v1/classes/${classId}/bulk-content-request`,
      data
    )
    return response.data
  },

  /**
   * Get class analytics (Phase 2.5)
   * Enhanced version with date range
   */
  async getAnalytics(
    classId: string,
    startDate?: string,
    endDate?: string
  ): Promise<ClassAnalytics> {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)

    const url = `/api/v1/classes/${classId}/analytics${
      params.toString() ? `?${params.toString()}` : ''
    }`

    const response = await apiClient.get<ClassAnalytics>(url)
    return response.data
  },

  /**
   * Export class data to CSV (Phase 2.5)
   * NOTE: This endpoint needs to be implemented in backend
   */
  async exportClassData(
    classId: string,
    dataType: 'roster' | 'analytics' | 'requests'
  ): Promise<Blob> {
    const response = await apiClient.get(
      `/api/v1/classes/${classId}/export/${dataType}`,
      {
        responseType: 'blob',
      }
    )
    return response.data
  },
}
