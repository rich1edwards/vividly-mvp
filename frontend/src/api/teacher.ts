/**
 * Teacher API Service
 *
 * API methods for teacher class and student management
 */

import apiClient from './client'
import { ENDPOINTS } from './config'
import type {
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
  }
}
