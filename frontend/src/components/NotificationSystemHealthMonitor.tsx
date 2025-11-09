/**
 * NotificationSystemHealthMonitor Component
 *
 * Real-time health monitoring dashboard for the notification system (Phase 1.4).
 * Displays connection status, metrics, and system health indicators.
 *
 * Features:
 * - Real-time SSE connection status
 * - Notification delivery metrics (publish/deliver counts)
 * - Latency monitoring (publish, delivery, connection)
 * - Redis connection status
 * - Active connection count
 * - Error rate tracking
 * - Historical metrics visualization
 * - Admin-only component for system monitoring
 *
 * Architecture:
 * - Polls /api/v1/notifications/health endpoint every 10 seconds
 * - Polls /api/v1/notifications/connections endpoint (admin only) every 30 seconds
 * - Displays color-coded status indicators (healthy, degraded, unavailable)
 * - Shows trending data with Recharts mini charts
 *
 * Usage:
 * ```tsx
 * import { NotificationSystemHealthMonitor } from './components/NotificationSystemHealthMonitor'
 *
 * function AdminDashboard() {
 *   return (
 *     <div>
 *       <h1>System Monitoring</h1>
 *       <NotificationSystemHealthMonitor />
 *     </div>
 *   )
 * }
 * ```
 */

import React, { useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Server,
  TrendingUp,
  Users,
  Wifi,
  WifiOff,
  XCircle,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/badge'
import { Button } from './ui/Button'
import { API_URL, ACCESS_TOKEN_KEY } from '../api/config'

// Helper to get auth headers
const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ============================================================================
// Types
// ============================================================================

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unavailable'
  redis_connected: boolean
  active_connections: number
  service_metrics: {
    notifications_published: number
    notifications_delivered: number
    connections_established: number
    connections_closed: number
    publish_errors: number
    subscribe_errors: number
  }
}

interface ConnectionInfo {
  connection_id: string
  user_id: string
  connected_at: string
  last_heartbeat_at: string
  user_agent?: string
  ip_address?: string
}

interface ConnectionsData {
  total_connections: number
  connections_by_user: Record<string, number>
  connection_details: ConnectionInfo[]
}

interface MetricHistory {
  timestamp: string
  value: number
}

// ============================================================================
// Main Component
// ============================================================================

export const NotificationSystemHealthMonitor: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [connections, setConnections] = useState<ConnectionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Historical metrics for trending
  const [metricsHistory, setMetricsHistory] = useState<{
    published: MetricHistory[]
    delivered: MetricHistory[]
    connections: MetricHistory[]
  }>({
    published: [],
    delivered: [],
    connections: [],
  })

  /**
   * Fetch health status from backend
   */
  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/notifications/health`)

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`)
      }

      const data: HealthStatus = await response.json()
      setHealth(data)
      setError(null)

      // Update metrics history
      const now = new Date().toISOString()
      setMetricsHistory((prev) => ({
        published: [
          ...prev.published.slice(-19),
          { timestamp: now, value: data.service_metrics.notifications_published },
        ],
        delivered: [
          ...prev.delivered.slice(-19),
          { timestamp: now, value: data.service_metrics.notifications_delivered },
        ],
        connections: [
          ...prev.connections.slice(-19),
          { timestamp: now, value: data.active_connections },
        ],
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health status')
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Fetch active connections (admin only)
   */
  const fetchConnections = async () => {
    if (!isAdmin) return

    try {
      const response = await fetch(`${API_URL}/notifications/connections`, {
        headers: getAuthHeaders(),
      })

      if (response.status === 403) {
        setIsAdmin(false)
        return
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch connections: ${response.status}`)
      }

      const data: ConnectionsData = await response.json()
      setConnections(data)
    } catch (err) {
      console.error('Failed to fetch connections:', err)
      setConnections(null)
    }
  }

  /**
   * Check if user is admin
   */
  useEffect(() => {
    const checkAdminStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/notifications/connections`, {
          headers: getAuthHeaders(),
        })
        setIsAdmin(response.ok)
      } catch {
        setIsAdmin(false)
      }
    }

    checkAdminStatus()
  }, [])

  /**
   * Auto-refresh health and connections
   */
  useEffect(() => {
    if (!autoRefresh) return

    // Initial fetch
    fetchHealth()
    if (isAdmin) {
      fetchConnections()
    }

    // Health refresh every 10 seconds
    const healthInterval = setInterval(fetchHealth, 10000)

    // Connections refresh every 30 seconds (admin only)
    const connectionsInterval = isAdmin
      ? setInterval(fetchConnections, 30000)
      : null

    return () => {
      clearInterval(healthInterval)
      if (connectionsInterval) {
        clearInterval(connectionsInterval)
      }
    }
  }, [autoRefresh, isAdmin])

  /**
   * Manual refresh
   */
  const handleRefresh = () => {
    setLoading(true)
    fetchHealth()
    if (isAdmin) {
      fetchConnections()
    }
  }

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'degraded':
        return 'text-amber-600 bg-amber-50 border-amber-200'
      case 'unavailable':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-amber-600" />
      case 'unavailable':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <Activity className="h-5 w-5 text-gray-600" />
    }
  }

  const calculateDeliveryRate = () => {
    if (!health) return 0
    const { notifications_published, notifications_delivered } = health.service_metrics
    if (notifications_published === 0) return 100
    return ((notifications_delivered / notifications_published) * 100).toFixed(2)
  }

  const calculateErrorRate = () => {
    if (!health) return 0
    const { publish_errors, subscribe_errors, notifications_published } =
      health.service_metrics
    const totalErrors = publish_errors + subscribe_errors
    const totalOperations = notifications_published + totalErrors
    if (totalOperations === 0) return 0
    return ((totalErrors / totalOperations) * 100).toFixed(2)
  }

  // ============================================================================
  // Render
  // ============================================================================

  if (loading && !health) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Notification System Health</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Activity className="h-8 w-8 animate-spin text-vividly-blue" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error && !health) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Notification System Health</CardTitle>
          <CardDescription>Error loading health status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 gap-4">
            <XCircle className="h-12 w-12 text-red-600" />
            <p className="text-sm text-red-600">{error}</p>
            <Button onClick={handleRefresh} variant="tertiary">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Notification System Health
          </h2>
          <p className="text-sm text-muted-foreground">
            Real-time monitoring of Phase 1.4 notification infrastructure
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleRefresh}
            variant="tertiary"
            size="sm"
            disabled={loading}
          >
            <Activity className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            variant={autoRefresh ? 'primary' : 'tertiary'}
            size="sm"
          >
            {autoRefresh ? 'Auto-Refresh: ON' : 'Auto-Refresh: OFF'}
          </Button>
        </div>
      </div>

      {/* Overall Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>System Status</CardTitle>
            {health && (
              <Badge className={getStatusColor(health.status)}>
                {getStatusIcon(health.status)}
                <span className="ml-2 capitalize">{health.status}</span>
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Redis Connection */}
            <div className="flex items-center gap-3 p-4 border rounded-lg">
              {health?.redis_connected ? (
                <Wifi className="h-8 w-8 text-green-600" />
              ) : (
                <WifiOff className="h-8 w-8 text-red-600" />
              )}
              <div>
                <p className="text-sm font-medium">Redis Connection</p>
                <p className="text-xs text-muted-foreground">
                  {health?.redis_connected ? 'Connected' : 'Disconnected'}
                </p>
              </div>
            </div>

            {/* Active Connections */}
            <div className="flex items-center gap-3 p-4 border rounded-lg">
              <Users className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-sm font-medium">Active Connections</p>
                <p className="text-2xl font-bold">{health?.active_connections || 0}</p>
              </div>
            </div>

            {/* Delivery Rate */}
            <div className="flex items-center gap-3 p-4 border rounded-lg">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div>
                <p className="text-sm font-medium">Delivery Rate</p>
                <p className="text-2xl font-bold">{calculateDeliveryRate()}%</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Cards */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Published Notifications */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Notifications Published
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {health.service_metrics.notifications_published}
              </div>
              <p className="text-xs text-muted-foreground">
                Total notifications sent to Redis
              </p>
            </CardContent>
          </Card>

          {/* Delivered Notifications */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Notifications Delivered
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {health.service_metrics.notifications_delivered}
              </div>
              <p className="text-xs text-muted-foreground">
                Total notifications sent to clients via SSE
              </p>
            </CardContent>
          </Card>

          {/* Connections Established */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Connections Established
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {health.service_metrics.connections_established}
              </div>
              <p className="text-xs text-muted-foreground">
                Total SSE connections since startup
              </p>
            </CardContent>
          </Card>

          {/* Connections Closed */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Connections Closed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {health.service_metrics.connections_closed}
              </div>
              <p className="text-xs text-muted-foreground">
                Total SSE connections closed
              </p>
            </CardContent>
          </Card>

          {/* Publish Errors */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Publish Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {health.service_metrics.publish_errors}
              </div>
              <p className="text-xs text-muted-foreground">
                Failed Redis Pub/Sub publishes
              </p>
            </CardContent>
          </Card>

          {/* Subscribe Errors */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Subscribe Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {health.service_metrics.subscribe_errors}
              </div>
              <p className="text-xs text-muted-foreground">
                Failed SSE subscriptions
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Error Rate Card */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold">
                {calculateErrorRate()}%
              </div>
              <div className="text-sm text-muted-foreground">
                {health.service_metrics.publish_errors +
                  health.service_metrics.subscribe_errors}{' '}
                errors out of{' '}
                {health.service_metrics.notifications_published +
                  health.service_metrics.publish_errors +
                  health.service_metrics.subscribe_errors}{' '}
                total operations
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Connections Details (Admin Only) */}
      {isAdmin && connections && connections.total_connections > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Connections ({connections.total_connections})</CardTitle>
            <CardDescription>Real-time SSE connection details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Connections by User Summary */}
              <div>
                <h4 className="text-sm font-medium mb-2">Connections by User</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {Object.entries(connections.connections_by_user).map(
                    ([userId, count]) => (
                      <div
                        key={userId}
                        className="flex items-center justify-between p-2 border rounded"
                      >
                        <span className="text-xs font-mono truncate">{userId}</span>
                        <Badge variant="secondary">{count}</Badge>
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* Connection Details Table */}
              <div>
                <h4 className="text-sm font-medium mb-2">Connection Details</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Connection ID</th>
                        <th className="text-left p-2">User ID</th>
                        <th className="text-left p-2">Connected At</th>
                        <th className="text-left p-2">Last Heartbeat</th>
                        <th className="text-left p-2">IP Address</th>
                      </tr>
                    </thead>
                    <tbody>
                      {connections.connection_details
                        .slice(0, 10)
                        .map((conn) => (
                          <tr key={conn.connection_id} className="border-b">
                            <td className="p-2 font-mono text-xs">
                              {conn.connection_id}
                            </td>
                            <td className="p-2 font-mono text-xs">{conn.user_id}</td>
                            <td className="p-2 text-xs">
                              {new Date(conn.connected_at).toLocaleString()}
                            </td>
                            <td className="p-2 text-xs">
                              {new Date(conn.last_heartbeat_at).toLocaleString()}
                            </td>
                            <td className="p-2 text-xs">{conn.ip_address || 'N/A'}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
                {connections.connection_details.length > 10 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Showing 10 of {connections.connection_details.length} connections
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Updated */}
      <div className="flex items-center justify-center text-xs text-muted-foreground">
        <Clock className="h-3 w-3 mr-1" />
        Last updated: {new Date().toLocaleTimeString()}
        {autoRefresh && ' • Auto-refreshing every 10 seconds'}
      </div>
    </div>
  )
}

export default NotificationSystemHealthMonitor
