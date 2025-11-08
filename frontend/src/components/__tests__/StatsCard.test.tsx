/**
 * StatsCard Component Tests
 *
 * Comprehensive test suite for StatsCard component covering:
 * - Rendering with various prop combinations
 * - Trend indicators (up/down/neutral)
 * - Loading states
 * - Click interactions
 * - Keyboard accessibility
 * - Different size variants
 * - Specialized variants (Count, Percentage, Currency, Time)
 * - ARIA attributes and screen reader support
 *
 * Testing Strategy:
 * - Unit tests for component rendering
 * - Integration tests for user interactions
 * - Accessibility tests (ARIA, keyboard navigation)
 * - Visual regression tests (snapshot)
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Users, TrendingUp } from 'lucide-react'
import {
  StatsCard,
  CountStatsCard,
  PercentageStatsCard,
  CurrencyStatsCard,
  TimeStatsCard,
  LoadingStatsCard,
} from '../StatsCard'

describe('StatsCard', () => {
  // ============================================================================
  // Basic Rendering
  // ============================================================================

  describe('Basic Rendering', () => {
    it('renders with minimal props', () => {
      render(<StatsCard title="Test Card" value={42} />)

      expect(screen.getByText('Test Card')).toBeInTheDocument()
      expect(screen.getByText('42')).toBeInTheDocument()
    })

    it('renders with all props', () => {
      const handleClick = jest.fn()

      render(
        <StatsCard
          title="Total Students"
          value={156}
          icon={Users}
          iconColor="text-blue-600"
          iconBgColor="bg-blue-100"
          trend={{ value: 12, direction: 'up' }}
          subtitle="Active this week"
          onClick={handleClick}
          size="md"
        />
      )

      expect(screen.getByText('Total Students')).toBeInTheDocument()
      expect(screen.getByText('156')).toBeInTheDocument()
      expect(screen.getByText('Active this week')).toBeInTheDocument()
      expect(screen.getByText('12%')).toBeInTheDocument()
    })

    it('formats number values with commas', () => {
      render(<StatsCard title="Test" value={1234567} />)

      expect(screen.getByText('1,234,567')).toBeInTheDocument()
    })

    it('displays string values as-is', () => {
      render(<StatsCard title="Test" value="Custom Value" />)

      expect(screen.getByText('Custom Value')).toBeInTheDocument()
    })

    it('renders with custom class name', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} className="custom-class" />
      )

      const card = container.firstChild
      expect(card).toHaveClass('custom-class')
    })
  })

  // ============================================================================
  // Icon Rendering
  // ============================================================================

  describe('Icon Rendering', () => {
    it('renders icon when provided', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} icon={Users} />
      )

      // Check for Users icon (svg)
      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })

    it('applies icon color classes', () => {
      const { container } = render(
        <StatsCard
          title="Test"
          value={42}
          icon={Users}
          iconColor="text-blue-600"
          iconBgColor="bg-blue-100"
        />
      )

      const iconContainer = container.querySelector('.bg-blue-100')
      expect(iconContainer).toBeInTheDocument()

      const icon = container.querySelector('.text-blue-600')
      expect(icon).toBeInTheDocument()
    })

    it('does not render icon div when icon not provided', () => {
      const { container } = render(<StatsCard title="Test" value={42} />)

      const iconContainer = container.querySelector('.rounded-full')
      expect(iconContainer).not.toBeInTheDocument()
    })
  })

  // ============================================================================
  // Trend Indicators
  // ============================================================================

  describe('Trend Indicators', () => {
    it('renders upward trend with green color', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: 12, direction: 'up' }}
        />
      )

      const trendElement = screen.getByText('12%').closest('div')
      expect(trendElement).toHaveClass('text-green-600')
    })

    it('renders downward trend with red color', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: 8, direction: 'down' }}
        />
      )

      const trendElement = screen.getByText('8%').closest('div')
      expect(trendElement).toHaveClass('text-red-600')
    })

    it('renders neutral trend with gray color', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: 0, direction: 'neutral' }}
        />
      )

      const trendElement = screen.getByText('0%').closest('div')
      expect(trendElement).toHaveClass('text-gray-600')
    })

    it('displays trend with custom label', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: 12, direction: 'up', label: 'vs last week' }}
        />
      )

      expect(screen.getByText('vs last week')).toBeInTheDocument()
    })

    it('displays trend without percentage symbol when isPercentage=false', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: 5, direction: 'up', isPercentage: false }}
        />
      )

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.queryByText('5%')).not.toBeInTheDocument()
    })

    it('displays absolute value for negative trends', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: -15, direction: 'down' }}
        />
      )

      // Should display 15% (absolute value)
      expect(screen.getByText('15%')).toBeInTheDocument()
    })
  })

  // ============================================================================
  // Size Variants
  // ============================================================================

  describe('Size Variants', () => {
    it('renders small size correctly', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} size="sm" />
      )

      const card = container.firstChild
      expect(card).toHaveClass('h-24')
    })

    it('renders medium size correctly', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} size="md" />
      )

      const card = container.firstChild
      expect(card).toHaveClass('h-32')
    })

    it('renders large size correctly', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} size="lg" />
      )

      const card = container.firstChild
      expect(card).toHaveClass('h-40')
    })
  })

  // ============================================================================
  // Loading State
  // ============================================================================

  describe('Loading State', () => {
    it('renders loading skeleton when loading=true', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} loading={true} />
      )

      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })

    it('does not render content when loading', () => {
      render(<StatsCard title="Test" value={42} loading={true} />)

      expect(screen.queryByText('Test')).not.toBeInTheDocument()
      expect(screen.queryByText('42')).not.toBeInTheDocument()
    })

    it('LoadingStatsCard renders skeleton', () => {
      const { container } = render(<LoadingStatsCard size="md" />)

      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })
  })

  // ============================================================================
  // Click Interactions
  // ============================================================================

  describe('Click Interactions', () => {
    it('calls onClick when card is clicked', () => {
      const handleClick = jest.fn()

      render(<StatsCard title="Test" value={42} onClick={handleClick} />)

      const card = screen.getByRole('button')
      fireEvent.click(card)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when clickable=false', () => {
      const handleClick = jest.fn()

      render(
        <StatsCard
          title="Test"
          value={42}
          onClick={handleClick}
          clickable={false}
        />
      )

      // Should not have button role
      const card = screen.queryByRole('button')
      expect(card).not.toBeInTheDocument()

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('applies hover styles when clickable', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} onClick={() => {}} />
      )

      const card = container.firstChild
      expect(card).toHaveClass('cursor-pointer')
      expect(card).toHaveClass('hover:shadow-lg')
    })
  })

  // ============================================================================
  // Keyboard Accessibility
  // ============================================================================

  describe('Keyboard Accessibility', () => {
    it('handles Enter key press', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()

      render(<StatsCard title="Test" value={42} onClick={handleClick} />)

      const card = screen.getByRole('button')
      card.focus()
      await user.keyboard('{Enter}')

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('handles Space key press', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()

      render(<StatsCard title="Test" value={42} onClick={handleClick} />)

      const card = screen.getByRole('button')
      card.focus()
      await user.keyboard(' ')

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('is focusable when clickable', () => {
      render(<StatsCard title="Test" value={42} onClick={() => {}} />)

      const card = screen.getByRole('button')
      expect(card).toHaveAttribute('tabIndex', '0')
    })

    it('is not focusable when not clickable', () => {
      render(<StatsCard title="Test" value={42} />)

      const card = screen.queryByRole('button')
      expect(card).not.toBeInTheDocument()
    })
  })

  // ============================================================================
  // ARIA Attributes
  // ============================================================================

  describe('ARIA Attributes', () => {
    it('has default ARIA label', () => {
      render(<StatsCard title="Total Students" value={42} subtitle="Active" />)

      const card = screen.getByLabelText(/Total Students: 42, Active/)
      expect(card).toBeInTheDocument()
    })

    it('has ARIA label with trend', () => {
      render(
        <StatsCard
          title="Students"
          value={42}
          trend={{ value: 12, direction: 'up' }}
        />
      )

      const card = screen.getByLabelText(/trending up by 12%/)
      expect(card).toBeInTheDocument()
    })

    it('uses custom ARIA label when provided', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          ariaLabel="Custom accessibility label"
        />
      )

      const card = screen.getByLabelText('Custom accessibility label')
      expect(card).toBeInTheDocument()
    })

    it('trend has role=status for screen readers', () => {
      render(
        <StatsCard
          title="Test"
          value={42}
          trend={{ value: 12, direction: 'up' }}
        />
      )

      const trendStatus = screen.getByRole('status')
      expect(trendStatus).toBeInTheDocument()
    })
  })

  // ============================================================================
  // Custom Formatting
  // ============================================================================

  describe('Custom Formatting', () => {
    it('uses custom formatValue function', () => {
      const formatValue = (value: number | string) => {
        return `$${value} USD`
      }

      render(<StatsCard title="Test" value={42} formatValue={formatValue} />)

      expect(screen.getByText('$42 USD')).toBeInTheDocument()
    })
  })

  // ============================================================================
  // Specialized Variants
  // ============================================================================

  describe('Specialized Variants', () => {
    describe('CountStatsCard', () => {
      it('formats count with commas', () => {
        render(<CountStatsCard title="Total" value={1234567} />)

        expect(screen.getByText('1,234,567')).toBeInTheDocument()
      })
    })

    describe('PercentageStatsCard', () => {
      it('formats percentage with % symbol', () => {
        render(<PercentageStatsCard title="Completion Rate" value={87.5} />)

        expect(screen.getByText('87.5%')).toBeInTheDocument()
      })
    })

    describe('CurrencyStatsCard', () => {
      it('formats currency in USD', () => {
        render(<CurrencyStatsCard title="Revenue" value={1234.56} />)

        expect(screen.getByText('$1,234.56')).toBeInTheDocument()
      })

      it('formats currency in EUR', () => {
        render(
          <CurrencyStatsCard title="Revenue" value={1234.56} currency="EUR" />
        )

        expect(screen.getByText(/1,234.56/)).toBeInTheDocument()
      })
    })

    describe('TimeStatsCard', () => {
      it('formats hours and minutes', () => {
        render(<TimeStatsCard title="Watch Time" value={3665} />)
        // 3665 seconds = 1h 1m

        expect(screen.getByText('1h 1m')).toBeInTheDocument()
      })

      it('formats minutes and seconds', () => {
        render(<TimeStatsCard title="Watch Time" value={125} />)
        // 125 seconds = 2m 5s

        expect(screen.getByText('2m 5s')).toBeInTheDocument()
      })

      it('formats seconds only', () => {
        render(<TimeStatsCard title="Watch Time" value={45} />)

        expect(screen.getByText('45s')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // Snapshot Tests
  // ============================================================================

  describe('Snapshot Tests', () => {
    it('matches snapshot with all props', () => {
      const { container } = render(
        <StatsCard
          title="Total Students"
          value={156}
          icon={Users}
          iconColor="text-blue-600"
          trend={{ value: 12, direction: 'up' }}
          subtitle="Active this week"
          onClick={() => {}}
          size="md"
        />
      )

      expect(container).toMatchSnapshot()
    })

    it('matches snapshot for loading state', () => {
      const { container } = render(
        <StatsCard title="Test" value={42} loading={true} />
      )

      expect(container).toMatchSnapshot()
    })
  })
})
