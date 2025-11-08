/**
 * Time Estimation Utility - Phase 1.2.4
 *
 * Calculates estimated video generation time based on content complexity
 * and system load factors.
 */

export interface TimeEstimate {
  estimatedMinutes: number
  estimatedSeconds: number
  displayText: string
  isHighLoad: boolean
  confidenceLevel: 'high' | 'medium' | 'low'
}

/**
 * Complexity factors for content generation
 */
interface ComplexityFactors {
  queryLength: number
  gradeLevel: number
  hasInterest: boolean
}

/**
 * Base time estimates (in seconds)
 */
const BASE_TIMES = {
  MIN: 90,   // 1.5 minutes minimum
  BASE: 150, // 2.5 minutes base
  MAX: 210,  // 3.5 minutes maximum
}

/**
 * Calculate estimated generation time based on content complexity
 *
 * Factors considered:
 * - Query length (longer queries = more context to process)
 * - Grade level (higher grades = more complex explanations)
 * - Interest selection (personalization adds slight overhead)
 *
 * @param factors - Complexity factors for the content request
 * @returns Time estimate with confidence level
 */
export const calculateEstimatedTime = (factors: ComplexityFactors): TimeEstimate => {
  let baseTime = BASE_TIMES.BASE
  let adjustment = 0

  // Query length factor (0-10 seconds adjustment)
  // Longer queries require more NLU processing and content retrieval
  const queryLengthFactor = Math.min(factors.queryLength / 500, 1)
  adjustment += queryLengthFactor * 10

  // Grade level factor (-5 to +10 seconds adjustment)
  // 9th grade: -5s (simpler content)
  // 10th grade: 0s (base)
  // 11th grade: +5s (more complex)
  // 12th grade: +10s (most complex)
  const gradeLevelAdjustment = (factors.gradeLevel - 10) * 5
  adjustment += gradeLevelAdjustment

  // Interest personalization factor (+5 seconds if interest selected)
  // Personalization requires additional RAG retrieval and analogy generation
  if (factors.hasInterest) {
    adjustment += 5
  }

  // Calculate final time with bounds checking
  const estimatedSeconds = Math.max(
    BASE_TIMES.MIN,
    Math.min(BASE_TIMES.MAX, Math.round(baseTime + adjustment))
  )
  const estimatedMinutes = Math.floor(estimatedSeconds / 60)
  const remainingSeconds = estimatedSeconds % 60

  // Determine confidence level based on query completeness
  let confidenceLevel: 'high' | 'medium' | 'low' = 'high'
  if (factors.queryLength < 50) {
    confidenceLevel = 'medium'
  } else if (factors.queryLength < 20) {
    confidenceLevel = 'low'
  }

  // Format display text
  let displayText: string
  if (remainingSeconds === 0) {
    displayText = `${estimatedMinutes} minute${estimatedMinutes !== 1 ? 's' : ''}`
  } else if (estimatedMinutes === 0) {
    displayText = `${remainingSeconds} seconds`
  } else {
    displayText = `${estimatedMinutes}:${remainingSeconds.toString().padStart(2, '0')} minutes`
  }

  return {
    estimatedMinutes,
    estimatedSeconds,
    displayText,
    isHighLoad: false, // Will be updated by system load check
    confidenceLevel,
  }
}

/**
 * Check for high system load (optional - can be enhanced with API call)
 *
 * Currently returns a static value, but this can be enhanced to:
 * - Call backend API to check queue depth
 * - Check current worker utilization
 * - Return estimated wait time if queue is backed up
 *
 * @returns Whether system is under high load
 */
export const checkSystemLoad = async (): Promise<boolean> => {
  // TODO: Implement API call to check system load
  // For now, return false (normal load)
  // In production, this would call: GET /api/v1/system/load
  return false
}

/**
 * Get high load warning message
 *
 * @param estimatedMinutes - Base estimated time in minutes
 * @returns Warning message for high load conditions
 */
export const getHighLoadWarning = (estimatedMinutes: number): string => {
  const adjustedTime = Math.ceil(estimatedMinutes * 1.5)
  return `High demand detected. Generation may take up to ${adjustedTime} minutes. Your request will be queued.`
}

/**
 * Format time estimate with confidence indicator
 *
 * @param estimate - Time estimate object
 * @returns Formatted string with confidence indicator
 */
export const formatTimeEstimateWithConfidence = (estimate: TimeEstimate): string => {
  const prefix = estimate.confidenceLevel === 'high' ? 'Estimated time:' : 'Approximate time:'
  return `${prefix} ${estimate.displayText}`
}
