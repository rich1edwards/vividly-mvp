/**
 * Loading Component
 *
 * Loading spinner and skeleton components
 * Based on Vividly design system
 */

import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

// Spinner Component
const spinnerVariants = cva('animate-spin rounded-full border-2 border-current', {
  variants: {
    size: {
      sm: 'h-4 w-4 border-2',
      md: 'h-6 w-6 border-2',
      lg: 'h-8 w-8 border-3',
      xl: 'h-12 w-12 border-4'
    },
    variant: {
      primary: 'border-vividly-blue border-t-transparent',
      secondary: 'border-vividly-coral border-t-transparent',
      muted: 'border-muted-foreground border-t-transparent',
      white: 'border-white border-t-transparent'
    }
  },
  defaultVariants: {
    size: 'md',
    variant: 'primary'
  }
})

export interface SpinnerProps extends VariantProps<typeof spinnerVariants> {
  className?: string
}

export const Spinner: React.FC<SpinnerProps> = ({ size, variant, className }) => {
  return (
    <div className={cn(spinnerVariants({ size, variant }), className)} role="status">
      <span className="sr-only">Loading...</span>
    </div>
  )
}

// Full Page Loading
export const PageLoading: React.FC<{ message?: string }> = ({
  message = 'Loading...'
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="xl" variant="primary" />
        <p className="text-lg text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}

// Centered Loading (for sections)
export const CenteredLoading: React.FC<{ message?: string }> = ({
  message = 'Loading...'
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <Spinner size="lg" variant="primary" />
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </div>
  )
}

// Inline Loading
export const InlineLoading: React.FC<{ message?: string; className?: string }> = ({
  message,
  className
}) => {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Spinner size="sm" variant="primary" />
      {message && <span className="text-sm text-muted-foreground">{message}</span>}
    </div>
  )
}

// Skeleton Component
const skeletonVariants = cva('animate-pulse rounded bg-muted', {
  variants: {
    variant: {
      default: '',
      text: 'h-4',
      title: 'h-6',
      avatar: 'rounded-full',
      button: 'h-10'
    }
  },
  defaultVariants: {
    variant: 'default'
  }
})

export interface SkeletonProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof skeletonVariants> {}

export const Skeleton: React.FC<SkeletonProps> = ({ className, variant, ...props }) => {
  return <div className={cn(skeletonVariants({ variant }), className)} {...props} />
}

// Skeleton Variants
export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} variant="text" className={i === lines - 1 ? 'w-3/4' : 'w-full'} />
      ))}
    </div>
  )
}

export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn('space-y-3 p-4 border rounded-lg', className)}>
      <Skeleton variant="title" className="w-1/2" />
      <SkeletonText lines={2} />
      <Skeleton variant="button" className="w-1/3" />
    </div>
  )
}
