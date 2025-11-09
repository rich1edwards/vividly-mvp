/**
 * StatsCard Component (Phase 2.1.1)
 *
 * Reusable metric display card for dashboards with trend indicators and drill-down.
 * Designed for teacher dashboards to show class metrics, student engagement, and content stats.
 *
 * Features:
 * - Title, value, and optional subtitle display
 * - Trend indicator with percentage change and direction (up/down/neutral)
 * - Icon support with color customization
 * - Loading skeleton state
 * - Click handler for drill-down navigation
 * - Multiple size variants (sm, md, lg)
 * - Responsive design with mobile support
 * - Accessibility (ARIA labels, keyboard navigation, semantic HTML)
 * - Animation on hover and data updates
 *
 * Architecture:
 * - Built on shadcn/ui Card component
 * - Uses Lucide React icons
 * - TypeScript with comprehensive prop types
 * - Tailwind CSS for styling
 * - Follows Vividly design system
 *
 * Usage:
 * ```tsx
 * import { StatsCard } from './components/StatsCard'
 * import { Users, TrendingUp } from 'lucide-react'
 *
 * <StatsCard
 *   title="Total Students"
 *   value={42}
 *   icon={Users}
 *   iconColor="text-blue-600"
 *   trend={{ value: 12, direction: 'up' }}
 *   subtitle="Active this week"
 *   onClick={() => navigate('/students')}
 *   loading={false}
 * />
 * ```
 */

import React from 'react'
import { LucideIcon, TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'
import { cn } from '../lib/utils'

// ============================================================================
// Types
// ============================================================================

export type TrendDirection = 'up' | 'down' | 'neutral'

export interface TrendData {
  /**
   * Trend value (percentage or absolute number)
   */
  value: number
  /**
   * Direction of trend
   */
  direction: TrendDirection
  /**
   * Custom label for trend (e.g., "vs last week")
   */
  label?: string
  /**
   * Whether value is percentage (shows % symbol)
   */
  isPercentage?: boolean
}

export type StatsCardSize = 'sm' | 'md' | 'lg'

export interface StatsCardProps {
  /**
   * Card title (e.g., "Total Students")
   */
  title: string
  /**
   * Primary value to display (number or string)
   */
  value: number | string
  /**
   * Optional icon component from Lucide React
   */
  icon?: LucideIcon
  /**
   * Icon color class (Tailwind)
   */
  iconColor?: string
  /**
   * Icon background color class (Tailwind)
   */
  iconBgColor?: string
  /**
   * Trend data with value and direction
   */
  trend?: TrendData
  /**
   * Subtitle or description text
   */
  subtitle?: string
  /**
   * Click handler for drill-down navigation
   */
  onClick?: () => void
  /**
   * Loading state (shows skeleton)
   */
  loading?: boolean
  /**
   * Size variant
   */
  size?: StatsCardSize
  /**
   * Custom CSS class
   */
  className?: string
  /**
   * Whether card is clickable (shows hover effect)
   */
  clickable?: boolean
  /**
   * Accent color for value (Tailwind class)
   */
  valueColor?: string
  /**
   * Format function for value display
   */
  formatValue?: (value: number | string) => string
  /**
   * ARIA label for accessibility
   */
  ariaLabel?: string
}

// ============================================================================
// Helper Components
// ============================================================================

/**
 * Trend Indicator Component
 */
const TrendIndicator: React.FC<{ trend: TrendData }> = ({ trend }) => {
  const { value, direction, label, isPercentage = true } = trend

  const getTrendColor = () => {
    switch (direction) {
      case 'up':
        return 'text-green-600 bg-green-50'
      case 'down':
        return 'text-red-600 bg-red-50'
      case 'neutral':
        return 'text-gray-600 bg-gray-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getTrendIcon = () => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="h-3 w-3" />
      case 'down':
        return <TrendingDown className="h-3 w-3" />
      case 'neutral':
        return <Minus className="h-3 w-3" />
      default:
        return <Minus className="h-3 w-3" />
    }
  }

  const formattedValue = Math.abs(value)
  const displayValue = isPercentage ? `${formattedValue}%` : formattedValue.toString()

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
        getTrendColor()
      )}
      role="status"
      aria-label={`Trend: ${direction} by ${displayValue}${label ? ` ${label}` : ''}`}
    >
      {getTrendIcon()}
      <span>{displayValue}</span>
      {label && <span className="ml-1 text-xs opacity-75">{label}</span>}
    </div>
  )
}

/**
 * Loading Skeleton Component
 */
const StatsCardSkeleton: React.FC<{ size: StatsCardSize }> = ({ size }) => {
  const getSkeletonSize = () => {
    switch (size) {
      case 'sm':
        return 'h-24'
      case 'md':
        return 'h-32'
      case 'lg':
        return 'h-40'
      default:
        return 'h-32'
    }
  }

  return (
    <Card className={cn('animate-pulse', getSkeletonSize())}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="h-4 w-24 bg-gray-200 rounded" />
          <div className="h-8 w-8 bg-gray-200 rounded-full" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="h-8 w-16 bg-gray-200 rounded" />
          <div className="h-3 w-20 bg-gray-200 rounded" />
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  iconColor = 'text-gray-600',
  iconBgColor = 'bg-gray-100',
  trend,
  subtitle,
  onClick,
  loading = false,
  size = 'md',
  className,
  clickable = !!onClick,
  valueColor = 'text-gray-900',
  formatValue,
  ariaLabel,
}) => {
  // Loading state
  if (loading) {
    return <StatsCardSkeleton size={size} />
  }

  // Format value for display
  const displayValue = formatValue
    ? formatValue(value)
    : typeof value === 'number'
    ? value.toLocaleString()
    : value

  // Size classes
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          card: 'h-24',
          icon: 'h-6 w-6 p-1.5',
          value: 'text-2xl',
          title: 'text-xs',
        }
      case 'md':
        return {
          card: 'h-32',
          icon: 'h-10 w-10 p-2',
          value: 'text-3xl',
          title: 'text-sm',
        }
      case 'lg':
        return {
          card: 'h-40',
          icon: 'h-12 w-12 p-2.5',
          value: 'text-4xl',
          title: 'text-base',
        }
      default:
        return {
          card: 'h-32',
          icon: 'h-10 w-10 p-2',
          value: 'text-3xl',
          title: 'text-sm',
        }
    }
  }

  const sizeClasses = getSizeClasses()

  // Click handler
  const handleClick = () => {
    if (onClick) {
      onClick()
    }
  }

  // Keyboard handler
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (clickable && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <Card
      className={cn(
        sizeClasses.card,
        'transition-all duration-200',
        clickable && [
          'cursor-pointer',
          'hover:shadow-lg hover:scale-[1.02]',
          'active:scale-[0.98]',
          'focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:ring-offset-2',
        ],
        className
      )}
      onClick={clickable ? handleClick : undefined}
      onKeyDown={clickable ? handleKeyDown : undefined}
      tabIndex={clickable ? 0 : undefined}
      role={clickable ? 'button' : undefined}
      aria-label={
        ariaLabel ||
        `${title}: ${displayValue}${subtitle ? `, ${subtitle}` : ''}${
          trend ? `, trending ${trend.direction} by ${trend.value}${trend.isPercentage !== false ? '%' : ''}` : ''
        }`
      }
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className={cn('font-medium', sizeClasses.title)}>
            {title}
          </CardTitle>
          {Icon && (
            <div
              className={cn(
                'rounded-full flex items-center justify-center',
                sizeClasses.icon,
                iconBgColor
              )}
            >
              <Icon className={cn('h-full w-full', iconColor)} />
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-2">
          {/* Value */}
          <div
            className={cn(
              'font-bold tracking-tight',
              sizeClasses.value,
              valueColor
            )}
          >
            {displayValue}
          </div>

          {/* Subtitle and Trend */}
          <div className="flex items-center justify-between gap-2">
            {subtitle && (
              <CardDescription className="text-xs">{subtitle}</CardDescription>
            )}
            {trend && <TrendIndicator trend={trend} />}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Specialized StatsCard Variants
// ============================================================================

/**
 * Loading StatsCard (convenience component)
 */
export const LoadingStatsCard: React.FC<{
  size?: StatsCardSize
  className?: string
}> = ({ size = 'md', className }) => {
  return <StatsCardSkeleton size={size} />
}

/**
 * CountStatsCard (formatted for counts/integers)
 */
export const CountStatsCard: React.FC<Omit<StatsCardProps, 'formatValue'>> = (
  props
) => {
  const formatValue = (value: number | string) => {
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
    return value
  }

  return <StatsCard {...props} formatValue={formatValue} />
}

/**
 * PercentageStatsCard (formatted for percentages)
 */
export const PercentageStatsCard: React.FC<
  Omit<StatsCardProps, 'formatValue' | 'value'> & { value: number }
> = (props) => {
  const formatValue = (value: number | string) => {
    if (typeof value === 'number') {
      return `${value.toFixed(1)}%`
    }
    return value
  }

  return <StatsCard {...props} formatValue={formatValue} />
}

/**
 * CurrencyStatsCard (formatted for currency)
 */
export const CurrencyStatsCard: React.FC<
  Omit<StatsCardProps, 'formatValue' | 'value'> & {
    value: number
    currency?: string
  }
> = ({ currency = 'USD', ...props }) => {
  const formatValue = (value: number | string) => {
    if (typeof value === 'number') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
      }).format(value)
    }
    return value
  }

  return <StatsCard {...props} formatValue={formatValue} />
}

/**
 * TimeStatsCard (formatted for time duration)
 */
export const TimeStatsCard: React.FC<
  Omit<StatsCardProps, 'formatValue' | 'value'> & {
    value: number // seconds
  }
> = (props) => {
  const formatValue = (value: number | string) => {
    if (typeof value === 'number') {
      const hours = Math.floor(value / 3600)
      const minutes = Math.floor((value % 3600) / 60)
      const seconds = Math.floor(value % 60)

      if (hours > 0) {
        return `${hours}h ${minutes}m`
      } else if (minutes > 0) {
        return `${minutes}m ${seconds}s`
      } else {
        return `${seconds}s`
      }
    }
    return value
  }

  return <StatsCard {...props} formatValue={formatValue} />
}

export default StatsCard
