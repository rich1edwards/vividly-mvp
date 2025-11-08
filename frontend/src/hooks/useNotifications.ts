/**
 * useNotifications Hook (Phase 1.4)
 *
 * React hook for real-time notification system using Server-Sent Events (SSE).
 * Manages notification state, connection lifecycle, and automatic reconnection.
 *
 * Architecture:
 * - Establishes SSE connection to /api/v1/notifications/stream
 * - Receives real-time notifications from push_worker via Redis Pub/Sub
 * - Manages connection state (connecting, connected, disconnected, error)
 * - Implements exponential backoff reconnection strategy
 * - Persists notifications in Zustand store for global access
 * - Provides actions for marking as read, clearing notifications
 *
 * Usage:
 * ```tsx
 * const {
 *   notifications,
 *   connectionState,
 *   unreadCount,
 *   markAsRead,
 *   markAllAsRead,
 *   clearAll
 * } = useNotifications()
 * ```
 */

import { useEffect, useCallback, useRef } from 'react'
import { create } from 'zustand'
import { API_URL, ACCESS_TOKEN_KEY } from '../api/config'
import {
  Notification,
  NotificationPayload,
  ConnectionState,
  UseNotificationsReturn,
} from '../types/notification'

// SSE endpoint
const SSE_ENDPOINT = `${API_URL}/notifications/stream`

// Reconnection configuration
const INITIAL_RETRY_DELAY = 1000 // 1 second
const MAX_RETRY_DELAY = 30000 // 30 seconds
const MAX_RETRY_ATTEMPTS = 10
const RETRY_DELAY_MULTIPLIER = 1.5

// Notification store state interface
interface NotificationStore {
  notifications: Notification[]
  connectionState: ConnectionState
  error: Error | null
  addNotification: (payload: NotificationPayload) => void
  markAsRead: (notificationId: string) => void
  markAllAsRead: () => void
  clearNotification: (notificationId: string) => void
  clearAll: () => void
  setConnectionState: (state: ConnectionState) => void
  setError: (error: Error | null) => void
}

// Zustand store for notifications (with localStorage persistence for notifications only)
const useNotificationStore = create<NotificationStore>((set) => {
  // Load notifications from localStorage on initialization
  const storedNotifications = localStorage.getItem('vividly-notifications')
  const initialNotifications: Notification[] = storedNotifications
    ? JSON.parse(storedNotifications)
    : []

  return {
    notifications: initialNotifications,
    connectionState: ConnectionState.DISCONNECTED,
    error: null,

    addNotification: (payload: NotificationPayload) => {
      const notification: Notification = {
        ...payload,
        id: `${payload.content_request_id}-${Date.now()}`,
        received_at: new Date().toISOString(),
        read: false,
      }

      set((state) => {
        const newNotifications = [notification, ...state.notifications].slice(0, 50) // Keep max 50
        // Persist to localStorage
        localStorage.setItem('vividly-notifications', JSON.stringify(newNotifications))
        return { notifications: newNotifications }
      })
    },

    markAsRead: (notificationId: string) => {
      set((state) => {
        const newNotifications = state.notifications.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        )
        localStorage.setItem('vividly-notifications', JSON.stringify(newNotifications))
        return { notifications: newNotifications }
      })
    },

    markAllAsRead: () => {
      set((state) => {
        const newNotifications = state.notifications.map((n) => ({ ...n, read: true }))
        localStorage.setItem('vividly-notifications', JSON.stringify(newNotifications))
        return { notifications: newNotifications }
      })
    },

    clearNotification: (notificationId: string) => {
      set((state) => {
        const newNotifications = state.notifications.filter((n) => n.id !== notificationId)
        localStorage.setItem('vividly-notifications', JSON.stringify(newNotifications))
        return { notifications: newNotifications }
      })
    },

    clearAll: () => {
      localStorage.removeItem('vividly-notifications')
      set({ notifications: [] })
    },

    setConnectionState: (connectionState: ConnectionState) => {
      set({ connectionState })
    },

    setError: (error: Error | null) => {
      set({ error })
    },
  }
})

/**
 * Custom hook for managing real-time notifications via SSE
 */
export function useNotifications(): UseNotificationsReturn {
  const store = useNotificationStore()
  const eventSourceRef = useRef<EventSource | null>(null)
  const retryCountRef = useRef(0)
  const retryTimeoutRef = useRef<number | null>(null)
  const isManualDisconnectRef = useRef(false)

  /**
   * Calculate exponential backoff delay for reconnection
   */
  const getRetryDelay = useCallback((): number => {
    const delay = Math.min(
      INITIAL_RETRY_DELAY * Math.pow(RETRY_DELAY_MULTIPLIER, retryCountRef.current),
      MAX_RETRY_DELAY
    )
    return delay
  }, [])

  /**
   * Establish SSE connection to backend
   */
  const connect = useCallback(() => {
    // Don't reconnect if manually disconnected
    if (isManualDisconnectRef.current) {
      return
    }

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (!token) {
      console.warn('[useNotifications] No auth token found, skipping SSE connection')
      store.setConnectionState(ConnectionState.DISCONNECTED)
      return
    }

    store.setConnectionState(ConnectionState.CONNECTING)
    store.setError(null)

    try {
      // EventSource doesn't support custom headers, so we pass token as query param
      // Backend validates this token in the SSE endpoint
      const sseUrl = `${SSE_ENDPOINT}?token=${encodeURIComponent(token)}`
      const eventSource = new EventSource(sseUrl)
      eventSourceRef.current = eventSource

      // Connection established
      eventSource.onopen = () => {
        console.log('[useNotifications] SSE connection established')
        store.setConnectionState(ConnectionState.CONNECTED)
        store.setError(null)
        retryCountRef.current = 0 // Reset retry count on successful connection
      }

      // Receive notification event
      eventSource.addEventListener('notification', (event: MessageEvent) => {
        try {
          const payload: NotificationPayload = JSON.parse(event.data)
          console.log('[useNotifications] Received notification:', payload.event_type)
          store.addNotification(payload)
        } catch (error) {
          console.error('[useNotifications] Failed to parse notification:', error)
        }
      })

      // Heartbeat event (keep-alive)
      eventSource.addEventListener('heartbeat', (event: MessageEvent) => {
        console.debug('[useNotifications] Heartbeat received:', event.data)
      })

      // Connection error
      eventSource.onerror = (error) => {
        console.error('[useNotifications] SSE error:', error)
        store.setConnectionState(ConnectionState.ERROR)
        store.setError(new Error('SSE connection error'))
        eventSource.close()
        eventSourceRef.current = null

        // Attempt reconnection with exponential backoff
        if (retryCountRef.current < MAX_RETRY_ATTEMPTS && !isManualDisconnectRef.current) {
          const delay = getRetryDelay()
          console.log(
            `[useNotifications] Reconnecting in ${delay}ms (attempt ${retryCountRef.current + 1}/${MAX_RETRY_ATTEMPTS})`
          )

          retryTimeoutRef.current = setTimeout(() => {
            retryCountRef.current++
            connect()
          }, delay)
        } else if (retryCountRef.current >= MAX_RETRY_ATTEMPTS) {
          console.error('[useNotifications] Max retry attempts reached, giving up')
          store.setError(new Error('Max reconnection attempts reached'))
        }
      }
    } catch (error) {
      console.error('[useNotifications] Failed to create EventSource:', error)
      store.setConnectionState(ConnectionState.ERROR)
      store.setError(error as Error)
    }
  }, [store, getRetryDelay])

  /**
   * Disconnect SSE connection
   */
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    store.setConnectionState(ConnectionState.DISCONNECTED)
  }, [store])

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    isManualDisconnectRef.current = false
    retryCountRef.current = 0
    disconnect()
    connect()
  }, [connect, disconnect])

  // Establish connection on mount, clean up on unmount
  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // Calculate unread count
  const unreadCount = store.notifications.filter((n) => !n.read).length

  return {
    notifications: store.notifications,
    connectionState: store.connectionState,
    error: store.error,
    unreadCount,
    markAsRead: store.markAsRead,
    markAllAsRead: store.markAllAsRead,
    clearNotification: store.clearNotification,
    clearAll: store.clearAll,
    reconnect,
  }
}
