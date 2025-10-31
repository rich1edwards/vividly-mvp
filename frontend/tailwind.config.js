/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Shadcn/UI semantic colors (HSL-based)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },

        // Vividly Design System Colors
        vividly: {
          // Primary - Vivid Blue
          blue: {
            DEFAULT: "#2196F3",
            50: "#E3F2FD",
            100: "#BBDEFB",
            200: "#90CAF9",
            300: "#64B5F6",
            400: "#42A5F5",
            500: "#2196F3",
            600: "#1E88E5",
            700: "#1976D2",
            800: "#1565C0",
            900: "#0D47A1",
          },
          // Secondary - Warm Coral
          coral: {
            DEFAULT: "#FF7043",
            50: "#FBE9E7",
            100: "#FFCCBC",
            200: "#FFAB91",
            300: "#FF8A65",
            400: "#FF7043",
            500: "#FF5722",
            600: "#F4511E",
            700: "#E64A19",
            800: "#D84315",
            900: "#BF360C",
          },
          // Accent - Electric Purple
          purple: {
            DEFAULT: "#9C27B0",
            50: "#F3E5F5",
            100: "#E1BEE7",
            200: "#CE93D8",
            300: "#BA68C8",
            400: "#AB47BC",
            500: "#9C27B0",
            600: "#8E24AA",
            700: "#7B1FA2",
            800: "#6A1B9A",
            900: "#4A148C",
          },
          // Success - Fresh Green
          green: {
            DEFAULT: "#4CAF50",
            50: "#E8F5E9",
            100: "#C8E6C9",
            200: "#A5D6A7",
            300: "#81C784",
            400: "#66BB6A",
            500: "#4CAF50",
            600: "#43A047",
            700: "#388E3C",
            800: "#2E7D32",
            900: "#1B5E20",
          },
          // Warning - Sunny Yellow
          yellow: {
            DEFAULT: "#FFC107",
            50: "#FFF8E1",
            100: "#FFECB3",
            200: "#FFE082",
            300: "#FFD54F",
            400: "#FFCA28",
            500: "#FFC107",
            600: "#FFB300",
            700: "#FFA000",
            800: "#FF8F00",
            900: "#FF6F00",
          },
          // Error - Alert Red
          red: {
            DEFAULT: "#F44336",
            50: "#FFEBEE",
            100: "#FFCDD2",
            200: "#EF9A9A",
            300: "#E57373",
            400: "#EF5350",
            500: "#F44336",
            600: "#E53935",
            700: "#D32F2F",
            800: "#C62828",
            900: "#B71C1C",
          },
          // Neutral - Cool Gray
          gray: {
            DEFAULT: "#607D8B",
            50: "#ECEFF1",
            100: "#CFD8DC",
            200: "#B0BEC5",
            300: "#90A4AE",
            400: "#78909C",
            500: "#607D8B",
            600: "#546E7A",
            700: "#455A64",
            800: "#37474F",
            900: "#263238",
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Poppins', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // Type scale with 1.250 ratio
        'xs': ['0.640rem', { lineHeight: '1.5', letterSpacing: '0.01em' }],      // 10.24px
        'sm': ['0.800rem', { lineHeight: '1.5', letterSpacing: '0.01em' }],      // 12.8px
        'base': ['1rem', { lineHeight: '1.5', letterSpacing: '0' }],             // 16px
        'lg': ['1.250rem', { lineHeight: '1.4', letterSpacing: '-0.01em' }],     // 20px
        'xl': ['1.563rem', { lineHeight: '1.3', letterSpacing: '-0.01em' }],     // 25px
        '2xl': ['1.953rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],    // 31.25px
        '3xl': ['2.441rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],    // 39px
        '4xl': ['3.052rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],    // 48.83px
        '5xl': ['3.815rem', { lineHeight: '1.1', letterSpacing: '-0.03em' }],    // 61.04px
      },
      spacing: {
        // 8px base grid
        '0': '0',
        '0.5': '0.25rem',   // 4px
        '1': '0.5rem',      // 8px
        '2': '1rem',        // 16px
        '3': '1.5rem',      // 24px
        '4': '2rem',        // 32px
        '5': '2.5rem',      // 40px
        '6': '3rem',        // 48px
        '7': '3.5rem',      // 56px
        '8': '4rem',        // 64px
        '10': '5rem',       // 80px
        '12': '6rem',       // 96px
      },
      borderRadius: {
        'none': '0',
        'sm': '0.25rem',    // 4px
        DEFAULT: '0.5rem',  // 8px
        'md': '0.75rem',    // 12px
        'lg': '1rem',       // 16px
        'xl': '1.5rem',     // 24px
        '2xl': '2rem',      // 32px
        'full': '9999px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 2px 8px 0 rgba(0, 0, 0, 0.1)',
        'md': '0 4px 16px 0 rgba(0, 0, 0, 0.1)',
        'lg': '0 8px 24px 0 rgba(0, 0, 0, 0.15)',
        'xl': '0 16px 48px 0 rgba(0, 0, 0, 0.2)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-in-from-top": {
          from: { transform: "translateY(-10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        "slide-in-from-bottom": {
          from: { transform: "translateY(10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.2s ease-out",
        "slide-in-top": "slide-in-from-top 0.3s ease-out",
        "slide-in-bottom": "slide-in-from-bottom 0.3s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
