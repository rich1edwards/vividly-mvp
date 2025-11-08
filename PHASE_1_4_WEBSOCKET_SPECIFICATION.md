# Phase 1.4: WebSocket Push Notifications - Technical Specification

**Status**: PENDING - Requires Backend Implementation
**Priority**: Medium (Can be deferred post-MVP)
**Estimated Effort**: 2-3 days (Backend: 1.5 days, Frontend: 0.5-1 day)
**Created**: Session 12 Part 4

---

## Executive Summary

Phase 1.4 implements real-time push notifications to inform students when their video content generation is complete. This feature enhances UX by eliminating the need for manual page refreshes and provides instant feedback on long-running async operations.

**Key Decision**: Use **Server-Sent Events (SSE)** instead of WebSockets for simpler unidirectional server-to-client push notifications.

---

## Architecture Overview

### Current State (Session 12)

```
Student submits content request
        ↓
Backend creates ContentRequest record (status="pending")
        ↓
Pub/Sub message published to "vividly-content-requests"
        ↓
Push Worker (Cloud Run Service) receives message
        ↓
Content Worker generates video (NLU → RAG → Script → TTS → Video)
        ↓
ContentRequest updated in database (status="completed")
        ↓
❌ Student must manually refresh to see completion
```

### Target State (Phase 1.4)

```
Student submits content request
        ↓
Frontend establishes SSE connection to /api/v1/notifications/stream/{user_id}
        ↓
Backend creates ContentRequest record (status="pending")
        ↓
Pub/Sub message published
        ↓
Push Worker generates video
        ↓
ContentRequest updated (status="completed")
        ↓
✅ Backend publishes notification to Redis/Pub-Sub
        ↓
✅ SSE endpoint sends event to connected clients
        ↓
✅ Frontend receives notification → shows toast → updates UI
```

---

## Technical Design

### 1. Backend Implementation

#### 1.1 Notification Service

**File**: `backend/app/services/notification_service.py` (NEW FILE - ~200 lines)

```python
"""
Notification Service

Handles real-time notifications via Server-Sent Events (SSE).
Uses Redis Pub/Sub for distributed notification delivery across Cloud Run instances.
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from redis.asyncio import Redis
from fastapi import Request

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Manages real-time notifications using Server-Sent Events.

    Architecture:
    - Redis Pub/Sub for inter-instance messaging
    - SSE for client connections
    - Each user has a dedicated Redis channel: notifications:{user_id}
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.active_connections: Dict[str, set] = {}  # user_id -> set of connection IDs

    async def publish_notification(
        self,
        user_id: str,
        notification_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Publish notification to user's channel.

        Notification Types:
        - video_complete: Video generation finished
        - video_failed: Video generation failed
        - clarification_needed: Need user input for clarification

        Args:
            user_id: Target user ID
            notification_type: Type of notification
            payload: Notification data (content_id, title, etc.)

        Returns:
            True if published successfully
        """
        try:
            notification = {
                "type": notification_type,
                "user_id": user_id,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            }

            channel = f"notifications:{user_id}"
            await self.redis.publish(channel, json.dumps(notification))

            logger.info(
                f"Published {notification_type} notification to user {user_id}",
                extra={"user_id": user_id, "type": notification_type}
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to publish notification: {e}",
                extra={"user_id": user_id, "type": notification_type}
            )
            return False

    async def subscribe_user_notifications(
        self,
        user_id: str,
        request: Request
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to user's notification stream (SSE endpoint).

        Yields SSE-formatted messages:
        data: {"type":"video_complete","payload":{...},"timestamp":"..."}

        Args:
            user_id: User to subscribe to
            request: FastAPI request (for disconnection detection)

        Yields:
            SSE-formatted notification strings
        """
        pubsub = self.redis.pubsub()
        channel = f"notifications:{user_id}"

        try:
            await pubsub.subscribe(channel)
            logger.info(f"User {user_id} subscribed to notifications")

            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Listen for messages with timeout
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=30.0  # 30s keepalive
                )

                if message and message["type"] == "message":
                    # Forward notification to client
                    yield f"data: {message['data'].decode('utf-8')}\n\n"
                else:
                    # Send keepalive ping
                    yield f": keepalive\n\n"

                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"SSE stream error for user {user_id}: {e}")

        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"User {user_id} unsubscribed from notifications")
```

**Dependencies**:
- `redis[hiredis]>=5.0.0` (async Redis client)
- Add to `requirements.txt`

**Redis Setup**:
- **Local Dev**: Use Docker: `docker run -d -p 6379:6379 redis:7-alpine`
- **GCP Production**: Use **Cloud Memorystore** (Redis):
  ```bash
  gcloud redis instances create vividly-notifications \
    --size=1 \
    --region=us-central1 \
    --tier=basic \
    --project=vividly-dev-rich
  ```

#### 1.2 SSE API Endpoint

**File**: `backend/app/api/v1/endpoints/notifications.py` (NEW FILE - ~100 lines)

```python
"""
Notifications API Endpoints
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.services.notification_service import NotificationService
from app.core.deps import get_current_user, get_redis_client
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/stream")
async def stream_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends()
):
    """
    Server-Sent Events endpoint for real-time notifications.

    Client usage:
    ```javascript
    const eventSource = new EventSource('/api/v1/notifications/stream');
    eventSource.onmessage = (event) => {
        const notification = JSON.parse(event.data);
        handleNotification(notification);
    };
    ```

    Returns:
        StreamingResponse with SSE events
    """
    return StreamingResponse(
        notification_service.subscribe_user_notifications(
            user_id=current_user.user_id,
            request=request
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable proxy buffering
        }
    )

@router.get("/history")
async def get_notification_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Get recent notification history for user.

    Returns:
        List of recent notifications (stored in database)
    """
    # TODO: Implement notification persistence in database
    pass
```

#### 1.3 Trigger Notifications from Content Worker

**File**: `backend/app/workers/push_worker.py` (MODIFY EXISTING - add ~20 lines)

```python
# Add to imports
from app.services.notification_service import NotificationService
from app.core.deps import get_redis_client

# In push_handler function, after video generation completes:

async def push_handler(request: Request):
    # ... existing code ...

    # After successful video generation
    if content_data:
        # Existing: Update ContentRequest in database
        # ...

        # NEW: Send push notification
        redis_client = await get_redis_client()
        notification_service = NotificationService(redis_client)

        await notification_service.publish_notification(
            user_id=message_data["student_id"],
            notification_type="video_complete",
            payload={
                "content_id": content_data["content_id"],
                "title": script_data.get("title", "Your video is ready!"),
                "video_url": video_url,
                "thumbnail_url": video_data.get("thumbnail_url"),
                "duration_seconds": video_data.get("duration_seconds"),
            }
        )
```

---

### 2. Frontend Implementation

#### 2.1 useNotifications Hook

**File**: `frontend/src/hooks/useNotifications.ts` (NEW FILE - ~150 lines)

```typescript
/**
 * useNotifications Hook
 *
 * Manages Server-Sent Events connection for real-time notifications.
 * Handles reconnection, error recovery, and notification state.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from './useAuth'
import { useToast } from './use-toast'

export interface Notification {
  type: 'video_complete' | 'video_failed' | 'clarification_needed' | 'connected'
  payload?: {
    content_id?: string
    title?: string
    video_url?: string
    thumbnail_url?: string
    duration_seconds?: number
    error_message?: string
  }
  timestamp: string
}

export interface UseNotificationsReturn {
  notifications: Notification[]
  isConnected: boolean
  unreadCount: number
  markAsRead: (notification: Notification) => void
  markAllAsRead: () => void
  clearAll: () => void
}

export const useNotifications = (): UseNotificationsReturn => {
  const { isAuthenticated, user } = useAuth()
  const { toast } = useToast()

  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)

  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY_MS = 2000

  // Connect to SSE endpoint
  const connect = useCallback(() => {
    if (!isAuthenticated || eventSourceRef.current) return

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${apiUrl}/api/v1/notifications/stream`

    console.log('[Notifications] Connecting to SSE endpoint:', url)

    const eventSource = new EventSource(url, {
      withCredentials: true  // Send auth cookies
    })

    eventSource.onopen = () => {
      console.log('[Notifications] Connected to SSE')
      setIsConnected(true)
      reconnectAttemptsRef.current = 0
    }

    eventSource.onmessage = (event) => {
      try {
        const notification: Notification = JSON.parse(event.data)

        console.log('[Notifications] Received:', notification)

        // Handle different notification types
        if (notification.type === 'video_complete') {
          // Show toast notification
          toast({
            title: "Video Ready!",
            description: notification.payload?.title || "Your video is ready to watch",
            action: {
              label: "Watch Now",
              onClick: () => {
                window.location.href = `/video/${notification.payload?.content_id}`
              }
            },
            duration: 10000  // 10 seconds
          })

          // Add to notification history
          setNotifications(prev => [notification, ...prev])
          setUnreadCount(prev => prev + 1)
        }

        if (notification.type === 'video_failed') {
          toast({
            title: "Video Generation Failed",
            description: notification.payload?.error_message || "Sorry, something went wrong",
            variant: "destructive",
            duration: 10000
          })

          setNotifications(prev => [notification, ...prev])
          setUnreadCount(prev => prev + 1)
        }

      } catch (error) {
        console.error('[Notifications] Failed to parse event:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('[Notifications] SSE error:', error)
      setIsConnected(false)
      eventSource.close()
      eventSourceRef.current = null

      // Attempt reconnection with exponential backoff
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current)
        console.log(`[Notifications] Reconnecting in ${delay}ms...`)

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++
          connect()
        }, delay)
      } else {
        console.error('[Notifications] Max reconnection attempts reached')
        toast({
          title: "Connection Lost",
          description: "Unable to receive notifications. Please refresh the page.",
          variant: "destructive"
        })
      }
    }

    eventSourceRef.current = eventSource
  }, [isAuthenticated, toast])

  // Disconnect from SSE
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setIsConnected(false)
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  // Mark notification as read
  const markAsRead = useCallback((notification: Notification) => {
    // TODO: Update read status in backend
    setUnreadCount(prev => Math.max(0, prev - 1))
  }, [])

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    // TODO: Update read status in backend
    setUnreadCount(0)
  }, [])

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([])
    setUnreadCount(0)
  }, [])

  return {
    notifications,
    isConnected,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAll
  }
}
```

#### 2.2 Notification Center Component

**File**: `frontend/src/components/NotificationCenter.tsx` (NEW FILE - ~200 lines)

```typescript
/**
 * Notification Center Component
 *
 * Bell icon in header with dropdown showing recent notifications.
 */
import React, { useState } from 'react'
import { Bell, Check, CheckCheck, Trash2, Video, AlertCircle } from 'lucide-react'
import { useNotifications } from '../hooks/useNotifications'
import { formatDistanceToNow } from 'date-fns'
import { Button } from './ui/Button'

export const NotificationCenter: React.FC = () => {
  const {
    notifications,
    isConnected,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAll
  } = useNotifications()

  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
      >
        <Bell className="w-6 h-6 text-gray-700" />

        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-vividly-red rounded-full">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}

        {/* Connection Status Indicator */}
        <span
          className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${
            isConnected ? 'bg-green-500' : 'bg-gray-400'
          }`}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[600px] flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Notifications</h3>
              <div className="flex gap-2">
                {notifications.length > 0 && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={markAllAsRead}
                      title="Mark all as read"
                    >
                      <CheckCheck className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearAll}
                      title="Clear all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Notifications List */}
          <div className="flex-1 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p>No notifications yet</p>
              </div>
            ) : (
              <ul>
                {notifications.map((notification, index) => (
                  <li
                    key={index}
                    className="p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <NotificationItem
                      notification={notification}
                      onMarkRead={() => markAsRead(notification)}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const NotificationItem: React.FC<{
  notification: any
  onMarkRead: () => void
}> = ({ notification, onMarkRead }) => {
  const getIcon = () => {
    if (notification.type === 'video_complete') return <Video className="w-5 h-5 text-green-600" />
    if (notification.type === 'video_failed') return <AlertCircle className="w-5 h-5 text-red-600" />
    return <Bell className="w-5 h-5 text-blue-600" />
  }

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 mt-1">
        {getIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">
          {notification.payload?.title || 'Notification'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
        </p>

        {notification.type === 'video_complete' && notification.payload?.video_url && (
          <Button
            variant="link"
            size="sm"
            className="mt-2 p-0 h-auto"
            onClick={() => {
              window.location.href = `/video/${notification.payload.content_id}`
            }}
          >
            Watch Now →
          </Button>
        )}
      </div>
      <button
        onClick={onMarkRead}
        className="flex-shrink-0 text-gray-400 hover:text-gray-600"
        title="Mark as read"
      >
        <Check className="w-4 h-4" />
      </button>
    </div>
  )
}
```

#### 2.3 Integration into App Layout

**File**: `frontend/src/components/Layout.tsx` (MODIFY EXISTING)

```typescript
// Add to imports
import { NotificationCenter } from './NotificationCenter'

// In header nav:
<nav className="flex items-center gap-4">
  {/* Existing nav items */}
  <NotificationCenter />
  {/* User menu, etc. */}
</nav>
```

---

## Infrastructure Requirements

### 1. Redis / Cloud Memorystore

**Development**:
```bash
docker run -d -p 6379:6379 --name vividly-redis redis:7-alpine
```

**Production (GCP)**:
```bash
# Create Cloud Memorystore instance
gcloud redis instances create vividly-notifications \
  --size=1 \
  --region=us-central1 \
  --tier=basic \
  --redis-version=redis_7_0 \
  --project=vividly-dev-rich

# Get connection info
gcloud redis instances describe vividly-notifications \
  --region=us-central1 \
  --project=vividly-dev-rich
```

**Environment Variables**:
```bash
# Add to backend .env
REDIS_HOST=10.x.x.x  # From gcloud describe output
REDIS_PORT=6379
```

### 2. Cloud Run Configuration

**Update**: `backend/cloudbuild.yaml`

Add VPC connector for Redis access:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'dev-vividly-api'
      - '--vpc-connector=vividly-vpc-connector'  # ADD THIS
      # ... existing args
```

---

## Testing Strategy

### Backend Tests

**File**: `backend/tests/test_notification_service.py`

```python
import pytest
from app.services.notification_service import NotificationService

@pytest.mark.asyncio
async def test_publish_notification(redis_client):
    service = NotificationService(redis_client)
    result = await service.publish_notification(
        user_id="test-user-123",
        notification_type="video_complete",
        payload={"content_id": "video-456"}
    )
    assert result is True

@pytest.mark.asyncio
async def test_subscribe_notifications(redis_client, mock_request):
    service = NotificationService(redis_client)

    # Subscribe in background
    async for event in service.subscribe_user_notifications(
        user_id="test-user-123",
        request=mock_request
    ):
        assert "data:" in event
        break  # Test first event only
```

### Frontend Tests

**File**: `frontend/src/hooks/__tests__/useNotifications.test.ts`

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useNotifications } from '../useNotifications'

describe('useNotifications', () => {
  it('should connect to SSE endpoint on mount', async () => {
    const { result } = renderHook(() => useNotifications())

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('should receive video_complete notification', async () => {
    const { result } = renderHook(() => useNotifications())

    // Simulate SSE event
    global.EventSource.mockMessageEvent({
      data: JSON.stringify({
        type: 'video_complete',
        payload: { title: 'Test Video', content_id: '123' }
      })
    })

    await waitFor(() => {
      expect(result.current.notifications).toHaveLength(1)
      expect(result.current.unreadCount).toBe(1)
    })
  })
})
```

---

## Deployment Checklist

### Backend Deployment

- [ ] Add `redis[hiredis]` to requirements.txt
- [ ] Create Redis instance in Cloud Memorystore
- [ ] Create VPC connector for Cloud Run → Redis access
- [ ] Update Cloud Run service with VPC connector
- [ ] Add REDIS_HOST and REDIS_PORT environment variables
- [ ] Deploy notification_service.py
- [ ] Deploy notifications API endpoint
- [ ] Update push_worker.py to publish notifications
- [ ] Test SSE endpoint with curl:
  ```bash
  curl -N -H "Authorization: Bearer $TOKEN" \
    https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/api/v1/notifications/stream
  ```

### Frontend Deployment

- [ ] Implement useNotifications hook
- [ ] Create NotificationCenter component
- [ ] Add NotificationCenter to app layout header
- [ ] Test SSE connection in browser DevTools (Network tab)
- [ ] Test notification toast display
- [ ] Test reconnection on network interruption
- [ ] Build and deploy frontend
- [ ] Verify CORS allows EventSource connections

### E2E Testing

- [ ] Submit content request
- [ ] Verify SSE connection established
- [ ] Wait for video generation (or use mock/test mode)
- [ ] Verify notification received in browser
- [ ] Verify toast displayed with correct title
- [ ] Click "Watch Now" → navigates to video page
- [ ] Verify notification appears in Notification Center
- [ ] Test "Mark as Read" functionality
- [ ] Test "Mark All as Read"
- [ ] Test "Clear All"
- [ ] Test multiple concurrent users
- [ ] Test reconnection after simulated disconnect

---

## Performance Considerations

### 1. Connection Limits

- **Cloud Run**: Default 1000 concurrent connections per instance
- **Redis**: Basic tier supports 10,000 connections
- **Scaling**: Cloud Run auto-scales based on concurrency

### 2. Message Throughput

- **Expected Load**: 10-20 notifications/second at MVP scale
- **Redis Capacity**: Pub/Sub can handle 50,000+ msg/s
- **Bottleneck**: None expected at MVP scale

### 3. Memory Usage

- **Per SSE Connection**: ~1-2 KB
- **1000 connections**: ~1-2 MB
- **Cloud Run Memory**: 512 MB default (sufficient)

### 4. Bandwidth

- **SSE Keepalive**: 30s interval, minimal (<50 bytes/msg)
- **Video Complete Event**: ~500 bytes
- **Expected**: <10 KB/s per connection

---

## Security Considerations

### 1. Authentication

- SSE endpoint requires valid JWT token
- Cookie-based auth: `withCredentials: true`
- Token validation on every SSE connection

### 2. Authorization

- Users only receive notifications for their own user_id
- Redis channels scoped by user: `notifications:{user_id}`

### 3. Rate Limiting

- Limit SSE connections per user: max 3 concurrent
- Disconnect stale connections after 5 minutes idle

### 4. Data Validation

- Sanitize all notification payloads
- Prevent XSS in notification titles/descriptions

---

## Alternative Approaches Considered

### 1. Polling (Rejected)

**Pros**: Simple, no persistent connections
**Cons**: Inefficient, delayed notifications (30-60s), higher server load

### 2. WebSockets (Rejected for Phase 1)

**Pros**: Bi-directional, lower latency
**Cons**: More complex, unnecessary for unidirectional push, harder to scale in Cloud Run

### 3. Firebase Cloud Messaging (Deferred to Phase 2)

**Pros**: Browser push notifications, works when tab closed
**Cons**: Requires service worker, user permission, more setup

### 4. **Server-Sent Events (SELECTED)**

**Pros**:
- Simple HTTP protocol
- Auto-reconnection built-in
- Efficient unidirectional push
- Works well with Cloud Run
- No browser permissions needed

**Cons**:
- Only server → client (sufficient for notifications)
- Some corporate firewalls block SSE (rare)

---

## Future Enhancements (Phase 2+)

1. **Persistent Notification History**
   - Store notifications in database
   - GET /api/v1/notifications/history endpoint
   - Pagination and filtering

2. **Notification Preferences**
   - User settings for notification types
   - Email digest option
   - Mute notifications

3. **Browser Push Notifications**
   - Service worker for offline notifications
   - Desktop notifications when tab not focused

4. **Analytics**
   - Track notification delivery rates
   - Measure click-through rates
   - A/B test notification copy

5. **Rich Notifications**
   - Video preview thumbnails
   - In-app action buttons
   - Quick reply for clarifications

---

## Estimated Timeline

### Backend (1.5 days)

- **Day 1 Morning**: Redis setup, NotificationService implementation
- **Day 1 Afternoon**: SSE endpoint, testing with curl
- **Day 2 Morning**: Integrate with push_worker, deploy to dev
- **Day 2 Afternoon**: E2E testing, debugging, production deployment

### Frontend (0.5-1 day)

- **Morning**: useNotifications hook, basic testing
- **Afternoon**: NotificationCenter component, integration, E2E testing

### Total: 2-3 days (with testing and deployment)

---

## Success Criteria

Phase 1.4 is complete when:

- [ ] Backend SSE endpoint (/api/v1/notifications/stream) deployed and working
- [ ] Redis Pub/Sub messaging functional
- [ ] Push worker publishes notifications on video completion
- [ ] Frontend useNotifications hook connects to SSE
- [ ] NotificationCenter shows notification history
- [ ] Toast notifications display for video_complete events
- [ ] "Watch Now" button navigates to correct video
- [ ] SSE reconnection works after network interruption
- [ ] No memory leaks with long-lived connections (24hr+ test)
- [ ] E2E test passes: submit request → receive notification → watch video
- [ ] Documentation updated in FRONTEND_UX_IMPLEMENTATION_PLAN.md

---

## References

- **Server-Sent Events**: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- **Redis Pub/Sub**: https://redis.io/docs/manual/pubsub/
- **Cloud Memorystore**: https://cloud.google.com/memorystore/docs/redis
- **FastAPI Streaming**: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- **EventSource API**: https://developer.mozilla.org/en-US/docs/Web/API/EventSource

---

**Created**: 2025-11-08
**Author**: Claude (Session 12 Part 4)
**Status**: SPECIFICATION - Ready for Implementation
