/**
 * Content API Service
 *
 * API methods for content generation and retrieval
 */

import apiClient from './client'
import { ENDPOINTS } from './config'
import type {
  Interest,
  ContentResponse,
  GeneratedContent,
  AsyncContentRequest,
  AsyncContentResponse,
  ContentRequestStatus
} from '../types'

export const contentApi = {
  /**
   * Get all available interests
   */
  async getInterests(): Promise<Interest[]> {
    const response = await apiClient.get<Interest[]>('/interests')
    return response.data
  },

  /**
   * Get student's selected interests
   */
  async getStudentInterests(): Promise<Interest[]> {
    const response = await apiClient.get<Interest[]>(ENDPOINTS.STUDENT_INTERESTS)
    return response.data
  },

  /**
   * Update student's interests (1-5 required)
   */
  async updateStudentInterests(interestIds: string[]): Promise<Interest[]> {
    const response = await apiClient.put<Interest[]>(
      ENDPOINTS.STUDENT_INTERESTS,
      { interest_ids: interestIds }
    )
    return response.data
  },

  /**
   * Request new content generation
   */
  async generateContent(data: {
    query: string
    topic?: string
    subject?: string
  }): Promise<ContentResponse> {
    const response = await apiClient.post<ContentResponse>(
      ENDPOINTS.CONTENT_GENERATE,
      data
    )
    return response.data
  },

  /**
   * Check content generation status
   */
  async getContentStatus(cacheKey: string): Promise<ContentResponse> {
    const response = await apiClient.get<ContentResponse>(
      ENDPOINTS.CONTENT_STATUS(cacheKey)
    )
    return response.data
  },

  /**
   * Get generated content by cache key
   */
  async getContent(cacheKey: string): Promise<GeneratedContent> {
    const response = await apiClient.get<GeneratedContent>(
      ENDPOINTS.CONTENT_VIDEO(cacheKey)
    )
    return response.data
  },

  /**
   * Get student's content history
   */
  async getContentHistory(): Promise<GeneratedContent[]> {
    const response = await apiClient.get<GeneratedContent[]>(ENDPOINTS.CONTENT_HISTORY)
    return response.data
  },

  /**
   * Respond to clarification request
   */
  async respondToClarification(data: {
    request_id: string
    clarified_query: string
    topic?: string
  }): Promise<ContentResponse> {
    const response = await apiClient.post<ContentResponse>(
      '/content/clarify',
      data
    )
    return response.data
  },

  /**
   * Request async content generation (202 Accepted)
   * Returns immediately with request_id for polling
   */
  async generateContentAsync(data: AsyncContentRequest): Promise<AsyncContentResponse> {
    const response = await apiClient.post<AsyncContentResponse>(
      ENDPOINTS.CONTENT_GENERATE,
      data
    )
    return response.data
  },

  /**
   * Poll content request status
   * Use this to track progress of async content generation
   */
  async getRequestStatus(requestId: string): Promise<ContentRequestStatus> {
    const response = await apiClient.get<ContentRequestStatus>(
      ENDPOINTS.CONTENT_REQUEST_STATUS(requestId)
    )
    return response.data
  }
}
