/**
 * Loading Fallback Component (Phase 4.3.1)
 *
 * Provides a consistent loading experience during code splitting and lazy loading
 * Features:
 * - Centered spinner with animation
 * - Optional loading message
 * - Accessible ARIA labels
 * - Smooth fade-in transition
 * - Prevents layout shift
 */

import React from 'react'
import { RefreshCw } from 'lucide-react'

interface LoadingFallbackProps {
  message?: string
  fullScreen?: boolean
}

/**
 * LoadingFallback Component
 *
 * Used as fallback for React.Suspense during lazy loading
 */
export const LoadingFallback: React.FC<LoadingFallbackProps> = ({
  message = 'Loading...',
  fullScreen = true,
}) => {
  return (
    <div
      className={`
        flex items-center justify-center bg-gray-50
        ${fullScreen ? 'min-h-screen' : 'min-h-[400px]'}
      `}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="text-center animate-fade-in">
        <RefreshCw
          className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600"
          aria-hidden="true"
        />
        <p className="text-gray-600 text-sm">{message}</p>
      </div>
    </div>
  )
}

/**
 * Minimal Loading Spinner
 *
 * Lightweight spinner for inline loading states
 */
export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <RefreshCw
      className={`${sizeClasses[size]} animate-spin text-blue-600`}
      aria-hidden="true"
    />
  )
}

export default LoadingFallback
