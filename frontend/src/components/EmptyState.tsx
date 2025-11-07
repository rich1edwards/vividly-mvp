/**
 * Empty State Component
 *
 * Production-ready flexible empty state component for various scenarios
 * Features:
 * - Flexible layout with custom icon, title, description, and action button
 * - Pre-configured variants for common empty states
 * - Support for custom illustrations (optional)
 * - Responsive sizing
 * - Consistent styling with design system
 * - Accessibility (ARIA labels, semantic HTML, screen reader support)
 */

import React from 'react'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'
import {
  FileQuestion,
  Inbox,
  Search,
  AlertCircle,
  ServerCrash,
  WifiOff,
  Filter,
  Video,
  type LucideIcon,
} from 'lucide-react'

/**
 * Pre-configured empty state variants
 */
export type EmptyStateVariant =
  | 'no-videos'
  | 'no-results'
  | 'no-filtered-results'
  | 'empty-inbox'
  | 'error'
  | 'network-error'
  | 'not-found'
  | 'server-error'
  | 'custom'

/**
 * Variant configuration type
 */
interface VariantConfig {
  icon: LucideIcon
  title: string
  description: string
  iconColor: string
}

/**
 * Pre-configured variant settings
 */
const VARIANT_CONFIG: Record<EmptyStateVariant, VariantConfig | null> = {
  'no-videos': {
    icon: Video,
    title: 'No videos yet',
    description: "You haven't generated any videos yet. Create your first video to get started!",
    iconColor: 'text-vividly-blue',
  },
  'no-results': {
    icon: Search,
    title: 'No results found',
    description: 'We couldn\'t find anything matching your search. Try different keywords.',
    iconColor: 'text-muted-foreground',
  },
  'no-filtered-results': {
    icon: Filter,
    title: 'No matches found',
    description: 'No content matches your current filters. Try adjusting your filter criteria.',
    iconColor: 'text-muted-foreground',
  },
  'empty-inbox': {
    icon: Inbox,
    title: 'All caught up!',
    description: 'You have no new notifications or messages.',
    iconColor: 'text-vividly-green',
  },
  error: {
    icon: AlertCircle,
    title: 'Something went wrong',
    description: 'An unexpected error occurred. Please try again later.',
    iconColor: 'text-vividly-red',
  },
  'network-error': {
    icon: WifiOff,
    title: 'Connection lost',
    description: 'Unable to connect to the server. Please check your internet connection.',
    iconColor: 'text-vividly-red',
  },
  'not-found': {
    icon: FileQuestion,
    title: 'Not found',
    description: 'The content you\'re looking for doesn\'t exist or has been removed.',
    iconColor: 'text-muted-foreground',
  },
  'server-error': {
    icon: ServerCrash,
    title: 'Server error',
    description: 'Our servers are experiencing issues. Please try again in a few moments.',
    iconColor: 'text-vividly-red',
  },
  custom: null, // Custom variant requires manual configuration
}

export interface EmptyStateProps {
  /**
   * Pre-configured variant or 'custom' for manual configuration
   */
  variant?: EmptyStateVariant

  /**
   * Custom icon component (overrides variant icon)
   */
  icon?: LucideIcon

  /**
   * Custom title (overrides variant title)
   */
  title?: string

  /**
   * Custom description (overrides variant description)
   */
  description?: string

  /**
   * Optional illustration image URL
   */
  illustration?: string

  /**
   * Action button configuration
   */
  action?: {
    label: string
    onClick: () => void
    variant?: 'primary' | 'secondary' | 'tertiary'
  }

  /**
   * Secondary action button configuration
   */
  secondaryAction?: {
    label: string
    onClick: () => void
  }

  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * Additional CSS classes
   */
  className?: string

  /**
   * Show border
   */
  bordered?: boolean
}

/**
 * Size configuration
 */
const SIZE_CONFIG = {
  sm: {
    container: 'py-8 px-4',
    icon: 'w-12 h-12',
    title: 'text-lg',
    description: 'text-sm',
    maxWidth: 'max-w-sm',
  },
  md: {
    container: 'py-12 px-6',
    icon: 'w-16 h-16',
    title: 'text-xl',
    description: 'text-base',
    maxWidth: 'max-w-md',
  },
  lg: {
    container: 'py-16 px-8',
    icon: 'w-20 h-20',
    title: 'text-2xl',
    description: 'text-lg',
    maxWidth: 'max-w-lg',
  },
} as const

/**
 * Main Empty State Component
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'custom',
  icon: CustomIcon,
  title: customTitle,
  description: customDescription,
  illustration,
  action,
  secondaryAction,
  size = 'md',
  className,
  bordered = false,
}) => {
  // Get variant configuration
  const variantConfig = variant !== 'custom' ? VARIANT_CONFIG[variant] : null

  // Determine which props to use (custom props override variant config)
  const Icon = CustomIcon || variantConfig?.icon
  const title = customTitle || variantConfig?.title
  const description = customDescription || variantConfig?.description
  const iconColor = variantConfig?.iconColor || 'text-muted-foreground'

  // Get size configuration
  const sizeConfig = SIZE_CONFIG[size]

  // Ensure we have at least a title or description
  if (!title && !description && !Icon && !illustration) {
    console.warn('EmptyState: No content provided (title, description, icon, or illustration)')
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        sizeConfig.container,
        bordered && 'border rounded-lg bg-card',
        className
      )}
      role="status"
      aria-label={title || 'Empty state'}
    >
      <div className={cn('flex flex-col items-center', sizeConfig.maxWidth, 'w-full space-y-4')}>
        {/* Illustration or Icon */}
        {illustration ? (
          <div className="w-full max-w-xs">
            <img
              src={illustration}
              alt=""
              className="w-full h-auto object-contain"
              aria-hidden="true"
            />
          </div>
        ) : Icon ? (
          <div
            className={cn(
              'flex items-center justify-center rounded-full bg-muted p-4',
              sizeConfig.icon
            )}
            aria-hidden="true"
          >
            <Icon className={cn('w-full h-full', iconColor)} strokeWidth={1.5} />
          </div>
        ) : null}

        {/* Title */}
        {title && (
          <h3
            className={cn(
              'font-display font-semibold text-foreground',
              sizeConfig.title
            )}
          >
            {title}
          </h3>
        )}

        {/* Description */}
        {description && (
          <p className={cn('text-muted-foreground leading-relaxed', sizeConfig.description)}>
            {description}
          </p>
        )}

        {/* Actions */}
        {(action || secondaryAction) && (
          <div className="flex flex-col sm:flex-row gap-3 mt-6 w-full sm:w-auto">
            {action && (
              <Button
                variant={action.variant || 'primary'}
                size={size === 'sm' ? 'sm' : 'md'}
                onClick={action.onClick}
                className="w-full sm:w-auto"
              >
                {action.label}
              </Button>
            )}
            {secondaryAction && (
              <Button
                variant="tertiary"
                size={size === 'sm' ? 'sm' : 'md'}
                onClick={secondaryAction.onClick}
                className="w-full sm:w-auto"
              >
                {secondaryAction.label}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Pre-configured Empty State Components for common scenarios
 */

export const NoVideosEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="no-videos" {...props} />
)

export const NoResultsEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="no-results" {...props} />
)

export const NoFilteredResultsEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (
  props
) => <EmptyState variant="no-filtered-results" {...props} />

export const EmptyInboxEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="empty-inbox" {...props} />
)

export const ErrorEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="error" {...props} />
)

export const NetworkErrorEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="network-error" {...props} />
)

export const NotFoundEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="not-found" {...props} />
)

export const ServerErrorEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState variant="server-error" {...props} />
)

// Export for use in other components
export default EmptyState
