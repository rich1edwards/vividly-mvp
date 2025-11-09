/**
 * Skip to Content Component (Phase 4.1.1)
 *
 * Accessibility feature that allows keyboard users to skip repetitive navigation
 * and jump directly to main content.
 *
 * Features:
 * - Hidden visually but accessible to screen readers
 * - Visible on keyboard focus
 * - Smooth scroll to main content
 * - WCAG 2.1 AA compliance
 * - High contrast focus indicator
 *
 * Usage:
 * ```tsx
 * <SkipToContent />
 * // ... navigation/header ...
 * <main id="main-content">
 *   // Main content here
 * </main>
 * ```
 */

import React from 'react'

export const SkipToContent: React.FC = () => {
  const handleSkip = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    const mainContent = document.getElementById('main-content')
    if (mainContent) {
      mainContent.focus()
      mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <a
      href="#main-content"
      onClick={handleSkip}
      className="
        sr-only
        focus:not-sr-only
        focus:absolute
        focus:z-50
        focus:top-4
        focus:left-4
        focus:px-4
        focus:py-2
        focus:bg-blue-600
        focus:text-white
        focus:rounded-lg
        focus:shadow-lg
        focus:outline-none
        focus:ring-2
        focus:ring-blue-500
        focus:ring-offset-2
        transition-all
        font-medium
        text-sm
      "
      aria-label="Skip to main content"
    >
      Skip to main content
    </a>
  )
}

export default SkipToContent
