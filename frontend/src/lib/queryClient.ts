/**
 * React Query Client Configuration (Phase 2.2)
 *
 * Centralized configuration for TanStack Query (React Query) v5.
 * Provides server state management with optimized caching, retries, and error handling.
 *
 * Key Features:
 * - Smart retry logic (no retries for 4xx errors, retry for 5xx)
 * - Stale-while-revalidate caching strategy
 * - Error handling with custom logger
 * - Optimistic updates support
 * - DevTools integration in development
 *
 * Usage:
 * ```tsx
 * import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
 * import { queryClient } from './lib/queryClient'
 *
 * <QueryClientProvider client={queryClient}>
 *   <App />
 * </QueryClientProvider>
 * ```
 */

import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query'

/**
 * Custom error logger
 * In production, this would send to a monitoring service (Sentry, LogRocket, etc.)
 */
const logError = (error: unknown, query?: any) => {
  console.error('[React Query Error]', {
    error,
    query: query?.queryKey,
    timestamp: new Date().toISOString(),
  })

  // TODO: Send to monitoring service in production
  // if (import.meta.env.PROD) {
  //   Sentry.captureException(error, {
  //     tags: {
  //       component: 'ReactQuery',
  //       queryKey: JSON.stringify(query?.queryKey),
  //     },
  //   })
  // }
}

/**
 * Determine if error should retry
 * - Don't retry client errors (4xx)
 * - Retry server errors (5xx)
 * - Retry network errors
 */
const shouldRetry = (failureCount: number, error: any): boolean => {
  // Max 3 retries
  if (failureCount >= 3) return false

  // Don't retry if it's a client error (4xx)
  if (error?.response?.status && error.response.status >= 400 && error.response.status < 500) {
    return false
  }

  // Retry server errors (5xx) and network errors
  return true
}

/**
 * Query Cache Configuration
 * Handles errors for all queries globally
 */
const queryCache = new QueryCache({
  onError: (error, query) => {
    logError(error, query)
  },
})

/**
 * Mutation Cache Configuration
 * Handles errors for all mutations globally
 */
const mutationCache = new MutationCache({
  onError: (error, _variables, _context, mutation) => {
    logError(error, { mutationKey: mutation.options.mutationKey })
  },
})

/**
 * React Query Client Instance
 *
 * Default Options:
 * - staleTime: 5 minutes (data considered fresh for 5 min)
 * - cacheTime: 10 minutes (unused data kept in cache for 10 min)
 * - retry: Smart retry logic (don't retry 4xx, retry 5xx up to 3 times)
 * - refetchOnWindowFocus: true (refetch when user returns to tab)
 * - refetchOnReconnect: true (refetch when internet reconnects)
 */
export const queryClient = new QueryClient({
  queryCache,
  mutationCache,
  defaultOptions: {
    queries: {
      // Stale-while-revalidate caching strategy
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime in v4)

      // Retry configuration
      retry: shouldRetry,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch configuration
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      refetchOnMount: true,

      // Error handling
      throwOnError: false, // Don't throw errors, handle them in components
    },
    mutations: {
      // Retry mutations only once
      retry: 1,
      retryDelay: 1000,

      // Error handling
      throwOnError: false,
    },
  },
})

/**
 * Prefetch helper for server-side rendering or initial page load
 */
export const prefetchQuery = async <TData>(
  queryKey: unknown[],
  queryFn: () => Promise<TData>
): Promise<void> => {
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
  })
}

/**
 * Invalidate queries helper
 * Useful for invalidating after mutations
 */
export const invalidateQueries = (queryKey: unknown[]) => {
  return queryClient.invalidateQueries({ queryKey })
}

/**
 * Set query data helper
 * Useful for optimistic updates
 */
export const setQueryData = <TData>(queryKey: unknown[], updater: TData | ((old: TData | undefined) => TData)) => {
  queryClient.setQueryData(queryKey, updater)
}

/**
 * Remove query helper
 * Useful for clearing specific cached data
 */
export const removeQuery = (queryKey: unknown[]) => {
  queryClient.removeQueries({ queryKey })
}
