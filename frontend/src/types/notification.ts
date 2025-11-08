/**
 * Notification Types
 *
 * TypeScript interfaces for real-time notification system (Phase 1.4)
 */

export enum NotificationEventType {
  CONTENT_GENERATION_STARTED = 'content_generation_started',
  CONTENT_GENERATION_PROGRESS = 'content_generation_progress',
  CONTENT_GENERATION_COMPLETED = 'content_generation_completed',
  CONTENT_GENERATION_FAILED = 'content_generation_failed',
}

export interface NotificationPayload {
  event_type: NotificationEventType
  content_request_id: string
  title: string
  message: string
  progress_percentage: number
  metadata?: Record<string, any>
  timestamp?: string
}

export interface Notification extends NotificationPayload {
  id: string
  received_at: string
  read: boolean
}

export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  ERROR = 'error',
}

export interface NotificationHookState {
  notifications: Notification[]
  connectionState: ConnectionState
  error: Error | null
  unreadCount: number
}

export interface NotificationHookActions {
  markAsRead: (notificationId: string) => void
  markAllAsRead: () => void
  clearNotification: (notificationId: string) => void
  clearAll: () => void
  reconnect: () => void
}

export type UseNotificationsReturn = NotificationHookState & NotificationHookActions
