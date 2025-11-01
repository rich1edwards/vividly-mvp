/**
 * Authentication API Service
 *
 * API methods for authentication operations
 */

import apiClient from './client'
import { ENDPOINTS, ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from './config'
import type { User, AuthTokens, LoginCredentials, RegisterData } from '../types'

export const authApi = {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> {
    console.log('[authApi] Login request starting', {
      email: credentials.email,
      endpoint: ENDPOINTS.AUTH_LOGIN
    })

    const response = await apiClient.post<AuthTokens>(ENDPOINTS.AUTH_LOGIN, {
      email: credentials.email,
      password: credentials.password
    })

    console.log('[authApi] Login response received', {
      status: response.status,
      hasAccessToken: !!response.data.access_token,
      hasRefreshToken: !!response.data.refresh_token
    })

    // Store tokens
    localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token)
    console.log('[authApi] Tokens stored in localStorage')

    // Fetch user profile
    console.log('[authApi] Fetching user profile from', ENDPOINTS.AUTH_ME)
    const userResponse = await apiClient.get<User>(ENDPOINTS.AUTH_ME)
    console.log('[authApi] User profile received', {
      userId: userResponse.data.user_id,
      email: userResponse.data.email,
      role: userResponse.data.role
    })

    localStorage.setItem(USER_KEY, JSON.stringify(userResponse.data))
    console.log('[authApi] User data stored in localStorage')

    return {
      user: userResponse.data,
      tokens: response.data
    }
  },

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<{ user: User; tokens: AuthTokens }> {
    await apiClient.post<User>(ENDPOINTS.AUTH_REGISTER, data)

    // After registration, login automatically
    return this.login({
      email: data.email,
      password: data.password
    })
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post(ENDPOINTS.AUTH_LOGOUT)
    } finally {
      // Always clear local storage, even if API call fails
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  },

  /**
   * Get current user profile
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>(ENDPOINTS.AUTH_ME)
    localStorage.setItem(USER_KEY, JSON.stringify(response.data))
    return response.data
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await apiClient.post<AuthTokens>(ENDPOINTS.AUTH_REFRESH, {
      refresh_token: refreshToken
    })

    localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token)
    if (response.data.refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token)
    }

    return response.data
  },

  /**
   * Check if user is authenticated (has valid tokens)
   */
  isAuthenticated(): boolean {
    return !!(
      localStorage.getItem(ACCESS_TOKEN_KEY) && localStorage.getItem(REFRESH_TOKEN_KEY)
    )
  },

  /**
   * Get stored user from localStorage
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem(USER_KEY)
    if (!userStr) return null

    try {
      return JSON.parse(userStr) as User
    } catch {
      return null
    }
  }
}
