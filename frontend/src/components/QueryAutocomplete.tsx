/**
 * QueryAutocomplete Component
 *
 * Provides autocomplete suggestions for query input based on past successful queries
 * Features:
 * - Fuzzy search matching
 * - Keyboard navigation (arrow keys, enter to select, escape to close)
 * - Mobile-friendly
 * - Fast performance (<200ms response time)
 * - Cached suggestions
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { Clock, ChevronRight } from 'lucide-react'
import { fuzzySearch, extractQueriesFromHistory } from '../utils/fuzzySearch'
import { contentApi } from '../api/content'
import type { GeneratedContent } from '../types'

interface QueryAutocompleteProps {
  /** Current query value */
  query: string
  /** Callback when a suggestion is selected */
  onSelect: (suggestion: string) => void
  /** Optional className for styling */
  className?: string
}

interface AutocompleteCache {
  queries: string[]
  timestamp: number
}

const CACHE_KEY = 'vividly_autocomplete_cache'
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

/**
 * QueryAutocomplete component
 */
export default function QueryAutocomplete({
  query,
  onSelect,
  className = ''
}: QueryAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)
  const [cachedQueries, setCachedQueries] = useState<string[]>([])

  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  /**
   * Load cached queries from localStorage
   */
  const loadCachedQueries = useCallback((): string[] => {
    try {
      const cached = localStorage.getItem(CACHE_KEY)
      if (!cached) return []

      const data: AutocompleteCache = JSON.parse(cached)
      const now = Date.now()

      // Check if cache is still valid
      if (now - data.timestamp < CACHE_DURATION) {
        return data.queries
      }

      // Cache expired, remove it
      localStorage.removeItem(CACHE_KEY)
      return []
    } catch (error) {
      console.error('Failed to load cached queries:', error)
      return []
    }
  }, [])

  /**
   * Save queries to localStorage cache
   */
  const saveCachedQueries = useCallback((queries: string[]) => {
    try {
      const data: AutocompleteCache = {
        queries,
        timestamp: Date.now()
      }
      localStorage.setItem(CACHE_KEY, JSON.stringify(data))
    } catch (error) {
      console.error('Failed to save cached queries:', error)
    }
  }, [])

  /**
   * Fetch content history and extract queries
   */
  const fetchAndCacheQueries = useCallback(async () => {
    setIsLoading(true)
    try {
      const history: GeneratedContent[] = await contentApi.getContentHistory()
      const queries = extractQueriesFromHistory(history)

      setCachedQueries(queries)
      saveCachedQueries(queries)

      return queries
    } catch (error) {
      console.error('Failed to fetch content history:', error)
      return []
    } finally {
      setIsLoading(false)
    }
  }, [saveCachedQueries])

  /**
   * Initialize cached queries on mount
   */
  useEffect(() => {
    const cached = loadCachedQueries()

    if (cached.length > 0) {
      setCachedQueries(cached)
    } else {
      // No cache, fetch from API
      fetchAndCacheQueries()
    }
  }, [loadCachedQueries, fetchAndCacheQueries])

  /**
   * Update suggestions when query changes
   */
  useEffect(() => {
    const startTime = performance.now()

    if (!query || query.trim().length === 0) {
      setSuggestions([])
      setShowSuggestions(false)
      setSelectedIndex(-1)
      return
    }

    // Perform fuzzy search
    const matches = fuzzySearch(query, cachedQueries, 0.3, 5)

    const endTime = performance.now()
    const duration = endTime - startTime

    // Log performance (should be < 200ms)
    if (duration > 200) {
      console.warn(`Autocomplete search took ${duration.toFixed(2)}ms (target: <200ms)`)
    }

    setSuggestions(matches)
    setShowSuggestions(matches.length > 0)
    setSelectedIndex(-1)
  }, [query, cachedQueries])

  /**
   * Handle suggestion selection
   */
  const handleSelectSuggestion = useCallback((suggestion: string) => {
    onSelect(suggestion)
    setShowSuggestions(false)
    setSelectedIndex(-1)
  }, [onSelect])

  /**
   * Handle keyboard navigation
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!showSuggestions || suggestions.length === 0) return

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault()
          setSelectedIndex(prev =>
            prev < suggestions.length - 1 ? prev + 1 : 0
          )
          break

        case 'ArrowUp':
          event.preventDefault()
          setSelectedIndex(prev =>
            prev > 0 ? prev - 1 : suggestions.length - 1
          )
          break

        case 'Enter':
          event.preventDefault()
          if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
            handleSelectSuggestion(suggestions[selectedIndex])
          }
          break

        case 'Escape':
          event.preventDefault()
          setShowSuggestions(false)
          setSelectedIndex(-1)
          break

        default:
          break
      }
    }

    // Only attach when suggestions are showing
    if (showSuggestions) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [showSuggestions, suggestions, selectedIndex, handleSelectSuggestion])

  /**
   * Handle click outside to close suggestions
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  /**
   * Scroll selected suggestion into view
   */
  useEffect(() => {
    if (selectedIndex >= 0 && suggestionsRef.current) {
      const selectedElement = suggestionsRef.current.children[selectedIndex] as HTMLElement
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        })
      }
    }
  }, [selectedIndex])

  return (
    <div className={`relative ${className}`}>
      {/* Screen reader announcement for suggestions */}
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {showSuggestions && suggestions.length > 0 && (
          `${suggestions.length} suggestion${suggestions.length === 1 ? '' : 's'} available. Use arrow keys to navigate.`
        )}
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto"
          role="listbox"
          aria-label="Query suggestions"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={`${suggestion}-${index}`}
              type="button"
              className={`
                w-full px-4 py-3 text-left flex items-center justify-between gap-3
                transition-colors duration-150
                ${index === selectedIndex
                  ? 'bg-vividly-blue/10 text-vividly-blue'
                  : 'hover:bg-gray-50 text-gray-900'
                }
                ${index === 0 ? 'rounded-t-lg' : ''}
                ${index === suggestions.length - 1 ? 'rounded-b-lg' : 'border-b border-gray-100'}
              `}
              onClick={() => handleSelectSuggestion(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
              role="option"
              aria-selected={index === selectedIndex}
              tabIndex={-1}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <Clock className={`
                  w-4 h-4 flex-shrink-0
                  ${index === selectedIndex ? 'text-vividly-blue' : 'text-gray-400'}
                `} />
                <span className="truncate text-sm font-medium">
                  {suggestion}
                </span>
              </div>

              <ChevronRight className={`
                w-4 h-4 flex-shrink-0
                ${index === selectedIndex ? 'text-vividly-blue' : 'text-gray-300'}
              `} />
            </button>
          ))}

          {/* Footer hint */}
          <div className="px-4 py-2 text-xs text-gray-500 bg-gray-50 border-t border-gray-100 rounded-b-lg">
            Press <kbd className="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-700 font-mono">↑</kbd> <kbd className="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-700 font-mono">↓</kbd> to navigate, <kbd className="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-700 font-mono">Enter</kbd> to select, <kbd className="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-700 font-mono">Esc</kbd> to close
          </div>
        </div>
      )}

      {/* Loading indicator (hidden, for screen readers) */}
      {isLoading && (
        <div className="sr-only" role="status" aria-live="polite">
          Loading suggestions...
        </div>
      )}
    </div>
  )
}

/**
 * Export keyboard handler for parent component
 */
export { QueryAutocomplete }
