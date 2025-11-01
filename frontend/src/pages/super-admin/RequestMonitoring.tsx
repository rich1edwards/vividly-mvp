/**
 * Request Monitoring Page
 *
 * Real-time monitoring dashboard for content generation pipeline.
 * Shows request flow through all pipeline stages with confidence scores.
 * Super Admin only.
 */

import React, { useState, useEffect } from 'react'
import DashboardLayout from '../../components/DashboardLayout'
import { Button } from '../../components/ui/Button'
import { monitoringApi, RequestFlow, SystemMetrics } from '../../api/monitoring'

// Pipeline stage constants
const PIPELINE_STAGES = {
  request_received: { label: 'Request Received', color: 'bg-blue-100 text-blue-800' },
  nlu_extraction: { label: 'NLU Extraction', color: 'bg-purple-100 text-purple-800' },
  interest_matching: { label: 'Interest Matching', color: 'bg-pink-100 text-pink-800' },
  rag_retrieval: { label: 'RAG Retrieval', color: 'bg-indigo-100 text-indigo-800' },
  script_generation: { label: 'Script Generation', color: 'bg-cyan-100 text-cyan-800' },
  tts_generation: { label: 'TTS Generation', color: 'bg-teal-100 text-teal-800' },
  video_generation: { label: 'Video Generation', color: 'bg-emerald-100 text-emerald-800' },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-800' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-800' },
}

const RequestMonitoring: React.FC = () => {
  const [requests, setRequests] = useState<RequestFlow[]>([])
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [searchEmail, setSearchEmail] = useState('')
  const [searchId, setSearchId] = useState('')
  const [selectedRequest, setSelectedRequest] = useState<RequestFlow | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Load data
  const loadData = async () => {
    try {
      setError(null)

      // Load requests and metrics in parallel
      const [requestsData, metricsData] = await Promise.all([
        searchEmail || searchId
          ? monitoringApi.searchRequests(searchEmail || undefined, searchId || undefined)
          : monitoringApi.getActiveRequests(),
        monitoringApi.getSystemMetrics()
      ])

      setRequests(requestsData)
      setMetrics(metricsData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load monitoring data')
      console.error('Monitoring error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadData()
  }, [])

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      loadData()
    }, 5000)

    return () => clearInterval(interval)
  }, [autoRefresh, searchEmail, searchId])

  // Handle search
  const handleSearch = () => {
    setLoading(true)
    loadData()
  }

  // Clear search
  const handleClearSearch = () => {
    setSearchEmail('')
    setSearchId('')
    setLoading(true)
    loadData()
  }

  // Format elapsed time
  const formatElapsedTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  // Get status badge color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Format confidence score
  const formatConfidence = (score: number | null): string => {
    if (score === null) return 'N/A'
    return `${(score * 100).toFixed(0)}%`
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Request Monitoring</h1>
            <p className="text-muted-foreground">
              Real-time pipeline tracking for content generation requests
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={autoRefresh ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? (
                <>
                  <svg className="w-4 h-4 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Auto-refresh (5s)
                </>
              ) : (
                'Enable Auto-refresh'
              )}
            </Button>
            <Button variant="ghost" size="sm" onClick={loadData}>
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Now
            </Button>
          </div>
        </div>

        {/* System Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-card p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Total Requests</div>
              <div className="text-2xl font-bold">{metrics.total_requests}</div>
            </div>
            <div className="bg-card p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Active</div>
              <div className="text-2xl font-bold text-yellow-600">{metrics.active_requests}</div>
            </div>
            <div className="bg-card p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Completed</div>
              <div className="text-2xl font-bold text-green-600">{metrics.completed_requests}</div>
            </div>
            <div className="bg-card p-4 rounded-lg border">
              <div className="text-sm text-muted-foreground">Failed</div>
              <div className="text-2xl font-bold text-red-600">{metrics.failed_requests}</div>
            </div>
          </div>
        )}

        {/* Search Bar */}
        <div className="bg-card p-4 rounded-lg border">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search by student email..."
              value={searchEmail}
              onChange={(e) => setSearchEmail(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <input
              type="text"
              placeholder="Or student ID..."
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <Button onClick={handleSearch}>Search</Button>
            {(searchEmail || searchId) && (
              <Button variant="ghost" onClick={handleClearSearch}>Clear</Button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Request List */}
        {loading && requests.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-2 text-muted-foreground">Loading requests...</p>
          </div>
        ) : requests.length === 0 ? (
          <div className="text-center py-12 bg-card border rounded-lg">
            <svg className="mx-auto h-12 w-12 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="mt-2 text-muted-foreground">
              {searchEmail || searchId ? 'No requests found for search criteria' : 'No active requests'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {requests.map((request) => (
              <div
                key={request.request_id}
                className="bg-card p-4 rounded-lg border hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedRequest(selectedRequest?.request_id === request.request_id ? null : request)}
              >
                {/* Request Header */}
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-mono text-sm text-muted-foreground">
                      Request ID: {request.request_id.substring(0, 8)}...
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Student ID: {request.student_id}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${getStatusColor(request.status || 'unknown')}`}>
                      {request.status?.toUpperCase()}
                    </div>
                    {request.elapsed_seconds !== undefined && (
                      <div className="text-sm text-muted-foreground mt-1">
                        {formatElapsedTime(request.elapsed_seconds)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Current Stage */}
                {request.current_stage && (
                  <div className="mb-3">
                    <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${PIPELINE_STAGES[request.current_stage as keyof typeof PIPELINE_STAGES]?.color || 'bg-gray-100 text-gray-800'}`}>
                      {PIPELINE_STAGES[request.current_stage as keyof typeof PIPELINE_STAGES]?.label || request.current_stage}
                    </div>
                  </div>
                )}

                {/* Pipeline Progress Bar */}
                {request.events && request.events.length > 0 && (
                  <div className="flex gap-1 mb-3">
                    {Object.keys(PIPELINE_STAGES).slice(0, -2).map((stage) => {
                      const hasStage = request.events?.some(e => e.stage === stage)
                      const isCurrent = request.current_stage === stage
                      return (
                        <div
                          key={stage}
                          className={`flex-1 h-2 rounded-full transition-all ${
                            hasStage ? 'bg-primary' : isCurrent ? 'bg-primary/50' : 'bg-muted'
                          }`}
                          title={PIPELINE_STAGES[stage as keyof typeof PIPELINE_STAGES]?.label}
                        />
                      )
                    })}
                  </div>
                )}

                {/* Expanded Details */}
                {selectedRequest?.request_id === request.request_id && request.events && (
                  <div className="mt-4 pt-4 border-t space-y-2">
                    <h4 className="font-semibold mb-2">Pipeline Events:</h4>
                    {request.events.map((event, idx) => (
                      <div key={idx} className="bg-muted p-3 rounded-lg">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className={`inline-block px-2 py-1 rounded text-xs font-medium mb-1 ${PIPELINE_STAGES[event.stage as keyof typeof PIPELINE_STAGES]?.color || 'bg-gray-100 text-gray-800'}`}>
                              {PIPELINE_STAGES[event.stage as keyof typeof PIPELINE_STAGES]?.label || event.stage}
                            </div>
                            <div className="text-sm">
                              Status: <span className="font-medium">{event.status}</span>
                            </div>
                            {event.confidence_score !== null && (
                              <div className="text-sm">
                                Confidence: <span className="font-medium">{formatConfidence(event.confidence_score)}</span>
                              </div>
                            )}
                            {event.error && (
                              <div className="text-sm text-red-600 mt-1">
                                Error: {event.error}
                              </div>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                        {event.metadata && Object.keys(event.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs cursor-pointer text-muted-foreground hover:text-foreground">
                              View metadata
                            </summary>
                            <pre className="mt-2 text-xs bg-background p-2 rounded overflow-x-auto">
                              {JSON.stringify(event.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

export default RequestMonitoring
