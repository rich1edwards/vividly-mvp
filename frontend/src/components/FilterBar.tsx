/**
 * Filter Bar Component
 *
 * Production-ready filter and search component for content browsing
 * Features:
 * - Search input with 300ms debouncing
 * - Filter dropdowns (subject, topic, date range, status)
 * - Sort dropdown (newest, oldest, most viewed)
 * - Clear all filters button
 * - Active filter badge count
 * - URL query parameter persistence
 * - Mobile-responsive design (collapsible drawer on small screens)
 * - Accessibility (keyboard navigation, ARIA labels, screen reader support)
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Input } from './ui/input'
import { Button } from './ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import { Badge } from './ui/badge'
import { cn } from '@/lib/utils'
import {
  Search,
  Filter,
  X,
  ChevronDown,
  SlidersHorizontal,
  Calendar as CalendarIcon,
} from 'lucide-react'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover'

/**
 * Filter options configuration
 */
export const FILTER_OPTIONS = {
  subjects: [
    'Mathematics',
    'Science',
    'History',
    'English',
    'Social Studies',
    'Computer Science',
    'Art',
    'Music',
    'Physical Education',
  ],
  statuses: [
    { value: 'all', label: 'All Status' },
    { value: 'completed', label: 'Ready' },
    { value: 'processing', label: 'Processing' },
    { value: 'failed', label: 'Failed' },
  ],
  sortOptions: [
    { value: 'newest', label: 'Newest First' },
    { value: 'oldest', label: 'Oldest First' },
    { value: 'most_viewed', label: 'Most Viewed' },
  ],
  dateRanges: [
    { value: 'all', label: 'All Time' },
    { value: 'today', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'year', label: 'This Year' },
  ],
} as const

export interface FilterBarProps {
  onFilterChange: (filters: FilterState) => void
  className?: string
  placeholder?: string
  showSubjectFilter?: boolean
  showTopicFilter?: boolean
  showDateRangeFilter?: boolean
  showStatusFilter?: boolean
  showSortFilter?: boolean
  topics?: string[] // Dynamic topic list from API
}

export interface FilterState {
  search: string
  subject: string
  topic: string
  dateRange: string
  status: string
  sort: string
}

/**
 * Get initial filter state from URL query parameters
 */
const getInitialFilters = (searchParams: URLSearchParams): FilterState => {
  return {
    search: searchParams.get('search') || '',
    subject: searchParams.get('subject') || 'all',
    topic: searchParams.get('topic') || 'all',
    dateRange: searchParams.get('dateRange') || 'all',
    status: searchParams.get('status') || 'all',
    sort: searchParams.get('sort') || 'newest',
  }
}

/**
 * Count active filters (excluding search and sort)
 */
const countActiveFilters = (filters: FilterState): number => {
  let count = 0
  if (filters.subject !== 'all') count++
  if (filters.topic !== 'all') count++
  if (filters.dateRange !== 'all') count++
  if (filters.status !== 'all') count++
  return count
}

/**
 * Main FilterBar Component
 */
export const FilterBar: React.FC<FilterBarProps> = ({
  onFilterChange,
  className,
  placeholder = 'Search videos...',
  showSubjectFilter = true,
  showTopicFilter = true,
  showDateRangeFilter = true,
  showStatusFilter = true,
  showSortFilter = true,
  topics = [],
}) => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState<FilterState>(() =>
    getInitialFilters(searchParams)
  )
  const [searchInput, setSearchInput] = useState(filters.search)
  const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false)
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null)

  // Count active filters
  const activeFilterCount = useMemo(() => countActiveFilters(filters), [filters])

  /**
   * Update URL query parameters when filters change
   */
  useEffect(() => {
    const params = new URLSearchParams()

    if (filters.search) params.set('search', filters.search)
    if (filters.subject !== 'all') params.set('subject', filters.subject)
    if (filters.topic !== 'all') params.set('topic', filters.topic)
    if (filters.dateRange !== 'all') params.set('dateRange', filters.dateRange)
    if (filters.status !== 'all') params.set('status', filters.status)
    if (filters.sort !== 'newest') params.set('sort', filters.sort)

    // Update URL without causing a re-render
    setSearchParams(params, { replace: true })

    // Notify parent component
    onFilterChange(filters)
  }, [filters, onFilterChange, setSearchParams])

  /**
   * Handle search input with 300ms debouncing
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchInput(value)

    // Clear existing timer
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }

    // Set new timer
    const timer = setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: value }))
    }, 300)

    setDebounceTimer(timer)
  }, [debounceTimer])

  /**
   * Handle filter change
   */
  const handleFilterChange = useCallback(
    (key: keyof FilterState, value: string) => {
      setFilters((prev) => ({ ...prev, [key]: value }))
    },
    []
  )

  /**
   * Clear all filters
   */
  const handleClearFilters = useCallback(() => {
    const defaultFilters: FilterState = {
      search: '',
      subject: 'all',
      topic: 'all',
      dateRange: 'all',
      status: 'all',
      sort: 'newest',
    }
    setFilters(defaultFilters)
    setSearchInput('')

    // Clear debounce timer
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      setDebounceTimer(null)
    }
  }, [debounceTimer])

  /**
   * Clear search input
   */
  const handleClearSearch = useCallback(() => {
    setSearchInput('')
    setFilters((prev) => ({ ...prev, search: '' }))

    if (debounceTimer) {
      clearTimeout(debounceTimer)
      setDebounceTimer(null)
    }
  }, [debounceTimer])

  /**
   * Cleanup debounce timer on unmount
   */
  useEffect(() => {
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
    }
  }, [debounceTimer])

  /**
   * Filter Controls Component (reusable for desktop and mobile)
   */
  const FilterControls: React.FC<{ isMobile?: boolean }> = ({ isMobile = false }) => (
    <div
      className={cn(
        'flex gap-3',
        isMobile ? 'flex-col' : 'flex-row flex-wrap items-center'
      )}
    >
      {/* Subject Filter */}
      {showSubjectFilter && (
        <div className={cn('flex flex-col gap-1.5', isMobile ? 'w-full' : 'min-w-[160px]')}>
          {isMobile && (
            <label className="text-sm font-medium text-foreground">Subject</label>
          )}
          <Select value={filters.subject} onValueChange={(value) => handleFilterChange('subject', value)}>
            <SelectTrigger aria-label="Filter by subject">
              <SelectValue placeholder="Subject" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Subjects</SelectItem>
              {FILTER_OPTIONS.subjects.map((subject) => (
                <SelectItem key={subject} value={subject}>
                  {subject}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Topic Filter */}
      {showTopicFilter && topics.length > 0 && (
        <div className={cn('flex flex-col gap-1.5', isMobile ? 'w-full' : 'min-w-[160px]')}>
          {isMobile && (
            <label className="text-sm font-medium text-foreground">Topic</label>
          )}
          <Select value={filters.topic} onValueChange={(value) => handleFilterChange('topic', value)}>
            <SelectTrigger aria-label="Filter by topic">
              <SelectValue placeholder="Topic" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Topics</SelectItem>
              {topics.map((topic) => (
                <SelectItem key={topic} value={topic}>
                  {topic}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Date Range Filter */}
      {showDateRangeFilter && (
        <div className={cn('flex flex-col gap-1.5', isMobile ? 'w-full' : 'min-w-[160px]')}>
          {isMobile && (
            <label className="text-sm font-medium text-foreground">Date Range</label>
          )}
          <Select value={filters.dateRange} onValueChange={(value) => handleFilterChange('dateRange', value)}>
            <SelectTrigger aria-label="Filter by date range">
              <SelectValue placeholder="Date Range" />
            </SelectTrigger>
            <SelectContent>
              {FILTER_OPTIONS.dateRanges.map((range) => (
                <SelectItem key={range.value} value={range.value}>
                  {range.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Status Filter */}
      {showStatusFilter && (
        <div className={cn('flex flex-col gap-1.5', isMobile ? 'w-full' : 'min-w-[160px]')}>
          {isMobile && (
            <label className="text-sm font-medium text-foreground">Status</label>
          )}
          <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
            <SelectTrigger aria-label="Filter by status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {FILTER_OPTIONS.statuses.map((status) => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Sort Filter */}
      {showSortFilter && (
        <div className={cn('flex flex-col gap-1.5', isMobile ? 'w-full' : 'min-w-[160px]')}>
          {isMobile && (
            <label className="text-sm font-medium text-foreground">Sort By</label>
          )}
          <Select value={filters.sort} onValueChange={(value) => handleFilterChange('sort', value)}>
            <SelectTrigger aria-label="Sort videos">
              <SelectValue placeholder="Sort By" />
            </SelectTrigger>
            <SelectContent>
              {FILTER_OPTIONS.sortOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  )

  return (
    <div
      className={cn(
        'bg-card border rounded-lg p-4 space-y-4 transition-all duration-200',
        className
      )}
      role="search"
      aria-label="Filter and search videos"
    >
      {/* Top Row: Search + Clear Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search Input */}
        <div className="flex-1 relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4"
            aria-hidden="true"
          />
          <input
            type="search"
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder={placeholder}
            className={cn(
              'flex w-full rounded-lg border bg-background pl-10 pr-10 py-2 text-base transition-all duration-200',
              'border-input focus:border-primary focus:ring-2 focus:ring-primary focus:ring-offset-1',
              'placeholder:text-muted-foreground focus:outline-none',
              'disabled:cursor-not-allowed disabled:opacity-50'
            )}
            aria-label="Search videos"
          />
          {searchInput && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Clear Filters Button */}
        {activeFilterCount > 0 && (
          <Button
            variant="tertiary"
            size="md"
            onClick={handleClearFilters}
            className="flex-shrink-0"
            aria-label={`Clear all filters (${activeFilterCount} active)`}
          >
            <X className="w-4 h-4" />
            Clear Filters
            {activeFilterCount > 0 && (
              <Badge variant="secondary" className="ml-2">
                {activeFilterCount}
              </Badge>
            )}
          </Button>
        )}
      </div>

      {/* Desktop: Filter Controls */}
      <div className="hidden lg:block">
        <FilterControls />
      </div>

      {/* Mobile: Collapsible Filter Controls */}
      <div className="lg:hidden">
        <Popover open={isMobileFiltersOpen} onOpenChange={setIsMobileFiltersOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="tertiary"
              size="md"
              fullWidth
              className="relative"
              aria-label="Open filter options"
              aria-expanded={isMobileFiltersOpen}
            >
              <SlidersHorizontal className="w-4 h-4" />
              Filters
              {activeFilterCount > 0 && (
                <Badge variant="default" className="ml-2">
                  {activeFilterCount}
                </Badge>
              )}
              <ChevronDown
                className={cn(
                  'w-4 h-4 ml-auto transition-transform duration-200',
                  isMobileFiltersOpen && 'rotate-180'
                )}
                aria-hidden="true"
              />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-full p-4" align="start">
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-display font-semibold text-base">Filter Options</h3>
                <button
                  onClick={() => setIsMobileFiltersOpen(false)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Close filters"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <FilterControls isMobile />
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  )
}

// Export for use in other components
export default FilterBar
