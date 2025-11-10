/**
 * Run Color Contrast Audit Script
 *
 * Executes the full WCAG 2.1 color contrast audit and outputs results
 *
 * Usage:
 * ```bash
 * npx tsx frontend/src/scripts/runColorAudit.ts
 * ```
 */

import { generateAuditReport, runFullAudit } from '../utils/colorContrastAudit'

console.log('🎨 Running Vividly Design System Color Contrast Audit...\n')

const { lightMode, darkMode, summary } = runFullAudit()

// Print full report
console.log(generateAuditReport())

// Exit with error code if any failures
if (summary.failed > 0) {
  console.error(`\n❌ Audit failed: ${summary.failed} color combinations do not meet WCAG AA standards.`)
  process.exit(1)
} else {
  console.log('\n✅ All color combinations pass WCAG AA standards!')
  process.exit(0)
}
