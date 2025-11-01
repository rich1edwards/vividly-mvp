/**
 * Monitoring Dashboard Component
 *
 * Real-time visualization of content generation requests flowing through the system.
 *
 * Features:
 * - Live request flow visualization
 * - Success/error/failure metrics
 * - Stage-by-stage progress tracking
 * - Server-Sent Events for real-time updates
 * - Request detail modal
 * - Circuit breaker status
 *
 * Usage:
 *   <MonitoringDashboard />
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import {
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Zap,
} from 'lucide-react';

// Types
interface Request {
  id: string;
  correlation_id: string;
  student_id: string;
  student_name?: string;
  topic: string;
  status: string;
  current_stage?: string;
  progress_percentage: number;
  created_at: string;
  elapsed_seconds: number;
  error_message?: string;
}

interface Stage {
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  duration_seconds?: number;
  error_message?: string;
  retry_count: number;
}

interface RequestDetail {
  id: string;
  correlation_id: string;
  topic: string;
  status: string;
  progress_percentage: number;
  stages: Stage[];
  error_message?: string;
  total_duration_seconds?: number;
}

interface DashboardStats {
  active_requests: number;
  completed_today: number;
  failed_today: number;
  avg_duration_seconds?: number;
  success_rate_today?: number;
  requests_per_hour: number;
  circuit_breaker_status: Record<string, any>;
}

interface MetricsBucket {
  time_bucket: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  in_progress: number;
  avg_duration?: number;
}

// Pipeline stage display configuration
const STAGE_DISPLAY = {
  validation: { label: 'Validation', icon: '🔍', color: 'bg-blue-500' },
  rag_retrieval: { label: 'Content Retrieval', icon: '📚', color: 'bg-purple-500' },
  script_generation: { label: 'Script Generation', icon: '✍️', color: 'bg-green-500' },
  video_generation: { label: 'Video Generation', icon: '🎬', color: 'bg-orange-500' },
  video_processing: { label: 'Processing', icon: '⚙️', color: 'bg-cyan-500' },
  notification: { label: 'Notification', icon: '📧', color: 'bg-pink-500' },
};

// Status badge styles
const STATUS_STYLES = {
  pending: 'bg-gray-200 text-gray-800',
  validating: 'bg-blue-100 text-blue-800',
  retrieving: 'bg-purple-100 text-purple-800',
  generating_script: 'bg-green-100 text-green-800',
  generating_video: 'bg-orange-100 text-orange-800',
  processing_video: 'bg-cyan-100 text-cyan-800',
  notifying: 'bg-pink-100 text-pink-800',
  completed: 'bg-green-200 text-green-900',
  failed: 'bg-red-200 text-red-900',
  cancelled: 'bg-gray-300 text-gray-900',
};

export const MonitoringDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activeRequests, setActiveRequests] = useState<Request[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<RequestDetail | null>(null);
  const [setMetrics] = useState<MetricsBucket[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch initial data
  const fetchDashboardData = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');

      // Fetch overview stats
      const statsResponse = await fetch('/api/v1/monitoring/dashboard', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch active requests
      const requestsResponse = await fetch('/api/v1/monitoring/requests?status=active&limit=20', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (requestsResponse.ok) {
        const requestsData = await requestsResponse.json();
        setActiveRequests(requestsData);
      }

      // Fetch metrics
      const metricsResponse = await fetch('/api/v1/monitoring/metrics?hours=12', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  }, []);

  // Setup Server-Sent Events for real-time updates
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const eventSource = new EventSource(
      `/api/v1/monitoring/stream?token=${token}`
    );

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Update active requests from SSE
      if (data.requests) {
        setActiveRequests(data.requests);
      }

      // Refresh stats periodically
      if (Math.random() < 0.1) {  // 10% of updates
        fetchDashboardData();
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
    };

    // Initial fetch
    fetchDashboardData();

    // Cleanup
    return () => {
      eventSource.close();
    };
  }, [fetchDashboardData]);

  // Fetch request details
  const fetchRequestDetails = async (requestId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/monitoring/requests/${requestId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(data);
      }
    } catch (error) {
      console.error('Error fetching request details:', error);
    }
  };

  // Format duration
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '—';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  // Format percentage
  const formatPercent = (value?: number): string => {
    if (value === undefined || value === null) return '—';
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="w-full min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Content Generation Monitor</h1>
            <p className="text-gray-600 mt-1">Real-time request tracking and pipeline visualization</p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Requests</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_requests ?? 0}</div>
            <p className="text-xs text-gray-600 mt-1">Currently processing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-700">{stats?.completed_today ?? 0}</div>
            <p className="text-xs text-gray-600 mt-1">
              Success rate: {formatPercent(stats?.success_rate_today)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Failed Today</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">{stats?.failed_today ?? 0}</div>
            <p className="text-xs text-gray-600 mt-1">Requires attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(stats?.avg_duration_seconds)}</div>
            <p className="text-xs text-gray-600 mt-1">
              {stats?.requests_per_hour.toFixed(1)} req/hour
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Circuit Breaker Status */}
      {stats?.circuit_breaker_status && Object.keys(stats.circuit_breaker_status).length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Circuit Breaker Status
            </CardTitle>
            <CardDescription>External API health monitoring</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(stats.circuit_breaker_status).map(([name, breaker]: [string, any]) => (
                <div key={name} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">{name}</div>
                    <div className="text-sm text-gray-600">
                      {breaker.total_calls} calls, {breaker.total_failures} failures
                    </div>
                  </div>
                  <Badge
                    className={
                      breaker.state === 'closed'
                        ? 'bg-green-100 text-green-800'
                        : breaker.state === 'open'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }
                  >
                    {breaker.state}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Requests Flow */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Active Requests Flow</CardTitle>
          <CardDescription>Real-time pipeline visualization</CardDescription>
        </CardHeader>
        <CardContent>
          {activeRequests.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No active requests</p>
            </div>
          ) : (
            <div className="space-y-4">
              {activeRequests.map((request) => (
                <div
                  key={request.id}
                  onClick={() => fetchRequestDetails(request.id)}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{request.topic}</h3>
                        <Badge className={STATUS_STYLES[request.status as keyof typeof STATUS_STYLES]}>
                          {request.status}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        <span className="font-mono text-xs">{request.correlation_id}</span>
                        {request.student_name && <span className="ml-2">• {request.student_name}</span>}
                        <span className="ml-2">• {formatDuration(request.elapsed_seconds)} elapsed</span>
                      </div>
                    </div>
                    {request.error_message && (
                      <Alert className="max-w-xs">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>{request.error_message}</AlertDescription>
                      </Alert>
                    )}
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">
                        {request.current_stage && STAGE_DISPLAY[request.current_stage as keyof typeof STAGE_DISPLAY]?.label}
                      </span>
                      <span className="font-medium">{request.progress_percentage}%</span>
                    </div>
                    <Progress value={request.progress_percentage} className="h-2" />
                  </div>

                  {/* Stage Pills */}
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(STAGE_DISPLAY).map(([stageName, config]) => {
                      const isActive = request.current_stage === stageName;
                      const isPast =
                        request.current_stage &&
                        Object.keys(STAGE_DISPLAY).indexOf(stageName) <
                        Object.keys(STAGE_DISPLAY).indexOf(request.current_stage);

                      return (
                        <div
                          key={stageName}
                          className={`
                            px-3 py-1 rounded-full text-xs font-medium transition-all
                            ${isPast ? config.color + ' text-white' : ''}
                            ${isActive ? config.color + ' text-white animate-pulse' : ''}
                            ${!isPast && !isActive ? 'bg-gray-200 text-gray-600' : ''}
                          `}
                        >
                          <span className="mr-1">{config.icon}</span>
                          {config.label}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Request Detail Modal (simplified - would use a proper modal component) */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Request Details</CardTitle>
              <CardDescription>
                {selectedRequest.correlation_id}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Topic</h4>
                  <p>{selectedRequest.topic}</p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Pipeline Stages</h4>
                  <div className="space-y-2">
                    {selectedRequest.stages.map((stage, index) => (
                      <div key={index} className="border rounded p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">
                            {STAGE_DISPLAY[stage.name as keyof typeof STAGE_DISPLAY]?.label || stage.name}
                          </span>
                          <Badge className={STATUS_STYLES[stage.status as keyof typeof STATUS_STYLES]}>
                            {stage.status}
                          </Badge>
                        </div>
                        {stage.duration_seconds && (
                          <p className="text-sm text-gray-600 mt-1">
                            Duration: {formatDuration(stage.duration_seconds)}
                          </p>
                        )}
                        {stage.error_message && (
                          <p className="text-sm text-red-600 mt-1">{stage.error_message}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => setSelectedRequest(null)}
                  className="w-full py-2 px-4 bg-gray-200 hover:bg-gray-300 rounded"
                >
                  Close
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default MonitoringDashboard;
