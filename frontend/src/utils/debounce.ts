/**
 * Debounce utility
 *
 * Delays the execution of a function until after a specified delay has elapsed
 * since the last time it was invoked. Useful for rate-limiting expensive operations
 * like API calls during user input.
 *
 * Usage example:
 * ```typescript
 * const debouncedSearch = debounce((query: string) => {
 *   apiClient.search(query)
 * }, 500)
 *
 * // Call it multiple times, but API will only be called once after 500ms of inactivity
 * debouncedSearch('test')
 * debouncedSearch('testing')
 * debouncedSearch('testing 123')
 * ```
 */

/**
 * Creates a debounced function that delays invoking `func` until after `delay` milliseconds
 * have elapsed since the last time the debounced function was invoked.
 *
 * @param func - The function to debounce
 * @param delay - The number of milliseconds to delay
 * @returns The debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function (this: any, ...args: Parameters<T>) {
    // Clear the previous timeout if it exists
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    // Set a new timeout
    timeoutId = setTimeout(() => {
      func.apply(this, args)
      timeoutId = null
    }, delay)
  }
}

/**
 * Creates a debounced function with a cleanup function to cancel pending invocations
 *
 * @param func - The function to debounce
 * @param delay - The number of milliseconds to delay
 * @returns Object with debounced function and cancel method
 */
export function debounceWithCancel<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): {
  debounced: (...args: Parameters<T>) => void
  cancel: () => void
} {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const debounced = function (this: any, ...args: Parameters<T>) {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      func.apply(this, args)
      timeoutId = null
    }, delay)
  }

  const cancel = () => {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  return { debounced, cancel }
}
