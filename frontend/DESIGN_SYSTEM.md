# Vividly Design System

Comprehensive design system documentation for Vividly's frontend application.

## Table of Contents

1. [Overview](#overview)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Spacing](#spacing)
5. [Components](#components)
6. [Layout](#layout)
7. [Accessibility](#accessibility)
8. [Usage Guidelines](#usage-guidelines)

---

## Overview

Vividly uses **shadcn/ui** as its component library, built on top of:
- **Tailwind CSS** for utility-first styling
- **Radix UI** for accessible, unstyled primitives
- **class-variance-authority (CVA)** for component variants

### Design Principles

1. **Accessibility First**: WCAG 2.1 Level AA compliance
2. **Consistent**: Unified visual language across all user roles
3. **Responsive**: Mobile-first, works on all screen sizes
4. **Performant**: Optimized for fast load times
5. **Intuitive**: Clear visual hierarchy and user flows

---

## Color Palette

### Primary Colors

```css
/* Blue - Primary Actions, Links */
--primary: hsl(217, 91%, 60%)     /* #4C9AFF */
--primary-foreground: hsl(0, 0%, 100%)

/* Green - Success, Positive Actions */
--secondary: hsl(142, 76%, 36%)   /* #16A34A */
--secondary-foreground: hsl(0, 0%, 100%)

/* Purple - Accent, Highlights */
--accent: hsl(280, 89%, 60%)      /* #A855F7 */
--accent-foreground: hsl(0, 0%, 100%)
```

### Utility Colors

```css
/* Orange - Warnings, Alerts */
Orange: #F97316

/* Red - Errors, Destructive Actions */
--destructive: hsl(0, 84.2%, 60.2%)
--destructive-foreground: hsl(0, 0%, 100%)
```

### Grayscale

```css
--gray-50:  #F9FAFB
--gray-100: #F3F4F6
--gray-200: #E5E7EB
--gray-300: #D1D5DB
--gray-400: #9CA3AF
--gray-500: #6B7280
--gray-600: #4B5563
--gray-700: #374151
--gray-800: #1F2937
--gray-900: #111827
```

### Semantic Colors

```css
/* Background & Surfaces */
--background: hsl(0, 0%, 100%)
--card: hsl(0, 0%, 100%)
--popover: hsl(0, 0%, 100%)

/* Text Colors */
--foreground: hsl(222.2, 84%, 4.9%)
--muted-foreground: hsl(215.4, 16.3%, 46.9%)

/* Borders & Inputs */
--border: hsl(214.3, 31.8%, 91.4%)
--input: hsl(214.3, 31.8%, 91.4%)
--ring: hsl(217, 91%, 60%)
```

### Usage Guidelines

- **Blue (Primary)**: Main CTAs, navigation, links
- **Green (Secondary)**: Success states, confirmations, "Start Learning" actions
- **Purple (Accent)**: AI-generated content, highlights, special features
- **Orange**: Warnings, pending states
- **Red**: Errors, delete actions, critical alerts
- **Gray**: Text hierarchy, borders, backgrounds

### Color Contrast

All color combinations meet **WCAG 2.1 Level AA** requirements:
- Normal text: 4.5:1 minimum
- Large text (18pt+): 3:1 minimum
- UI components: 3:1 minimum

---

## Typography

### Font Family

```css
font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

Uses system fonts for optimal performance and native feel.

### Type Scale

| Name | Size | Line Height | Weight | Usage |
|------|------|-------------|--------|-------|
| `text-xs` | 0.75rem (12px) | 1rem | 400 | Captions, labels |
| `text-sm` | 0.875rem (14px) | 1.25rem | 400 | Body text (small) |
| `text-base` | 1rem (16px) | 1.5rem | 400 | Body text (default) |
| `text-lg` | 1.125rem (18px) | 1.75rem | 500 | Emphasized text |
| `text-xl` | 1.25rem (20px) | 1.75rem | 600 | Section headings |
| `text-2xl` | 1.5rem (24px) | 2rem | 700 | Page headings |
| `text-3xl` | 1.875rem (30px) | 2.25rem | 700 | Feature headings |
| `text-4xl` | 2.25rem (36px) | 2.5rem | 800 | Hero headings |
| `text-5xl` | 3rem (48px) | 1 | 900 | Display headings |

### Font Weights

- **400 (Normal)**: Body text
- **500 (Medium)**: Emphasized text, labels
- **600 (Semibold)**: Headings, buttons
- **700 (Bold)**: Important headings
- **800 (Extrabold)**: Hero sections
- **900 (Black)**: Display text

### Usage Examples

```tsx
{/* Page Heading */}
<h1 className="text-3xl font-bold text-foreground">
  Student Dashboard
</h1>

{/* Section Heading */}
<h2 className="text-xl font-semibold text-foreground">
  Recent Videos
</h2>

{/* Body Text */}
<p className="text-base text-muted-foreground">
  Watch personalized videos tailored to your interests.
</p>

{/* Small Text */}
<span className="text-sm text-muted-foreground">
  2 days ago
</span>
```

---

## Spacing

Tailwind's default spacing scale (based on 0.25rem = 4px):

```css
0   = 0px
1   = 4px
2   = 8px
3   = 12px
4   = 16px
5   = 20px
6   = 24px
8   = 32px
10  = 40px
12  = 48px
16  = 64px
20  = 80px
24  = 96px
32  = 128px
```

### Layout Spacing

- **Component padding**: `p-4` (16px) for cards, `p-6` (24px) for larger surfaces
- **Stack spacing**: `space-y-4` (16px) for related items
- **Section margins**: `mb-8` (32px) between major sections
- **Page margins**: `container mx-auto px-4` for consistent page margins

---

## Components

### Available Components

Core components from shadcn/ui installed:

#### Buttons
```tsx
import { Button } from "@/components/ui/button"

<Button variant="default">Primary Action</Button>
<Button variant="secondary">Secondary Action</Button>
<Button variant="outline">Outline Button</Button>
<Button variant="ghost">Ghost Button</Button>
<Button variant="destructive">Delete</Button>
```

**Variants**:
- `default`: Blue primary button
- `secondary`: Green secondary button
- `outline`: Outlined button
- `ghost`: Transparent button
- `destructive`: Red danger button
- `link`: Link-styled button

**Sizes**: `sm`, `default`, `lg`, `icon`

#### Cards
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>
    Card content goes here
  </CardContent>
  <CardFooter>
    Card footer
  </CardFooter>
</Card>
```

#### Forms
```tsx
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"

<Label htmlFor="email">Email</Label>
<Input id="email" type="email" placeholder="student@example.com" />

<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select a topic" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="physics">Physics</SelectItem>
    <SelectItem value="chemistry">Chemistry</SelectItem>
  </SelectContent>
</Select>
```

#### Dialogs
```tsx
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>
        Dialog description text
      </DialogDescription>
    </DialogHeader>
    {/* Dialog content */}
  </DialogContent>
</Dialog>
```

#### Tables
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>John Doe</TableCell>
      <TableCell>Active</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

#### Tabs
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

<Tabs defaultValue="videos">
  <TabsList>
    <TabsTrigger value="videos">Videos</TabsTrigger>
    <TabsTrigger value="progress">Progress</TabsTrigger>
  </TabsList>
  <TabsContent value="videos">
    Video content
  </TabsContent>
  <TabsContent value="progress">
    Progress content
  </TabsContent>
</Tabs>
```

#### Toasts
```tsx
import { useToast } from "@/components/ui/use-toast"

const { toast } = useToast()

toast({
  title: "Success",
  description: "Your video is ready!",
})
```

### Component Installation

To add more components:

```bash
npx shadcn-ui@latest add [component-name]
```

Available components: https://ui.shadcn.com/docs/components

---

## Layout

### Responsive Breakpoints

```css
sm:  640px   /* Small devices */
md:  768px   /* Medium devices */
lg:  1024px  /* Large devices */
xl:  1280px  /* Extra large devices */
2xl: 1536px  /* 2X large devices */
```

### Container

```tsx
<div className="container mx-auto px-4">
  {/* Content automatically centered with max-width */}
</div>
```

### Grid Layouts

```tsx
{/* Responsive Grid */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <Card>Card 1</Card>
  <Card>Card 2</Card>
  <Card>Card 3</Card>
</div>

{/* Two-Column Layout */}
<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
  <div>Main Content</div>
  <div>Sidebar</div>
</div>
```

### Flexbox Patterns

```tsx
{/* Horizontal Stack */}
<div className="flex items-center gap-4">
  <Button>Action 1</Button>
  <Button>Action 2</Button>
</div>

{/* Vertical Stack */}
<div className="flex flex-col space-y-4">
  <Card>Item 1</Card>
  <Card>Item 2</Card>
</div>

{/* Space Between */}
<div className="flex items-center justify-between">
  <h2>Title</h2>
  <Button>Action</Button>
</div>
```

---

## Accessibility

### ARIA Labels

```tsx
<Button aria-label="Close dialog">
  <XIcon />
</Button>

<Input aria-describedby="email-error" />
<p id="email-error" role="alert">Invalid email</p>
```

### Keyboard Navigation

All interactive components support:
- **Tab**: Navigate between elements
- **Enter/Space**: Activate buttons
- **Arrow keys**: Navigate dropdowns, tabs
- **Escape**: Close dialogs, dropdowns

### Focus States

```css
/* Automatic focus rings on all interactive elements */
focus-visible:outline-none
focus-visible:ring-2
focus-visible:ring-ring
focus-visible:ring-offset-2
```

### Screen Reader Support

- Semantic HTML elements (`<header>`, `<nav>`, `<main>`, `<footer>`)
- Proper heading hierarchy (h1 → h2 → h3)
- Alt text for all images
- ARIA landmarks for complex UIs

---

## Usage Guidelines

### Adding shadcn/ui Components

```bash
# Install a specific component
npx shadcn-ui@latest add button

# Install multiple components
npx shadcn-ui@latest add button card dialog
```

Components are added to `src/components/ui/` and can be customized.

### Customizing Components

Edit components directly in `src/components/ui/`:

```tsx
// src/components/ui/button.tsx
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        // Add custom variant
        vividly: "bg-gradient-to-r from-vividly-blue to-vividly-purple text-white",
      },
    },
  }
)
```

### Dark Mode

```tsx
// Toggle dark mode
<html className="dark">
```

All components automatically adapt to dark mode using CSS variables.

### Utility Functions

```tsx
import { cn } from "@/lib/utils"

// Merge Tailwind classes
<div className={cn(
  "base-classes",
  isActive && "active-classes",
  className
)} />
```

---

## Development Workflow

### Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   └── ...           # Custom components
│   ├── lib/
│   │   └── utils.ts      # Utility functions
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html
├── package.json
├── tailwind.config.js
├── vite.config.ts
└── DESIGN_SYSTEM.md      # This file
```

---

## Resources

- **shadcn/ui Documentation**: https://ui.shadcn.com
- **Tailwind CSS Documentation**: https://tailwindcss.com/docs
- **Radix UI Documentation**: https://www.radix-ui.com/docs
- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
