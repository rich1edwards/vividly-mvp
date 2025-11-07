/**
 * Interest Tag Component - Phase 1.2.3
 *
 * Visual interest tag with icon, color coding, and hover effects.
 * - Icon from Lucide React based on interest category
 * - Color-coded by category for visual differentiation
 * - Tooltip with interest description
 * - Accessible (WCAG AA compliant)
 * - Keyboard navigable
 */

import React from 'react'
import type { Interest } from '../types'
import { Tooltip } from './ui/Tooltip'
import { cn } from '@/lib/utils'
import {
  Dumbbell,
  Music,
  Palette,
  FlaskConical,
  BookOpen,
  Code,
  Gamepad2,
  Sparkles,
  Rocket,
  Camera,
  Plane,
  Heart,
  User,
  TrendingUp,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/**
 * Interest category to icon and color mapping
 */
const INTEREST_CONFIG: Record<string, { icon: LucideIcon; colorClass: string; hoverClass: string }> = {
  sports: {
    icon: Dumbbell,
    colorClass: 'bg-blue-100 text-blue-700 border-blue-300',
    hoverClass: 'hover:bg-blue-200 hover:border-blue-400',
  },
  music: {
    icon: Music,
    colorClass: 'bg-purple-100 text-purple-700 border-purple-300',
    hoverClass: 'hover:bg-purple-200 hover:border-purple-400',
  },
  arts: {
    icon: Palette,
    colorClass: 'bg-pink-100 text-pink-700 border-pink-300',
    hoverClass: 'hover:bg-pink-200 hover:border-pink-400',
  },
  science: {
    icon: FlaskConical,
    colorClass: 'bg-green-100 text-green-700 border-green-300',
    hoverClass: 'hover:bg-green-200 hover:border-green-400',
  },
  literature: {
    icon: BookOpen,
    colorClass: 'bg-amber-100 text-amber-700 border-amber-300',
    hoverClass: 'hover:bg-amber-200 hover:border-amber-400',
  },
  technology: {
    icon: Code,
    colorClass: 'bg-indigo-100 text-indigo-700 border-indigo-300',
    hoverClass: 'hover:bg-indigo-200 hover:border-indigo-400',
  },
  gaming: {
    icon: Gamepad2,
    colorClass: 'bg-violet-100 text-violet-700 border-violet-300',
    hoverClass: 'hover:bg-violet-200 hover:border-violet-400',
  },
  creativity: {
    icon: Sparkles,
    colorClass: 'bg-fuchsia-100 text-fuchsia-700 border-fuchsia-300',
    hoverClass: 'hover:bg-fuchsia-200 hover:border-fuchsia-400',
  },
  adventure: {
    icon: Rocket,
    colorClass: 'bg-orange-100 text-orange-700 border-orange-300',
    hoverClass: 'hover:bg-orange-200 hover:border-orange-400',
  },
  photography: {
    icon: Camera,
    colorClass: 'bg-cyan-100 text-cyan-700 border-cyan-300',
    hoverClass: 'hover:bg-cyan-200 hover:border-cyan-400',
  },
  travel: {
    icon: Plane,
    colorClass: 'bg-sky-100 text-sky-700 border-sky-300',
    hoverClass: 'hover:bg-sky-200 hover:border-sky-400',
  },
  wellness: {
    icon: Heart,
    colorClass: 'bg-rose-100 text-rose-700 border-rose-300',
    hoverClass: 'hover:bg-rose-200 hover:border-rose-400',
  },
  personal: {
    icon: User,
    colorClass: 'bg-gray-100 text-gray-700 border-gray-300',
    hoverClass: 'hover:bg-gray-200 hover:border-gray-400',
  },
  // Default fallback
  default: {
    icon: TrendingUp,
    colorClass: 'bg-slate-100 text-slate-700 border-slate-300',
    hoverClass: 'hover:bg-slate-200 hover:border-slate-400',
  },
}

/**
 * Get icon and colors for an interest based on its category
 */
const getInterestConfig = (category: string | null) => {
  if (!category) return INTEREST_CONFIG.default
  const normalizedCategory = category.toLowerCase()
  return INTEREST_CONFIG[normalizedCategory] || INTEREST_CONFIG.default
}

interface InterestTagProps {
  interest: Interest
  selected?: boolean
  onClick?: (interest: Interest) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
}

/**
 * InterestTag Component
 *
 * Displays an interest as a visual tag with icon, color, and tooltip.
 */
export const InterestTag: React.FC<InterestTagProps> = ({
  interest,
  selected = false,
  onClick,
  disabled = false,
  size = 'md',
}) => {
  const config = getInterestConfig(interest.category)
  const Icon = config.icon

  // Size classes
  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-xs gap-1.5',
    md: 'px-3 py-2 text-sm gap-2',
    lg: 'px-4 py-2.5 text-base gap-2.5',
  }

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }

  const handleClick = () => {
    if (!disabled && onClick) {
      onClick(interest)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!disabled && onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onClick(interest)
    }
  }

  const tag = (
    <button
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      className={cn(
        'inline-flex items-center rounded-lg border-2 font-medium transition-all',
        'focus:outline-none focus:ring-2 focus:ring-vividly-blue focus:ring-offset-2',
        sizeClasses[size],
        config.colorClass,
        onClick && !disabled && config.hoverClass,
        onClick && !disabled && 'cursor-pointer transform hover:scale-105 hover:shadow-md active:scale-100',
        selected && 'ring-2 ring-vividly-blue ring-offset-2 shadow-md',
        disabled && 'opacity-50 cursor-not-allowed',
        !onClick && 'cursor-default'
      )}
      type="button"
      aria-pressed={selected}
      aria-disabled={disabled}
    >
      <Icon className={iconSizes[size]} aria-hidden="true" />
      <span>{interest.name}</span>
    </button>
  )

  // Wrap with tooltip if description exists
  if (interest.description) {
    return (
      <Tooltip
        content={
          <div className="max-w-xs">
            <div className="font-semibold mb-1">{interest.name}</div>
            <div className="text-xs opacity-90">{interest.description}</div>
          </div>
        }
        delayDuration={300}
      >
        {tag}
      </Tooltip>
    )
  }

  return tag
}

/**
 * InterestTagGrid Component
 *
 * Grid layout for displaying multiple interest tags
 */
interface InterestTagGridProps {
  interests: Interest[]
  selectedInterest?: Interest | null
  onInterestSelect?: (interest: Interest) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  maxColumns?: number
}

export const InterestTagGrid: React.FC<InterestTagGridProps> = ({
  interests,
  selectedInterest,
  onInterestSelect,
  disabled = false,
  size = 'md',
  maxColumns = 4,
}) => {
  // Sort interests by category and display_order
  const sortedInterests = [...interests].sort((a, b) => {
    // First by category
    const catA = a.category || 'zzz'
    const catB = b.category || 'zzz'
    if (catA !== catB) return catA.localeCompare(catB)

    // Then by display_order
    const orderA = a.display_order ?? 9999
    const orderB = b.display_order ?? 9999
    if (orderA !== orderB) return orderA - orderB

    // Finally by name
    return a.name.localeCompare(b.name)
  })

  const gridColsClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  }[maxColumns] || 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'

  return (
    <div className={cn('grid gap-3', gridColsClass)}>
      {sortedInterests.map((interest) => (
        <InterestTag
          key={interest.interest_id}
          interest={interest}
          selected={selectedInterest?.interest_id === interest.interest_id}
          onClick={onInterestSelect}
          disabled={disabled}
          size={size}
        />
      ))}
    </div>
  )
}
