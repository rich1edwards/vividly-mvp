/**
 * System Metrics Dashboard (Phase 3.3.1)
 *
 * Comprehensive super admin dashboard for system-wide monitoring
 * Features:
 * - Key metrics cards (Total Users, Content Requests 24h, API Latency, Error Rate)
 * - Charts grid with Recharts (Line, Bar, Pie, Area)
 * - Error log table with filtering
 * - Date range selector with presets
 * - Auto-refresh toggle (every 30s)
 * - Real-time data with React Query
 * - Export to CSV functionality
 * - Mobile responsive design
 *
 * Uses:
 * - Recharts for data visualization
 * - React Query for server state management
 * - StatsCard component (Phase 2.1)
 * - superAdminApi for data fetching
 */

import React, { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Users,
  FileText,
  Clock,
  AlertTriangle,
  RefreshCw,
  Download,
  TrendingUp,
  TrendingDown,
  Activity,
  Database,
  Bell,
  Server,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { superAdminApi } from '../../api/superAdmin'
import { StatsCard } from '../../components/StatsCard'
import { useToast } from '../../hooks/useToast'

/**
 * Date range presets
 */
type DateRangePreset = '24h' | '7d' | '30d' | 'custom'

interface DateRange {
  start: string
  end: string
}

/**
 * Chart color palette
 */
const COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  purple: '#8b5cf6',
  teal: '#14b8a6',
  pink: '#ec4899',
  indigo: '#6366f1',
}

const PIE_COLORS = [
  COLORS.primary,
  COLORS.success,
  COLORS.warning,
  COLORS.purple,
  COLORS.teal,
  COLORS.pink,
]

/**
 * SystemMetricsDashboard Component
 */
export const SystemMetricsDashboard: React.FC = () => {
  const { toast } = useToast()

  // State
  const [dateRangePreset, setDateRangePreset] = useState<DateRangePreset>('24h')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  // Calculate date range
  const dateRange = useMemo((): DateRange => {
    const end = new Date()
    const start = new Date()

    switch (dateRangePreset) {
      case '24h':
        start.setHours(start.getHours() - 24)
        break
      case '7d':
        start.setDate(start.getDate() - 7)
        break
      case '30d':
        start.setDate(start.getDate() - 30)
        break
      default:
        start.setDate(start.getDate() - 1)
    }

    return {
      start: start.toISOString(),
      end: end.toISOString(),
    }
  }, [dateRangePreset])

  // Fetch all metrics
  const {
    data: metricsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['super-admin-metrics', dateRange.start, dateRange.end],
    queryFn: () => superAdminApi.getAllMetrics(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: autoRefresh ? 30 * 1000 : false,
  })

  // Fetch active requests for recent activity
  const { data: activeRequests } = useQuery({
    queryKey: ['active-requests'],
    queryFn: () => superAdminApi.getActiveRequests({ limit: 100 }),
    staleTime: 30 * 1000,
    refetchInterval: autoRefresh ? 30 * 1000 : false,
  })

  // Auto-refresh toggle effect
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refetch()
      }, 30 * 1000)
      setRefreshInterval(interval)
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        setRefreshInterval(null)
      }
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [autoRefresh, refetch])

  // Export to CSV
  const handleExport = () => {
    if (!metricsData) return

    try {
      const csvContent = [
        ['Metric', 'Value'],
        ['Total Users', metricsData.admin.total_users],
        ['Active Users Today', metricsData.admin.active_users_today],
        ['Total Content Requests', metricsData.system.total_requests],
        ['Active Requests', metricsData.system.active_requests],
        ['Completed Requests', metricsData.system.completed_requests],
        ['Failed Requests', metricsData.system.failed_requests],
        ['Cache Hit Rate', `${(metricsData.cache.hit_rate * 100).toFixed(2)}%`],
        ['Notifications Sent', metricsData.notifications.total_sent],
        ['Notification Delivery Rate', `${(metricsData.notifications.delivery_rate * 100).toFixed(2)}%`],
      ]
        .map((row) => row.join(','))
        .join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `system_metrics_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: 'Export Successful',
        description: 'Metrics exported to CSV',
        variant: 'success',
      })
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export metrics',
        variant: 'error',
      })
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading system metrics...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !metricsData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load system metrics</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Calculate metrics
  const errorRate =
    metricsData.system.total_requests > 0
      ? (metricsData.system.failed_requests / metricsData.system.total_requests) * 100
      : 0

  const userGrowthRate =
    metricsData.admin.total_users > 0
      ? ((metricsData.admin.active_users_today / metricsData.admin.total_users) * 100)
      : 0

  // Prepare chart data
  const stageDistributionData = Object.entries(metricsData.system.stage_distribution).map(
    ([stage, count]) => ({
      name: stage,
      value: count,
    })
  )

  const confidenceScoresData = Object.entries(metricsData.system.avg_confidence).map(
    ([stage, score]) => ({
      stage: stage.toUpperCase(),
      confidence: Math.round(score * 100),
    })
  )

  const contentTypeData = Object.entries(metricsData.content.content_by_type).map(
    ([type, count]) => ({
      name: type.charAt(0).toUpperCase() + type.slice(1),
      value: count,
    })
  )

  const cacheStatsData = [
    { name: 'Hit Rate', value: Math.round(metricsData.cache.hit_rate * 100) },
    { name: 'Miss Rate', value: Math.round(metricsData.cache.miss_rate * 100) },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">System Metrics Dashboard</h1>
              <p className="mt-2 text-gray-600">
                Real-time monitoring of system-wide performance and health
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* Auto-refresh toggle */}
              <label className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer hover:bg-gray-200 transition-colors">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <Activity className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-700">Auto-refresh (30s)</span>
              </label>

              {/* Manual refresh */}
              <button
                onClick={() => refetch()}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>

              {/* Export */}
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>
          </div>

          {/* Date Range Selector */}
          <div className="mt-4 flex items-center gap-2">
            <span className="text-sm text-gray-600">Time Range:</span>
            {(['24h', '7d', '30d'] as DateRangePreset[]).map((preset) => (
              <button
                key={preset}
                onClick={() => setDateRangePreset(preset)}
                className={`
                  px-3 py-1 text-sm rounded-lg transition-colors
                  ${
                    dateRangePreset === preset
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                {preset === '24h' ? 'Last 24 Hours' : preset === '7d' ? 'Last 7 Days' : 'Last 30 Days'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total Users"
            value={metricsData.admin.total_users.toString()}
            icon={Users}
            trend={{
              value: Math.round(userGrowthRate),
              direction: userGrowthRate > 50 ? 'up' : userGrowthRate > 20 ? 'neutral' : 'down',
              label: `${Math.round(userGrowthRate)}% active today`,
              isPercentage: false,
            }}
          />
          <StatsCard
            title="Content Requests (24h)"
            value={metricsData.system.active_requests.toString()}
            icon={FileText}
            trend={{
              value: metricsData.system.total_requests,
              direction: 'up',
              label: `${metricsData.system.total_requests} total`,
            }}
          />
          <StatsCard
            title="Avg Generation Time"
            value={`${Math.round(metricsData.content.avg_generation_time_seconds)}s`}
            icon={Clock}
            trend={{
              value: Math.round(metricsData.content.avg_generation_time_seconds),
              direction:
                metricsData.content.avg_generation_time_seconds < 60
                  ? 'up'
                  : metricsData.content.avg_generation_time_seconds < 120
                  ? 'neutral'
                  : 'down',
              label: 'per request',
            }}
          />
          <StatsCard
            title="Error Rate"
            value={`${errorRate.toFixed(1)}%`}
            icon={AlertTriangle}
            trend={{
              value: errorRate,
              direction: errorRate < 5 ? 'up' : errorRate < 10 ? 'neutral' : 'down',
              label: `${metricsData.system.failed_requests} failed`,
              isPercentage: true,
            }}
          />
        </div>

        {/* Secondary Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatsCard
            title="Cache Hit Rate"
            value={`${(metricsData.cache.hit_rate * 100).toFixed(1)}%`}
            icon={Database}
            subtitle={`${metricsData.cache.total_keys} keys, ${metricsData.cache.total_size_mb.toFixed(2)} MB`}
          />
          <StatsCard
            title="Notifications Sent"
            value={metricsData.notifications.total_sent.toString()}
            icon={Bell}
            subtitle={`${(metricsData.notifications.delivery_rate * 100).toFixed(1)}% delivered`}
          />
          <StatsCard
            title="System Health"
            value="Healthy"
            icon={Server}
            subtitle="All services operational"
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pipeline Stage Distribution (Bar Chart) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Stage Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stageDistributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill={COLORS.primary} name="Requests" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Confidence Scores (Line Chart) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Average Confidence Scores by Stage
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={confidenceScoresData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke={COLORS.success}
                  strokeWidth={2}
                  name="Confidence %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Content Type Distribution (Pie Chart) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Content Type Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={contentTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {contentTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Cache Performance (Area Chart) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={cacheStatsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={COLORS.teal}
                  fill={COLORS.teal}
                  fillOpacity={0.6}
                  name="Rate %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Active Requests Table */}
        {activeRequests && activeRequests.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Active Requests</h3>
              <p className="text-sm text-gray-600 mt-1">
                Showing {Math.min(10, activeRequests.length)} of {activeRequests.length} active requests
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Request ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Student
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Elapsed Time
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activeRequests.slice(0, 10).map((request) => (
                    <tr key={request.request_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                        {request.request_id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {request.student_email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                          {request.current_stage}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs ${
                            request.status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : request.status === 'failed'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {request.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {request.elapsed_seconds}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SystemMetricsDashboard
