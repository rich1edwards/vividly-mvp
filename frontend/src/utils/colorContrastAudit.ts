/**
 * Color Contrast Audit Utility (Phase 4.1.3)
 *
 * WCAG 2.1 Level AA Compliance Checker
 * - Normal text: 4.5:1 minimum contrast ratio
 * - Large text (18pt+/14pt+ bold): 3:1 minimum contrast ratio
 * - UI components: 3:1 minimum contrast ratio
 *
 * References:
 * - WCAG 2.1: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
 * - Contrast calculation: https://www.w3.org/TR/WCAG20-TECHS/G18.html
 */

// ============================================================================
// Color Conversion Utilities
// ============================================================================

/**
 * Convert HSL to RGB
 */
export function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  s = s / 100
  l = l / 100

  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = l - c / 2

  let r = 0
  let g = 0
  let b = 0

  if (h >= 0 && h < 60) {
    r = c
    g = x
    b = 0
  } else if (h >= 60 && h < 120) {
    r = x
    g = c
    b = 0
  } else if (h >= 120 && h < 180) {
    r = 0
    g = c
    b = x
  } else if (h >= 180 && h < 240) {
    r = 0
    g = x
    b = c
  } else if (h >= 240 && h < 300) {
    r = x
    g = 0
    b = c
  } else if (h >= 300 && h < 360) {
    r = c
    g = 0
    b = x
  }

  return [
    Math.round((r + m) * 255),
    Math.round((g + m) * 255),
    Math.round((b + m) * 255),
  ]
}

/**
 * Convert hex color to RGB
 */
export function hexToRgb(hex: string): [number, number, number] {
  const sanitized = hex.replace('#', '')
  const r = parseInt(sanitized.substring(0, 2), 16)
  const g = parseInt(sanitized.substring(2, 4), 16)
  const b = parseInt(sanitized.substring(4, 6), 16)
  return [r, g, b]
}

/**
 * Parse HSL string (e.g., "207 90% 54%") to RGB
 */
export function parseHslString(hsl: string): [number, number, number] {
  const parts = hsl.split(' ')
  const h = parseFloat(parts[0])
  const s = parseFloat(parts[1].replace('%', ''))
  const l = parseFloat(parts[2].replace('%', ''))
  return hslToRgb(h, s, l)
}

// ============================================================================
// Relative Luminance Calculation
// ============================================================================

/**
 * Calculate relative luminance of an RGB color
 * Formula from WCAG: https://www.w3.org/TR/WCAG20/#relativeluminancedef
 */
export function getRelativeLuminance(r: number, g: number, b: number): number {
  // Convert RGB to sRGB (0-1 range)
  const rsRGB = r / 255
  const gsRGB = g / 255
  const bsRGB = b / 255

  // Apply gamma correction
  const rLinear = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4)
  const gLinear = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4)
  const bLinear = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4)

  // Calculate relative luminance
  return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear
}

// ============================================================================
// Contrast Ratio Calculation
// ============================================================================

/**
 * Calculate contrast ratio between two colors
 * Formula from WCAG: (L1 + 0.05) / (L2 + 0.05)
 * where L1 is the lighter color and L2 is the darker color
 */
export function getContrastRatio(
  color1: [number, number, number],
  color2: [number, number, number]
): number {
  const l1 = getRelativeLuminance(...color1)
  const l2 = getRelativeLuminance(...color2)

  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)

  return (lighter + 0.05) / (darker + 0.05)
}

/**
 * Calculate contrast ratio from HSL strings
 */
export function getContrastRatioFromHsl(hsl1: string, hsl2: string): number {
  const rgb1 = parseHslString(hsl1)
  const rgb2 = parseHslString(hsl2)
  return getContrastRatio(rgb1, rgb2)
}

/**
 * Calculate contrast ratio from hex colors
 */
export function getContrastRatioFromHex(hex1: string, hex2: string): number {
  const rgb1 = hexToRgb(hex1)
  const rgb2 = hexToRgb(hex2)
  return getContrastRatio(rgb1, rgb2)
}

// ============================================================================
// WCAG Compliance Checking
// ============================================================================

export enum WcagLevel {
  AA = 'AA',
  AAA = 'AAA',
}

export enum TextSize {
  NORMAL = 'normal', // < 18pt (24px) regular or < 14pt (18.66px) bold
  LARGE = 'large', // >= 18pt (24px) regular or >= 14pt (18.66px) bold
}

export interface ContrastRequirement {
  level: WcagLevel
  textSize: TextSize
  minimumRatio: number
}

export interface ContrastResult {
  ratio: number
  passes: {
    AA_normal: boolean // 4.5:1
    AA_large: boolean // 3:1
    AAA_normal: boolean // 7:1
    AAA_large: boolean // 4.5:1
  }
  wcagLevel: WcagLevel | 'Fail'
  score: 'Excellent' | 'Good' | 'Poor' | 'Fail'
}

/**
 * Get WCAG minimum contrast ratio for given level and text size
 */
export function getMinimumContrastRatio(level: WcagLevel, textSize: TextSize): number {
  const requirements: Record<WcagLevel, Record<TextSize, number>> = {
    [WcagLevel.AA]: {
      [TextSize.NORMAL]: 4.5,
      [TextSize.LARGE]: 3.0,
    },
    [WcagLevel.AAA]: {
      [TextSize.NORMAL]: 7.0,
      [TextSize.LARGE]: 4.5,
    },
  }
  return requirements[level][textSize]
}

/**
 * Check if contrast ratio meets WCAG requirements
 */
export function checkContrastCompliance(
  ratio: number,
  level: WcagLevel = WcagLevel.AA,
  textSize: TextSize = TextSize.NORMAL
): boolean {
  const minimumRatio = getMinimumContrastRatio(level, textSize)
  return ratio >= minimumRatio
}

/**
 * Analyze contrast ratio and return detailed results
 */
export function analyzeContrast(ratio: number): ContrastResult {
  const passes = {
    AA_normal: ratio >= 4.5,
    AA_large: ratio >= 3.0,
    AAA_normal: ratio >= 7.0,
    AAA_large: ratio >= 4.5,
  }

  let wcagLevel: WcagLevel | 'Fail' = 'Fail'
  if (passes.AAA_normal) wcagLevel = WcagLevel.AAA
  else if (passes.AA_normal) wcagLevel = WcagLevel.AA

  let score: 'Excellent' | 'Good' | 'Poor' | 'Fail'
  if (ratio >= 7.0) score = 'Excellent'
  else if (ratio >= 4.5) score = 'Good'
  else if (ratio >= 3.0) score = 'Poor'
  else score = 'Fail'

  return { ratio, passes, wcagLevel, score }
}

// ============================================================================
// Vividly Design System Color Definitions
// ============================================================================

export const VIVIDLY_COLORS = {
  // Light Mode
  light: {
    background: '0 0% 100%', // White
    foreground: '210 11% 15%', // Dark gray

    // Primary colors
    primary: '207 90% 54%', // Blue #2196F3
    'primary-foreground': '0 0% 100%', // White

    secondary: '14 100% 63%', // Coral #FF7043
    'secondary-foreground': '0 0% 100%', // White

    accent: '291 64% 42%', // Purple #9C27B0
    'accent-foreground': '0 0% 100%', // White

    // Status colors
    success: '122 39% 49%', // Green #4CAF50
    'success-foreground': '0 0% 100%', // White

    warning: '45 100% 51%', // Yellow #FFC107
    'warning-foreground': '210 11% 15%', // Dark gray

    destructive: '4 90% 58%', // Red #F44336
    'destructive-foreground': '0 0% 100%', // White

    // Neutral
    muted: '200 18% 93%', // Light gray bg
    'muted-foreground': '200 7% 46%', // Medium gray text

    border: '200 18% 87%', // Border gray
  },

  // Dark Mode
  dark: {
    background: '200 18% 14%', // Dark gray
    foreground: '200 18% 93%', // Light gray

    primary: '207 90% 61%', // Lighter blue
    'primary-foreground': '0 0% 100%', // White

    secondary: '14 100% 68%', // Lighter coral
    'secondary-foreground': '0 0% 100%', // White

    accent: '291 64% 51%', // Lighter purple
    'accent-foreground': '0 0% 100%', // White

    success: '122 39% 54%', // Lighter green
    'success-foreground': '0 0% 100%', // White

    warning: '45 100% 60%', // Adjusted yellow
    'warning-foreground': '200 18% 14%', // Dark gray

    destructive: '4 90% 63%', // Lighter red
    'destructive-foreground': '0 0% 100%', // White

    muted: '200 16% 24%', // Dark gray bg
    'muted-foreground': '200 11% 58%', // Light gray text

    border: '200 16% 28%', // Border gray
  },

  // Direct hex colors from Tailwind config
  hex: {
    blue: {
      DEFAULT: '#2196F3',
      50: '#E3F2FD',
      100: '#BBDEFB',
      200: '#90CAF9',
      300: '#64B5F6',
      400: '#42A5F5',
      500: '#2196F3',
      600: '#1E88E5',
      700: '#1976D2',
      800: '#1565C0',
      900: '#0D47A1',
    },
    coral: {
      DEFAULT: '#FF7043',
      50: '#FBE9E7',
      100: '#FFCCBC',
      200: '#FFAB91',
      300: '#FF8A65',
      400: '#FF7043',
      500: '#FF5722',
      600: '#F4511E',
      700: '#E64A19',
      800: '#D84315',
      900: '#BF360C',
    },
    green: {
      DEFAULT: '#4CAF50',
      50: '#E8F5E9',
      100: '#C8E6C9',
      200: '#A5D6A7',
      300: '#81C784',
      400: '#66BB6A',
      500: '#4CAF50',
      600: '#43A047',
      700: '#388E3C',
      800: '#2E7D32',
      900: '#1B5E20',
    },
    yellow: {
      DEFAULT: '#FFC107',
      50: '#FFF8E1',
      100: '#FFECB3',
      200: '#FFE082',
      300: '#FFD54F',
      400: '#FFCA28',
      500: '#FFC107',
      600: '#FFB300',
      700: '#FFA000',
      800: '#FF8F00',
      900: '#FF6F00',
    },
    red: {
      DEFAULT: '#F44336',
      50: '#FFEBEE',
      100: '#FFCDD2',
      200: '#EF9A9A',
      300: '#E57373',
      400: '#EF5350',
      500: '#F44336',
      600: '#E53935',
      700: '#D32F2F',
      800: '#C62828',
      900: '#B71C1C',
    },
    purple: {
      DEFAULT: '#9C27B0',
      50: '#F3E5F5',
      100: '#E1BEE7',
      200: '#CE93D8',
      300: '#BA68C8',
      400: '#AB47BC',
      500: '#9C27B0',
      600: '#8E24AA',
      700: '#7B1FA2',
      800: '#6A1B9A',
      900: '#4A148C',
    },
    gray: {
      DEFAULT: '#607D8B',
      50: '#ECEFF1',
      100: '#CFD8DC',
      200: '#B0BEC5',
      300: '#90A4AE',
      400: '#78909C',
      500: '#607D8B',
      600: '#546E7A',
      700: '#455A64',
      800: '#37474F',
      900: '#263238',
    },
  },
}

// ============================================================================
// Audit Functions
// ============================================================================

export interface ColorPair {
  name: string
  foreground: string
  background: string
  context: string
  textSize: TextSize
}

export interface AuditResult extends ColorPair {
  ratio: number
  analysis: ContrastResult
  recommendation?: string
}

/**
 * Audit a single color pair
 */
export function auditColorPair(pair: ColorPair): AuditResult {
  let ratio: number

  // Determine if colors are HSL or hex
  if (pair.foreground.includes(' ') && pair.background.includes(' ')) {
    ratio = getContrastRatioFromHsl(pair.foreground, pair.background)
  } else {
    ratio = getContrastRatioFromHex(pair.foreground, pair.background)
  }

  const analysis = analyzeContrast(ratio)

  let recommendation: string | undefined
  if (pair.textSize === TextSize.NORMAL && !analysis.passes.AA_normal) {
    recommendation = 'Increase contrast to at least 4.5:1 for normal text (WCAG AA)'
  } else if (pair.textSize === TextSize.LARGE && !analysis.passes.AA_large) {
    recommendation = 'Increase contrast to at least 3:1 for large text (WCAG AA)'
  }

  return {
    ...pair,
    ratio,
    analysis,
    recommendation,
  }
}

/**
 * Run full audit on all Vividly design system colors
 */
export function runFullAudit(): {
  lightMode: AuditResult[]
  darkMode: AuditResult[]
  summary: {
    total: number
    passed: number
    failed: number
    passRate: number
  }
} {
  const lightModePairs: ColorPair[] = [
    // Primary text on backgrounds
    {
      name: 'Foreground on Background',
      foreground: VIVIDLY_COLORS.light.foreground,
      background: VIVIDLY_COLORS.light.background,
      context: 'Main body text',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Primary Button',
      foreground: VIVIDLY_COLORS.light['primary-foreground'],
      background: VIVIDLY_COLORS.light.primary,
      context: 'Primary action buttons',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Secondary Button',
      foreground: VIVIDLY_COLORS.light['secondary-foreground'],
      background: VIVIDLY_COLORS.light.secondary,
      context: 'Secondary action buttons',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Success Message',
      foreground: VIVIDLY_COLORS.light['success-foreground'],
      background: VIVIDLY_COLORS.light.success,
      context: 'Success notifications',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Warning Message',
      foreground: VIVIDLY_COLORS.light['warning-foreground'],
      background: VIVIDLY_COLORS.light.warning,
      context: 'Warning notifications',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Error Message',
      foreground: VIVIDLY_COLORS.light['destructive-foreground'],
      background: VIVIDLY_COLORS.light.destructive,
      context: 'Error notifications',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Muted Text',
      foreground: VIVIDLY_COLORS.light['muted-foreground'],
      background: VIVIDLY_COLORS.light.background,
      context: 'Secondary/helper text',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Muted Background Text',
      foreground: VIVIDLY_COLORS.light.foreground,
      background: VIVIDLY_COLORS.light.muted,
      context: 'Text on muted backgrounds',
      textSize: TextSize.NORMAL,
    },
  ]

  const darkModePairs: ColorPair[] = [
    {
      name: 'Foreground on Background (Dark)',
      foreground: VIVIDLY_COLORS.dark.foreground,
      background: VIVIDLY_COLORS.dark.background,
      context: 'Main body text (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Primary Button (Dark)',
      foreground: VIVIDLY_COLORS.dark['primary-foreground'],
      background: VIVIDLY_COLORS.dark.primary,
      context: 'Primary action buttons (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Secondary Button (Dark)',
      foreground: VIVIDLY_COLORS.dark['secondary-foreground'],
      background: VIVIDLY_COLORS.dark.secondary,
      context: 'Secondary action buttons (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Success Message (Dark)',
      foreground: VIVIDLY_COLORS.dark['success-foreground'],
      background: VIVIDLY_COLORS.dark.success,
      context: 'Success notifications (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Warning Message (Dark)',
      foreground: VIVIDLY_COLORS.dark['warning-foreground'],
      background: VIVIDLY_COLORS.dark.warning,
      context: 'Warning notifications (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Error Message (Dark)',
      foreground: VIVIDLY_COLORS.dark['destructive-foreground'],
      background: VIVIDLY_COLORS.dark.destructive,
      context: 'Error notifications (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Muted Text (Dark)',
      foreground: VIVIDLY_COLORS.dark['muted-foreground'],
      background: VIVIDLY_COLORS.dark.background,
      context: 'Secondary/helper text (dark mode)',
      textSize: TextSize.NORMAL,
    },
    {
      name: 'Muted Background Text (Dark)',
      foreground: VIVIDLY_COLORS.dark.foreground,
      background: VIVIDLY_COLORS.dark.muted,
      context: 'Text on muted backgrounds (dark mode)',
      textSize: TextSize.NORMAL,
    },
  ]

  const lightModeResults = lightModePairs.map(auditColorPair)
  const darkModeResults = darkModePairs.map(auditColorPair)

  const allResults = [...lightModeResults, ...darkModeResults]
  const total = allResults.length
  const passed = allResults.filter((r) => r.analysis.passes.AA_normal).length
  const failed = total - passed
  const passRate = (passed / total) * 100

  return {
    lightMode: lightModeResults,
    darkMode: darkModeResults,
    summary: {
      total,
      passed,
      failed,
      passRate,
    },
  }
}

/**
 * Format audit results for console output
 */
export function formatAuditResults(results: AuditResult[]): string {
  let output = '\n'
  output += '═'.repeat(80) + '\n'
  output += ' COLOR CONTRAST AUDIT REPORT\n'
  output += '═'.repeat(80) + '\n\n'

  results.forEach((result) => {
    const status = result.analysis.passes.AA_normal ? '✅ PASS' : '❌ FAIL'
    const ratio = result.ratio.toFixed(2)

    output += `${status} | ${result.name}\n`
    output += `  Context: ${result.context}\n`
    output += `  Contrast Ratio: ${ratio}:1 (${result.analysis.score})\n`
    output += `  WCAG Level: ${result.analysis.wcagLevel}\n`

    if (result.recommendation) {
      output += `  ⚠️  Recommendation: ${result.recommendation}\n`
    }

    output += '\n'
  })

  return output
}

/**
 * Generate audit report
 */
export function generateAuditReport(): string {
  const { lightMode, darkMode, summary } = runFullAudit()

  let report = '\n'
  report += '═'.repeat(80) + '\n'
  report += ' VIVIDLY DESIGN SYSTEM - WCAG 2.1 COLOR CONTRAST AUDIT\n'
  report += '═'.repeat(80) + '\n\n'

  report += '📊 SUMMARY\n'
  report += '─'.repeat(80) + '\n'
  report += `Total Combinations Tested: ${summary.total}\n`
  report += `Passed (WCAG AA): ${summary.passed}\n`
  report += `Failed: ${summary.failed}\n`
  report += `Pass Rate: ${summary.passRate.toFixed(1)}%\n\n`

  report += '☀️  LIGHT MODE RESULTS\n'
  report += '─'.repeat(80) + '\n'
  report += formatAuditResults(lightMode)

  report += '🌙 DARK MODE RESULTS\n'
  report += '─'.repeat(80) + '\n'
  report += formatAuditResults(darkMode)

  report += '═'.repeat(80) + '\n'
  report += ' END OF REPORT\n'
  report += '═'.repeat(80) + '\n'

  return report
}
