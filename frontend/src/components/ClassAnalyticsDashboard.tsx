/**
 * ClassAnalyticsDashboard Component (Phase 2.5.1)
 *
 * Comprehensive analytics dashboard for class performance tracking
 * Features:
 * - Line chart: Content requests over time
 * - Bar chart: Videos by topic
 * - Pie chart: Video completion rates
 * - Area chart: Student engagement trend
 * - Date range selector (7d, 30d, 90d, custom)
 * - CSV export functionality
 * - Print view support
 * - Responsive design (stacks on mobile)
 * - Interactive charts with hover tooltips
 */

import React, { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
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
import {
  Calendar,
  Download,
  Printer,
  TrendingUp,
  Users,
  Video,
  FileText,
  RefreshCw,
  ChevronDown,
} from 'lucide-react'
import { teacherApi } from '../api/teacher'
import { useToast } from '../hooks/useToast'
import type { ClassAnalytics } from '../types/teacher'

interface ClassAnalyticsDashboardProps {
  /**
   * Class ID to fetch analytics for
   */
  classId: string
  /**
   * Class name for display
   */
  className?: string
}

/**
 * Date range presets
 */
type DateRangePreset = '7d' | '30d' | '90d' | 'custom'

interface DateRange {
  start: string
  end: string
}

/**
 * Colors for charts
 */
const COLORS = {
  primary: '#3b82f6', // blue-600
  secondary: '#8b5cf6', // purple-600
  success: '#10b981', // green-600
  warning: '#f59e0b', // amber-600
  danger: '#ef4444', // red-600
  gray: '#6b7280', // gray-500
  pie: ['#3b82f6', '#10b981', '#f59e0b'], // blue, green, amber
}

/**
 * Format date for display (e.g., "Jan 15")
 */
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/**
 * Format time in seconds to readable format
 */
const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins}m`
  const hours = Math.floor(mins / 60)
  const remainingMins = mins % 60
  return `${hours}h ${remainingMins}m`
}

/**
 * Generate date range based on preset
 */
const getDateRange = (preset: DateRangePreset, customRange?: DateRange): DateRange => {
  const end = new Date()
  const start = new Date()

  switch (preset) {
    case '7d':
      start.setDate(end.getDate() - 7)
      break
    case '30d':
      start.setDate(end.getDate() - 30)
      break
    case '90d':
      start.setDate(end.getDate() - 90)
      break
    case 'custom':
      if (customRange) return customRange
      start.setDate(end.getDate() - 30)
      break
  }

  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  }
}

/**
 * Export data to CSV
 */
const exportToCSV = (data: ClassAnalytics, className: string) => {
  const timestamp = new Date().toISOString().split('T')[0]
  const filename = `${className.replace(/\s+/g, '_')}_analytics_${timestamp}.csv`

  // Build CSV content
  const csvRows: string[] = []

  // Header
  csvRows.push(`Class Analytics Report: ${className}`)
  csvRows.push(`Date Range: ${formatDate(data.date_range.start)} - ${formatDate(data.date_range.end)}`)
  csvRows.push('')

  // Content Requests Over Time
  csvRows.push('Content Requests Over Time')
  csvRows.push('Date,Count')
  data.content_requests_over_time.forEach((item) => {
    csvRows.push(`${formatDate(item.date)},${item.count}`)
  })
  csvRows.push('')

  // Videos by Topic
  csvRows.push('Videos by Topic')
  csvRows.push('Topic,Count')
  data.videos_by_topic.forEach((item) => {
    csvRows.push(`${item.topic},${item.count}`)
  })
  csvRows.push('')

  // Completion Rates
  csvRows.push('Video Completion Rates')
  csvRows.push('Status,Count')
  csvRows.push(`Completed,${data.completion_rates.completed}`)
  csvRows.push(`In Progress,${data.completion_rates.in_progress}`)
  csvRows.push(`Not Started,${data.completion_rates.not_started}`)
  csvRows.push('')

  // Student Engagement Trend
  csvRows.push('Student Engagement Trend')
  csvRows.push('Date,Active Students,Avg Watch Time (seconds)')
  data.student_engagement_trend.forEach((item) => {
    csvRows.push(`${formatDate(item.date)},${item.active_students},${item.avg_watch_time}`)
  })
  csvRows.push('')

  // Top Students
  csvRows.push('Top Students')
  csvRows.push('Name,Videos Watched,Engagement Score')
  data.top_students.forEach((student) => {
    csvRows.push(`${student.name},${student.videos_watched},${student.engagement_score}`)
  })

  // Create and download file
  const csvContent = csvRows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * ClassAnalyticsDashboard Component
 */
export const ClassAnalyticsDashboard: React.FC<ClassAnalyticsDashboardProps> = ({
  classId,
  className = 'Class',
}) => {
  const { toast } = useToast()
  const [dateRangePreset, setDateRangePreset] = useState<DateRangePreset>('30d')
  const [customDateRange, setCustomDateRange] = useState<DateRange | null>(null)
  const [showDatePicker, setShowDatePicker] = useState(false)

  // Calculate actual date range
  const dateRange = useMemo(() => {
    return getDateRange(dateRangePreset, customDateRange || undefined)
  }, [dateRangePreset, customDateRange])

  // Fetch analytics data
  const {
    data: analyticsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['class-analytics', classId, dateRange.start, dateRange.end],
    queryFn: () => teacherApi.getAnalytics(classId, dateRange.start, dateRange.end),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Handle export
  const handleExport = () => {
    if (!analyticsData) return

    try {
      exportToCSV(analyticsData, className)
      toast({
        title: 'Export Successful',
        description: 'Analytics data exported to CSV',
        variant: 'success',
      })
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export analytics data',
        variant: 'error',
      })
    }
  }

  // Handle print
  const handlePrint = () => {
    window.print()
  }

  // Handle date range change
  const handleDateRangeChange = (preset: DateRangePreset) => {
    setDateRangePreset(preset)
    if (preset !== 'custom') {
      setShowDatePicker(false)
      setCustomDateRange(null)
    } else {
      setShowDatePicker(true)
    }
  }

  // Handle custom date range submit
  const handleCustomDateRangeSubmit = (start: string, end: string) => {
    setCustomDateRange({ start, end })
    setShowDatePicker(false)
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !analyticsData) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load analytics</p>
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

  const data = analyticsData

  // Prepare pie chart data
  const pieData = [
    { name: 'Completed', value: data.completion_rates.completed },
    { name: 'In Progress', value: data.completion_rates.in_progress },
    { name: 'Not Started', value: data.completion_rates.not_started },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Date Range Selector */}
        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Calendar className="inline w-4 h-4 mr-1" />
            Date Range
          </label>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDateRangeChange('7d')}
              className={`px-4 py-2 text-sm rounded-lg border ${
                dateRangePreset === '7d'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => handleDateRangeChange('30d')}
              className={`px-4 py-2 text-sm rounded-lg border ${
                dateRangePreset === '30d'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => handleDateRangeChange('90d')}
              className={`px-4 py-2 text-sm rounded-lg border ${
                dateRangePreset === '90d'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              90 Days
            </button>
            <div className="relative">
              <button
                onClick={() => handleDateRangeChange('custom')}
                className={`px-4 py-2 text-sm rounded-lg border flex items-center gap-2 ${
                  dateRangePreset === 'custom'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Custom
                <ChevronDown className="w-4 h-4" />
              </button>
              {showDatePicker && (
                <div className="absolute top-full left-0 mt-2 p-4 bg-white border border-gray-300 rounded-lg shadow-lg z-10 min-w-[300px]">
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Start Date
                      </label>
                      <input
                        type="date"
                        defaultValue={dateRange.start}
                        onChange={(e) => {
                          const endInput = e.target.parentElement?.parentElement?.querySelector(
                            'input[type="date"]:last-of-type'
                          ) as HTMLInputElement
                          if (endInput?.value) {
                            handleCustomDateRangeSubmit(e.target.value, endInput.value)
                          }
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        End Date
                      </label>
                      <input
                        type="date"
                        defaultValue={dateRange.end}
                        onChange={(e) => {
                          const startInput = e.target.parentElement?.parentElement?.querySelector(
                            'input[type="date"]:first-of-type'
                          ) as HTMLInputElement
                          if (startInput?.value) {
                            handleCustomDateRangeSubmit(startInput.value, e.target.value)
                          }
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      />
                    </div>
                    <button
                      onClick={() => setShowDatePicker(false)}
                      className="w-full px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                      Close
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {formatDate(dateRange.start)} - {formatDate(dateRange.end)}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 print:hidden">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-sm"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-sm"
          >
            <Printer className="w-4 h-4" />
            Print
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-gray-900">
                {data.content_requests_over_time.reduce((sum, item) => sum + item.count, 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <Video className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Completed Videos</p>
              <p className="text-2xl font-bold text-gray-900">{data.completion_rates.completed}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Avg Active Students</p>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(
                  data.student_engagement_trend.reduce((sum, item) => sum + item.active_students, 0) /
                    (data.student_engagement_trend.length || 1)
                )}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Avg Watch Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatTime(
                  Math.round(
                    data.student_engagement_trend.reduce((sum, item) => sum + item.avg_watch_time, 0) /
                      (data.student_engagement_trend.length || 1)
                  )
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Line Chart: Content Requests Over Time */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Content Requests Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.content_requests_over_time}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
                labelFormatter={formatDate}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                name="Requests"
                stroke={COLORS.primary}
                strokeWidth={2}
                dot={{ fill: COLORS.primary, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart: Videos by Topic */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Videos by Topic</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.videos_by_topic}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="topic"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="count" name="Videos" fill={COLORS.secondary} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart: Video Completion Rates */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Video Completion Rates</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS.pie[index % COLORS.pie.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Area Chart: Student Engagement Trend */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Student Engagement Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data.student_engagement_trend}>
              <defs>
                <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.success} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={COLORS.success} stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
                labelFormatter={formatDate}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="active_students"
                name="Active Students"
                stroke={COLORS.success}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorActive)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Students Table */}
      {data.top_students.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Students</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Videos Watched
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Engagement Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.top_students.map((student, index) => (
                  <tr key={student.user_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                          index === 0
                            ? 'bg-yellow-100 text-yellow-700'
                            : index === 1
                            ? 'bg-gray-200 text-gray-700'
                            : index === 2
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-blue-50 text-blue-700'
                        }`}
                      >
                        {index + 1}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{student.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{student.videos_watched}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2 mr-3">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{ width: `${student.engagement_score}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {student.engagement_score}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Print Styles */}
      <style>{`
        @media print {
          @page {
            margin: 1cm;
          }
          .print\\:hidden {
            display: none !important;
          }
        }
      `}</style>
    </div>
  )
}

export default ClassAnalyticsDashboard
