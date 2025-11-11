import apiClient from './client'
import { ENDPOINTS } from './config'

export interface Interest {
  interest_id: string
  name: string
  category: string | null
  description: string | null
  icon?: string | null
  display_order?: number | null
}

export interface StudentInterestsResponse {
  interests: Interest[]
  count: number
}

export interface SetInterestsRequest {
  interest_ids: string[]
}

export const interestsApi = {
  // Get all available interests
  async getAll(): Promise<Interest[]> {
    const response = await apiClient.get<Interest[]>(ENDPOINTS.INTERESTS)
    return response.data
  },

  // Get current student's interests
  async getMy(): Promise<StudentInterestsResponse> {
    const response = await apiClient.get<StudentInterestsResponse>(`${ENDPOINTS.INTERESTS}/me`)
    return response.data
  },

  // Set/update current student's interests
  async setMy(interestIds: string[]): Promise<StudentInterestsResponse> {
    const response = await apiClient.post<StudentInterestsResponse>(
      `${ENDPOINTS.INTERESTS}/me`,
      { interest_ids: interestIds }
    )
    return response.data
  },

  // Check if student has selected interests
  async hasSelected(): Promise<boolean> {
    const response = await apiClient.get<{ has_selected: boolean }>(
      `${ENDPOINTS.INTERESTS}/me/has-selected`
    )
    return response.data.has_selected
  },
}
