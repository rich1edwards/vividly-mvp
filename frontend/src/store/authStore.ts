/**
 * Auth Store (Zustand)
 *
 * Global state management for authentication
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '../api'
import type {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterData,
  AuthState
} from '../types'

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  setUser: (user: User | null) => void
  setTokens: (tokens: AuthTokens | null) => void
  setError: (error: string | null) => void
  clearError: () => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: authApi.getStoredUser(),
      tokens: null,
      isAuthenticated: authApi.isAuthenticated(),
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null })

        try {
          const { user, tokens } = await authApi.login(credentials)

          set({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail ||
            error.message ||
            'Login failed. Please check your credentials.'

          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage
          })

          throw error
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null })

        try {
          const { user, tokens } = await authApi.register(data)

          set({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail ||
            error.message ||
            'Registration failed. Please try again.'

          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage
          })

          throw error
        }
      },

      logout: async () => {
        set({ isLoading: true, error: null })

        try {
          await authApi.logout()
        } catch (error) {
          // Continue with logout even if API call fails
          console.error('Logout API error:', error)
        } finally {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          })
        }
      },

      checkAuth: async () => {
        const storedUser = authApi.getStoredUser()
        const isAuthenticated = authApi.isAuthenticated()

        if (!isAuthenticated) {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false
          })
          return
        }

        // If we have stored user data, use it
        if (storedUser) {
          set({
            user: storedUser,
            isAuthenticated: true,
            isLoading: false
          })

          // Optionally, validate with backend in background
          try {
            const user = await authApi.getMe()
            set({ user })
          } catch (error) {
            console.error('Auth check failed:', error)
            // Token might be expired, logout
            await get().logout()
          }
        } else {
          // No stored user but have tokens, fetch user
          set({ isLoading: true })
          try {
            const user = await authApi.getMe()
            set({
              user,
              isAuthenticated: true,
              isLoading: false
            })
          } catch (error) {
            console.error('Failed to fetch user:', error)
            await get().logout()
          }
        }
      },

      setUser: (user: User | null) => {
        set({ user })
      },

      setTokens: (tokens: AuthTokens | null) => {
        set({ tokens })
      },

      setError: (error: string | null) => {
        set({ error })
      },

      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'vividly-auth-store',
      partialize: (state) => ({
        // Only persist user and isAuthenticated
        // Tokens are stored in localStorage by authApi
        user: state.user,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)
