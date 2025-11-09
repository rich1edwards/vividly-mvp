/**
 * NotificationCenter Component (Phase 1.4)
 *
 * Real-time notification center UI component for content generation updates.
 * Displays notifications in a popover with connection status, read/unread states,
 * and action buttons for managing notifications.
 *
 * Features:
 * - Real-time SSE notifications via useNotifications hook
 * - Visual connection status indicator
 * - Unread count badge
 * - Mark as read/unread functionality
 * - Clear individual or all notifications
 * - Empty state handling
 * - Responsive design with mobile support
 * - Accessibility (ARIA labels, keyboard navigation)
 *
 * Usage:
 * ```tsx
 * import { NotificationCenter } from './components/NotificationCenter'
 *
 * function Header() {
 *   return (
 *     <header>
 *       <NotificationCenter />
 *     </header>
 *   )
 * }
 * ```
 */

import React from 'react'
import { Bell, Check, CheckCheck, Loader2, Trash2, WifiOff, X } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { useNotifications } from '../hooks/useNotifications'
import {
  ConnectionState,
  Notification,
  NotificationEventType,
} from '../types/notification'
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover'
import { Button } from './ui/Button'
import { Badge } from './ui/badge'
import { cn } from '../lib/utils'

/**
 * Get icon component for notification event type
 */
function getNotificationIcon(eventType: NotificationEventType) {
  switch (eventType) {
    case NotificationEventType.CONTENT_GENERATION_STARTED:
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    case NotificationEventType.CONTENT_GENERATION_PROGRESS:
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    case NotificationEventType.CONTENT_GENERATION_COMPLETED:
      return <CheckCheck className="h-4 w-4 text-green-500" />
    case NotificationEventType.CONTENT_GENERATION_FAILED:
      return <X className="h-4 w-4 text-red-500" />
    default:
      return <Bell className="h-4 w-4 text-gray-500" />
  }
}

/**
 * Get color classes for notification based on event type
 */
function getNotificationColor(eventType: NotificationEventType): string {
  switch (eventType) {
    case NotificationEventType.CONTENT_GENERATION_STARTED:
      return 'bg-blue-50 border-blue-200'
    case NotificationEventType.CONTENT_GENERATION_PROGRESS:
      return 'bg-blue-50 border-blue-200'
    case NotificationEventType.CONTENT_GENERATION_COMPLETED:
      return 'bg-green-50 border-green-200'
    case NotificationEventType.CONTENT_GENERATION_FAILED:
      return 'bg-red-50 border-red-200'
    default:
      return 'bg-gray-50 border-gray-200'
  }
}

/**
 * Individual notification item component
 */
interface NotificationItemProps {
  notification: Notification
  onMarkAsRead: (id: string) => void
  onClear: (id: string) => void
}

function NotificationItem({ notification, onMarkAsRead, onClear }: NotificationItemProps) {
  const Icon = getNotificationIcon(notification.event_type)
  const colorClass = getNotificationColor(notification.event_type)

  return (
    <div
      className={cn(
        'p-3 border rounded-lg transition-all duration-200',
        colorClass,
        !notification.read && 'shadow-sm'
      )}
      role="listitem"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-1">{Icon}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4
              className={cn(
                'text-sm font-medium text-gray-900',
                !notification.read && 'font-semibold'
              )}
            >
              {notification.title}
            </h4>
            {!notification.read && (
              <div className="h-2 w-2 rounded-full bg-vividly-blue flex-shrink-0 mt-1" />
            )}
          </div>

          <p className="text-sm text-gray-600 mt-1">{notification.message}</p>

          {/* Progress bar for in-progress notifications */}
          {notification.progress_percentage > 0 &&
            notification.progress_percentage < 100 && (
              <div className="mt-2">
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-vividly-blue transition-all duration-300"
                    style={{ width: `${notification.progress_percentage}%` }}
                    role="progressbar"
                    aria-valuenow={notification.progress_percentage}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`Content generation progress: ${notification.progress_percentage}%`}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1" aria-hidden="true">
                  {notification.progress_percentage}% complete
                </p>
              </div>
            )}

          {/* Timestamp */}
          <p className="text-xs text-gray-500 mt-2">
            {formatDistanceToNow(new Date(notification.received_at), {
              addSuffix: true,
            })}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {!notification.read && (
            <button
              onClick={() => onMarkAsRead(notification.id)}
              className="p-1 hover:bg-white/50 rounded transition-colors"
              title="Mark as read"
              aria-label="Mark notification as read"
            >
              <Check className="h-4 w-4 text-gray-600" />
            </button>
          )}
          <button
            onClick={() => onClear(notification.id)}
            className="p-1 hover:bg-white/50 rounded transition-colors"
            title="Clear notification"
            aria-label="Clear notification"
          >
            <Trash2 className="h-4 w-4 text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Connection status indicator component
 */
interface ConnectionStatusProps {
  connectionState: ConnectionState
  onReconnect: () => void
}

function ConnectionStatus({ connectionState, onReconnect }: ConnectionStatusProps) {
  switch (connectionState) {
    case ConnectionState.CONNECTED:
      return (
        <div
          className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg"
          role="status"
          aria-live="polite"
          aria-label="Notification connection status: Connected"
        >
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" aria-hidden="true" />
          <span className="text-xs text-green-700 font-medium">Connected</span>
        </div>
      )
    case ConnectionState.CONNECTING:
      return (
        <div
          className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg"
          role="status"
          aria-live="polite"
          aria-label="Notification connection status: Connecting"
        >
          <Loader2 className="h-3 w-3 text-blue-500 animate-spin" aria-hidden="true" />
          <span className="text-xs text-blue-700 font-medium">Connecting...</span>
        </div>
      )
    case ConnectionState.ERROR:
      return (
        <div
          className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg"
          role="alert"
          aria-live="assertive"
          aria-label="Notification connection status: Connection error"
        >
          <WifiOff className="h-3 w-3 text-red-500" aria-hidden="true" />
          <span className="text-xs text-red-700 font-medium">Connection error</span>
          <Button
            size="sm"
            variant="ghost"
            onClick={onReconnect}
            className="ml-auto h-6 px-2 text-xs"
            aria-label="Retry notification connection"
          >
            Retry
          </Button>
        </div>
      )
    case ConnectionState.DISCONNECTED:
      return (
        <div
          className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg"
          role="status"
          aria-live="polite"
          aria-label="Notification connection status: Disconnected"
        >
          <div className="h-2 w-2 rounded-full bg-gray-400" aria-hidden="true" />
          <span className="text-xs text-gray-700 font-medium">Disconnected</span>
          <Button
            size="sm"
            variant="ghost"
            onClick={onReconnect}
            className="ml-auto h-6 px-2 text-xs"
            aria-label="Connect to notifications"
          >
            Connect
          </Button>
        </div>
      )
    default:
      return null
  }
}

/**
 * Empty state component
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
      <div className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
        <Bell className="h-6 w-6 text-gray-400" />
      </div>
      <h3 className="text-sm font-medium text-gray-900 mb-1">No notifications</h3>
      <p className="text-xs text-gray-500">
        You'll see real-time updates when content is being generated
      </p>
    </div>
  )
}

/**
 * Main NotificationCenter component
 */
export function NotificationCenter() {
  const {
    notifications,
    connectionState,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAll,
    reconnect,
  } = useNotifications()

  const [isOpen, setIsOpen] = React.useState(false)
  const [latestNotification, setLatestNotification] = React.useState<Notification | null>(null)
  const prevNotificationCountRef = React.useRef(notifications.length)

  // Detect new notifications for screen reader announcement
  React.useEffect(() => {
    if (notifications.length > prevNotificationCountRef.current) {
      const newest = notifications[0] // Assuming newest first
      setLatestNotification(newest)

      // Clear after announcement
      const timer = setTimeout(() => setLatestNotification(null), 3000)
      return () => clearTimeout(timer)
    }
    prevNotificationCountRef.current = notifications.length
  }, [notifications])

  return (
    <>
      {/* ARIA Live Region for new notification announcements */}
      {latestNotification && (
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          New notification: {latestNotification.title}. {latestNotification.message}
        </div>
      )}

      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <button
            className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:ring-offset-2"
            aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
          >
            <Bell className="h-5 w-5 text-gray-700" />
            {unreadCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-1 -right-1 h-5 min-w-[20px] flex items-center justify-center px-1 text-xs"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </Badge>
            )}
          </button>
        </PopoverTrigger>

      <PopoverContent
        align="end"
        className="w-96 max-h-[600px] flex flex-col p-0"
        sideOffset={8}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold text-gray-900">Notifications</h2>
            {notifications.length > 0 && (
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={markAllAsRead}
                    className="h-7 px-2 text-xs"
                  >
                    Mark all read
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={clearAll}
                  className="h-7 px-2 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  Clear all
                </Button>
              </div>
            )}
          </div>

          {/* Connection Status */}
          <ConnectionStatus connectionState={connectionState} onReconnect={reconnect} />
        </div>

        {/* Notification List */}
        <div className="flex-1 overflow-y-auto">
          {notifications.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="p-3 space-y-2" role="list">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={markAsRead}
                  onClear={clearNotification}
                />
              ))}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
    </>
  )
}
