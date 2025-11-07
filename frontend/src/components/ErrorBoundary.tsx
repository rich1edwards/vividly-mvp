/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs errors, and displays a fallback UI instead of crashing the app.
 *
 * Features:
 * - Catches rendering errors, lifecycle method errors, and constructor errors
 * - Displays user-friendly error message with reload option
 * - Logs error details to console for debugging
 * - Can reset error state to retry rendering
 * - Prevents cascading errors from crashing entire app
 *
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 *
 * Or wrap entire app in App.tsx:
 * <ErrorBoundary>
 *   <BrowserRouter>
 *     ...
 *   </BrowserRouter>
 * </ErrorBoundary>
 */

import React, { Component, ReactNode, ErrorInfo } from 'react'
import { Button } from './ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/Card'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorCount: number
}

/**
 * ErrorBoundary Component
 *
 * React Error Boundary for catching and handling component errors gracefully.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so next render shows fallback UI
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error details to console
    console.error('ErrorBoundary caught an error:', error)
    console.error('Error details:', errorInfo)
    console.error('Component stack:', errorInfo.componentStack)

    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }))

    // Call optional error handler prop
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // TODO: Send error to monitoring service (e.g., Sentry, LogRocket)
    // Example:
    // logErrorToService(error, errorInfo)
  }

  handleReset = (): void => {
    // Reset error state to retry rendering
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  handleReload = (): void => {
    // Reload the page to fully reset application state
    window.location.reload()
  }

  handleGoHome = (): void => {
    // Navigate to home page
    window.location.href = '/'
  }

  render(): ReactNode {
    const { hasError, error, errorInfo, errorCount } = this.state
    const { children, fallback, showDetails = false } = this.props

    // If error occurred, show fallback UI
    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card variant="elevated" padding="lg" className="max-w-2xl w-full">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 rounded-full bg-vividly-red/10 flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-vividly-red"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <div>
                  <CardTitle className="text-vividly-red">Something Went Wrong</CardTitle>
                  <CardDescription>
                    We encountered an unexpected error while loading this page.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* User-friendly error message */}
              <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4">
                <p className="text-sm text-vividly-red font-medium mb-1">
                  Error Details
                </p>
                <p className="text-sm text-vividly-red">
                  {error?.message || 'An unexpected error occurred'}
                </p>
                {errorCount > 1 && (
                  <p className="text-xs text-vividly-red mt-2">
                    This error has occurred {errorCount} time(s). Consider reloading the page.
                  </p>
                )}
              </div>

              {/* Debugging information (only shown if showDetails is true) */}
              {showDetails && errorInfo && (
                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-muted-foreground hover:text-foreground mb-2">
                    Technical Details (for debugging)
                  </summary>
                  <div className="bg-muted rounded-lg p-4 space-y-3">
                    <div>
                      <p className="font-medium text-xs text-muted-foreground mb-1">
                        Error Message:
                      </p>
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                        {error?.toString()}
                      </pre>
                    </div>
                    <div>
                      <p className="font-medium text-xs text-muted-foreground mb-1">
                        Component Stack:
                      </p>
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                    {error?.stack && (
                      <div>
                        <p className="font-medium text-xs text-muted-foreground mb-1">
                          Stack Trace:
                        </p>
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                          {error.stack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              {/* Troubleshooting suggestions */}
              <div className="text-sm">
                <p className="font-medium mb-2">Try the following:</p>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  <li>Click "Try Again" to retry loading this component</li>
                  <li>Click "Reload Page" to refresh the entire application</li>
                  <li>Click "Go Home" to return to the homepage</li>
                  <li>Clear your browser cache and cookies</li>
                  <li>If the problem persists, contact support</li>
                </ul>
              </div>
            </CardContent>

            <CardFooter className="flex gap-3">
              <Button variant="tertiary" onClick={this.handleReset} fullWidth>
                Try Again
              </Button>
              <Button variant="secondary" onClick={this.handleReload} fullWidth>
                Reload Page
              </Button>
              <Button variant="primary" onClick={this.handleGoHome} fullWidth>
                Go Home
              </Button>
            </CardFooter>
          </Card>
        </div>
      )
    }

    // No error, render children normally
    return children
  }
}

/**
 * Functional wrapper component for easier usage with hooks
 */
interface ErrorFallbackProps {
  error: Error
  resetError: () => void
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError }) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <Card variant="elevated" padding="lg" className="max-w-lg w-full">
        <CardHeader>
          <CardTitle className="text-vividly-red">Error</CardTitle>
          <CardDescription>Something went wrong</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-vividly-red/10 border border-vividly-red rounded-lg p-4">
            <p className="text-sm text-vividly-red">{error.message}</p>
          </div>
        </CardContent>
        <CardFooter className="flex gap-3">
          <Button variant="secondary" onClick={resetError} fullWidth>
            Try Again
          </Button>
          <Button variant="primary" onClick={() => window.location.reload()} fullWidth>
            Reload Page
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default ErrorBoundary
