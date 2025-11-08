/**
 * Fuzzy Search Utility
 *
 * Provides fuzzy matching for autocomplete suggestions
 */

/**
 * Calculate similarity score between two strings using Levenshtein distance
 * Returns a score between 0 and 1, where 1 is an exact match
 */
export function calculateSimilarity(str1: string, str2: string): number {
  const s1 = str1.toLowerCase()
  const s2 = str2.toLowerCase()

  // Exact match
  if (s1 === s2) return 1

  // One string contains the other
  if (s1.includes(s2) || s2.includes(s1)) {
    return 0.8 + (0.2 * (Math.min(s1.length, s2.length) / Math.max(s1.length, s2.length)))
  }

  // Levenshtein distance calculation
  const len1 = s1.length
  const len2 = s2.length
  const matrix: number[][] = []

  // Initialize matrix
  for (let i = 0; i <= len1; i++) {
    matrix[i] = [i]
  }
  for (let j = 0; j <= len2; j++) {
    matrix[0][j] = j
  }

  // Calculate distances
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = s1[i - 1] === s2[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,      // deletion
        matrix[i][j - 1] + 1,      // insertion
        matrix[i - 1][j - 1] + cost // substitution
      )
    }
  }

  const distance = matrix[len1][len2]
  const maxLength = Math.max(len1, len2)

  // Convert distance to similarity score (0-1)
  return 1 - (distance / maxLength)
}

/**
 * Search through items and return matches sorted by relevance
 *
 * @param query - Search query
 * @param items - Array of strings to search through
 * @param minScore - Minimum similarity score (0-1) to be considered a match
 * @param limit - Maximum number of results to return
 * @returns Array of matched items sorted by relevance (highest score first)
 */
export function fuzzySearch(
  query: string,
  items: string[],
  minScore: number = 0.3,
  limit: number = 5
): string[] {
  if (!query || query.trim().length === 0) {
    return []
  }

  const trimmedQuery = query.trim()

  // Calculate scores for all items
  const scoredItems = items.map(item => ({
    item,
    score: calculateSimilarity(trimmedQuery, item)
  }))

  // Filter by minimum score, sort by score descending, and limit results
  return scoredItems
    .filter(({ score }) => score >= minScore)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(({ item }) => item)
}

/**
 * Extract unique queries from content history
 *
 * @param contentHistory - Array of generated content items
 * @returns Array of unique query strings
 */
export function extractQueriesFromHistory(contentHistory: any[]): string[] {
  const queries = contentHistory
    .map(item => item.query || item.original_query)
    .filter(Boolean)

  // Return unique queries
  return Array.from(new Set(queries))
}
