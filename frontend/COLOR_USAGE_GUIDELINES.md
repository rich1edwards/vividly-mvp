# Vividly Design System - Color Usage Guidelines

**Version**: 1.0.0
**Date**: 2025-01-08
**WCAG Compliance**: Level AA (4.5:1 minimum contrast for normal text)

---

## Table of Contents

1. [Overview](#overview)
2. [WCAG AA Compliance](#wcag-aa-compliance)
3. [Color Palette](#color-palette)
4. [Semantic Color Usage](#semantic-color-usage)
5. [Text & Background Combinations](#text--background-combinations)
6. [Accessibility Best Practices](#accessibility-best-practices)
7. [Common Patterns](#common-patterns)
8. [Testing & Validation](#testing--validation)

---

## Overview

The Vividly design system uses a carefully calibrated color palette that ensures **WCAG 2.1 Level AA compliance** (4.5:1 contrast ratio minimum for normal text). All color values have been tested and validated to provide excellent readability and accessibility.

### Key Principles

1. **Never compromise accessibility for aesthetics**
2. **Use semantic colors for their intended purpose**
3. **Test all custom color combinations**
4. **Ensure information is not conveyed by color alone**

---

## WCAG AA Compliance

### Contrast Ratio Requirements

| Text Size | Minimum Contrast Ratio |
|-----------|------------------------|
| **Normal text** (< 18pt / 24px) | **4.5:1** |
| **Large text** (≥ 18pt / 24px or ≥ 14pt bold) | **3:1** |
| **UI components** (icons, borders) | **3:1** |

### Vividly Color Contrast Audit Results

All color combinations in our design system **pass WCAG AA**:

| Color Combination | Contrast Ratio | Status |
|-------------------|----------------|--------|
| Primary Button (white on blue) | **4.75:1** | ✅ PASS |
| Secondary Button (white on coral) | **4.68:1** | ✅ PASS |
| Success Message (white on green) | **4.68:1** | ✅ PASS |
| Error Message (white on red) | **4.72:1** | ✅ PASS |
| Warning Message (dark on yellow) | **9.34:1** | ✅ EXCELLENT |
| Body Text (dark on white) | **15.23:1** | ✅ EXCELLENT |
| Muted Text (gray on white) | **4.53:1** | ✅ PASS |

---

## Color Palette

### Primary Colors

#### Vivid Blue (Primary)
- **Variable**: `--primary` / `hsl(var(--primary))`
- **HSL**: `207 90% 42%` (adjusted for WCAG AA)
- **Use for**: Primary actions, links, selected states
- **Foreground**: White (`--primary-foreground`)

```tsx
// ✅ Correct usage
<Button variant="primary">Save</Button>

// ❌ Incorrect - don't use for backgrounds without proper text contrast
<div className="bg-primary text-gray-600">...</div>
```

#### Warm Coral (Secondary)
- **Variable**: `--secondary` / `hsl(var(--secondary))`
- **HSL**: `14 100% 43%` (adjusted for WCAG AA)
- **Use for**: Secondary actions, accents
- **Foreground**: White (`--secondary-foreground`)

#### Electric Purple (Accent)
- **Variable**: `--accent` / `hsl(var(--accent))`
- **HSL**: `291 64% 42%`
- **Use for**: Highlights, special features
- **Foreground**: White (`--accent-foreground`)

### Status Colors

#### Fresh Green (Success)
- **Variable**: `--success` / Custom utility
- **HSL**: `122 39% 37%` (adjusted for WCAG AA)
- **Use for**: Success messages, completed states
- **Foreground**: White

```tsx
// ✅ Success notification
<div className="bg-vividly-green-700 text-white">
  Content saved successfully!
</div>
```

#### Alert Red (Destructive/Error)
- **Variable**: `--destructive` / `hsl(var(--destructive))`
- **HSL**: `4 90% 47%` (adjusted for WCAG AA)
- **Use for**: Errors, destructive actions, critical alerts
- **Foreground**: White (`--destructive-foreground`)

```tsx
// ✅ Error state
<Button variant="danger">Delete Account</Button>

// ✅ Error message
<div className="bg-destructive text-destructive-foreground">
  Invalid credentials
</div>
```

#### Sunny Yellow (Warning)
- **Variable**: `--warning` / Custom utility
- **HSL**: `45 100% 51%`
- **Use for**: Warnings, cautions
- **Foreground**: Dark (`210 11% 15%`)

```tsx
// ✅ Warning - uses dark text for better contrast
<div className="bg-vividly-yellow text-foreground">
  ⚠️ Your session will expire in 5 minutes
</div>
```

### Neutral Colors

#### Background & Foreground
- **Background**: `0 0% 100%` (White)
- **Foreground**: `210 11% 15%` (Dark gray)
- **Contrast Ratio**: **15.23:1** ✅

#### Muted
- **Muted Background**: `200 18% 93%` (Light gray)
- **Muted Foreground**: `200 7% 46%` (Medium gray)
- **Use for**: Secondary text, disabled states, subtle backgrounds

```tsx
// ✅ Secondary information
<p className="text-muted-foreground">
  Last updated 2 hours ago
</p>

// ✅ Disabled state
<Button disabled className="bg-muted text-muted-foreground">
  Disabled
</Button>
```

---

## Semantic Color Usage

### ✅ DO

```tsx
// Use semantic colors for their intended purpose
<Button variant="primary">Save</Button>
<Button variant="danger">Delete</Button>

// Use success for positive feedback
<Toast variant="success">Profile updated!</Toast>

// Use warning for cautionary messages
<Alert variant="warning">Low disk space</Alert>

// Use muted for secondary text
<p className="text-muted-foreground">Optional field</p>
```

### ❌ DON'T

```tsx
// Don't use destructive color for non-destructive actions
<Button className="bg-destructive">Submit Form</Button>

// Don't use success color for errors
<Toast className="bg-success">Login failed</Toast>

// Don't mix semantic meanings
<Alert className="bg-vividly-green text-destructive">...</Alert>
```

---

## Text & Background Combinations

### Safe Combinations (Guaranteed WCAG AA)

| Background | Text Color | Contrast | Usage |
|------------|------------|----------|-------|
| `bg-background` | `text-foreground` | 15.23:1 | Body text |
| `bg-primary` | `text-primary-foreground` | 4.75:1 | Primary buttons |
| `bg-secondary` | `text-secondary-foreground` | 4.68:1 | Secondary buttons |
| `bg-destructive` | `text-destructive-foreground` | 4.72:1 | Error states |
| `bg-muted` | `text-foreground` | 13.05:1 | Muted backgrounds |
| `bg-background` | `text-muted-foreground` | 4.53:1 | Secondary text |

### Custom Combinations - Test First!

If you need to create a custom color combination:

1. **Use the contrast audit utility**:
   ```tsx
   import { getContrastRatioFromHsl } from '@/utils/colorContrastAudit'

   const ratio = getContrastRatioFromHsl('207 90% 42%', '0 0% 100%')
   console.log(ratio) // 4.75:1 ✅
   ```

2. **Ensure minimum 4.5:1 ratio for normal text**

3. **Test with color blindness simulators**

---

## Accessibility Best Practices

### 1. Never Rely on Color Alone

```tsx
// ❌ Bad - only uses color
<div className="bg-vividly-red">Error</div>

// ✅ Good - combines color with icon and text
<div className="bg-vividly-red-50 text-vividly-red-900 border border-vividly-red-200">
  <AlertCircle className="w-4 h-4" />
  <span>Error: Invalid input</span>
</div>
```

### 2. Provide Sufficient Contrast

```tsx
// ❌ Bad - insufficient contrast
<button className="bg-vividly-blue-200 text-vividly-blue-300">
  Click me
</button>

// ✅ Good - uses approved combinations
<button className="bg-primary text-primary-foreground">
  Click me
</button>
```

### 3. Use Semantic HTML & ARIA

```tsx
// ✅ Good - semantic and accessible
<div role="alert" className="bg-destructive text-destructive-foreground">
  <span className="sr-only">Error:</span>
  Failed to save changes
</div>
```

### 4. Test with Real Users

- Use screen readers (NVDA, JAWS, VoiceOver)
- Test with color blindness simulators
- Get feedback from users with visual impairments

---

## Common Patterns

### Buttons

```tsx
// Primary action
<Button variant="primary">Save Changes</Button>

// Secondary action
<Button variant="secondary">Cancel</Button>

// Destructive action
<Button variant="danger">Delete Account</Button>

// Tertiary/ghost action
<Button variant="ghost">Learn More</Button>
```

### Notifications

```tsx
// Success
<Toast variant="success" title="Success">
  Your changes have been saved
</Toast>

// Error
<Toast variant="error" title="Error">
  Failed to process request
</Toast>

// Warning
<Toast variant="warning" title="Warning">
  Session expiring soon
</Toast>

// Info
<Toast variant="info" title="Info">
  New feature available
</Toast>
```

### Status Badges

```tsx
// Active/Success
<Badge className="bg-vividly-green-700 text-white">Active</Badge>

// Pending/Warning
<Badge className="bg-vividly-yellow text-foreground">Pending</Badge>

// Inactive/Error
<Badge className="bg-vividly-red-700 text-white">Inactive</Badge>

// Neutral
<Badge className="bg-muted text-muted-foreground">Draft</Badge>
```

### Form States

```tsx
// Normal state
<Input className="border-input" />

// Focus state
<Input className="border-input focus:ring-2 focus:ring-primary" />

// Error state
<Input
  className="border-destructive focus:ring-destructive"
  aria-invalid="true"
  aria-describedby="error-message"
/>
<p id="error-message" className="text-destructive text-sm">
  This field is required
</p>

// Disabled state
<Input disabled className="bg-muted text-muted-foreground cursor-not-allowed" />
```

---

## Testing & Validation

### Running the Color Audit

```bash
# Run the full color contrast audit
npx tsx frontend/src/scripts/runColorAudit.ts
```

### Manual Testing Tools

1. **Browser DevTools**:
   - Chrome: Lighthouse accessibility audit
   - Firefox: Accessibility Inspector

2. **Online Tools**:
   - WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
   - Contrast Ratio: https://contrast-ratio.com/

3. **Color Blindness Simulators**:
   - Coblis: https://www.color-blindness.com/coblis-color-blindness-simulator/
   - Chrome extension: "Color Oracle"

### Pre-commit Checklist

- [ ] All custom colors tested for WCAG AA compliance (4.5:1 minimum)
- [ ] Information not conveyed by color alone
- [ ] Interactive elements have visible focus indicators
- [ ] Error states include icons and descriptive text
- [ ] Color combinations match approved palette

---

## Migration Guide

### Updating Existing Components

If you have existing components using the old (brighter) colors:

#### Before (may fail WCAG AA):
```tsx
<Button className="bg-vividly-blue text-white">
  Click me
</Button>
```

#### After (WCAG AA compliant):
```tsx
<Button variant="primary">
  Click me
</Button>

// Or using Tailwind classes with CSS variables:
<Button className="bg-primary text-primary-foreground">
  Click me
</Button>
```

### Direct Color References

If you must use direct Vividly colors from Tailwind config:

```tsx
// ✅ These are safe (darker shades with good contrast):
<div className="bg-vividly-blue-700 text-white">...</div>
<div className="bg-vividly-green-800 text-white">...</div>
<div className="bg-vividly-red-700 text-white">...</div>

// ⚠️ These may not have sufficient contrast - test first:
<div className="bg-vividly-blue-400 text-white">...</div>
<div className="bg-vividly-green-400 text-white">...</div>
```

---

## Resources

### Internal

- `frontend/src/utils/colorContrastAudit.ts` - Contrast calculation utilities
- `frontend/src/index.css` - CSS variable definitions
- `tailwind.config.js` - Tailwind color configuration

### External

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/)
- [Contrast (Minimum) - WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WebAIM Color Contrast](https://webaim.org/articles/contrast/)

---

## Questions & Support

For questions about color usage or accessibility:

1. Check this guide first
2. Run the color audit utility to test custom combinations
3. Consult the design team for new color requirements
4. Reference WCAG 2.1 guidelines for edge cases

**Remember**: Accessibility is not optional. When in doubt, choose higher contrast and test with real users.

---

**Last Updated**: 2025-01-08
**Maintained By**: Vividly Frontend Team
**Version**: 1.0.0
