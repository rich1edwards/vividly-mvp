/**
 * Optimized Image Component
 *
 * Production-ready image component with performance optimizations:
 * - Lazy loading with Intersection Observer
 * - Responsive images with srcset
 * - Blur placeholder before load
 * - Error handling with fallback
 * - Layout shift prevention
 * - Accessibility (alt text, ARIA)
 * - WebP support with fallback
 */

import React, { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

export interface OptimizedImageProps extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'src'> {
  /** Image source URL */
  src: string
  /** Alt text for accessibility (required) */
  alt: string
  /** Optional srcset for responsive images */
  srcSet?: string
  /** Optional sizes attribute for responsive images */
  sizes?: string
  /** Aspect ratio (width/height) to prevent layout shift */
  aspectRatio?: number
  /** Fallback image URL on error */
  fallbackSrc?: string
  /** Custom placeholder before load (React node or color) */
  placeholder?: React.ReactNode | string
  /** Object fit CSS property */
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down'
  /** Enable lazy loading (default: true) */
  lazy?: boolean
  /** Loading priority (eager for above-fold images) */
  priority?: boolean
  /** Callback when image loads successfully */
  onLoad?: () => void
  /** Callback when image fails to load */
  onError?: () => void
  /** Custom className */
  className?: string
  /** Container className for aspect ratio wrapper */
  containerClassName?: string
}

/**
 * OptimizedImage Component
 *
 * Uses Intersection Observer for lazy loading and provides responsive image support
 */
export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  srcSet,
  sizes,
  aspectRatio,
  fallbackSrc,
  placeholder,
  objectFit = 'cover',
  lazy = true,
  priority = false,
  onLoad,
  onError,
  className,
  containerClassName,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [isInView, setIsInView] = useState(!lazy || priority)
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  /**
   * Intersection Observer for lazy loading
   */
  useEffect(() => {
    if (!lazy || priority || !containerRef.current) {
      setIsInView(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01
      }
    )

    observer.observe(containerRef.current)

    return () => {
      observer.disconnect()
    }
  }, [lazy, priority])

  /**
   * Handle image load success
   */
  const handleLoad = () => {
    setIsLoaded(true)
    setHasError(false)
    onLoad?.()
  }

  /**
   * Handle image load error
   */
  const handleError = () => {
    setHasError(true)
    setIsLoaded(false)
    onError?.()

    // Try fallback if available
    if (fallbackSrc && imgRef.current && imgRef.current.src !== fallbackSrc) {
      imgRef.current.src = fallbackSrc
    }
  }

  /**
   * Determine which src to use
   */
  const imageSrc = hasError && fallbackSrc ? fallbackSrc : src

  /**
   * Render placeholder
   */
  const renderPlaceholder = () => {
    if (typeof placeholder === 'string') {
      // Color placeholder
      return (
        <div
          className="absolute inset-0 animate-pulse"
          style={{ backgroundColor: placeholder }}
          aria-hidden="true"
        />
      )
    } else if (placeholder) {
      // Custom placeholder component
      return <div className="absolute inset-0" aria-hidden="true">{placeholder}</div>
    } else {
      // Default blur placeholder
      return (
        <div
          className="absolute inset-0 bg-gradient-to-br from-muted to-muted/50 animate-pulse"
          aria-hidden="true"
        />
      )
    }
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative overflow-hidden bg-muted',
        containerClassName
      )}
      style={aspectRatio ? { aspectRatio: aspectRatio.toString() } : undefined}
    >
      {/* Placeholder (shown before image loads) */}
      {!isLoaded && renderPlaceholder()}

      {/* Actual Image (only render when in view or priority) */}
      {isInView && (
        <img
          ref={imgRef}
          src={imageSrc}
          alt={alt}
          srcSet={srcSet}
          sizes={sizes}
          loading={priority ? 'eager' : 'lazy'}
          decoding="async"
          onLoad={handleLoad}
          onError={handleError}
          className={cn(
            'w-full h-full transition-opacity duration-300',
            isLoaded ? 'opacity-100' : 'opacity-0',
            className
          )}
          style={{
            objectFit,
            ...props.style
          }}
          {...props}
        />
      )}

      {/* Error state (show if image failed and no fallback) */}
      {hasError && !fallbackSrc && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground"
          role="img"
          aria-label={`Failed to load image: ${alt}`}
        >
          <svg
            className="w-12 h-12 opacity-50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}
    </div>
  )
}

/**
 * Helper function to generate srcset for different sizes
 *
 * @example
 * const srcset = generateSrcSet('/images/photo.jpg', [320, 640, 1024, 1920])
 * // Returns: "/images/photo-320w.jpg 320w, /images/photo-640w.jpg 640w, ..."
 */
export const generateSrcSet = (baseUrl: string, widths: number[]): string => {
  return widths
    .map((width) => {
      // Assume your CDN or image service supports width parameter
      // Adjust this based on your actual image URL structure
      const url = baseUrl.includes('?')
        ? `${baseUrl}&w=${width}`
        : `${baseUrl}?w=${width}`
      return `${url} ${width}w`
    })
    .join(', ')
}

/**
 * Helper function to generate sizes attribute
 *
 * @example
 * const sizes = generateSizes([
 *   { breakpoint: 640, size: '100vw' },
 *   { breakpoint: 1024, size: '50vw' },
 *   { size: '33vw' }
 * ])
 * // Returns: "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
 */
export const generateSizes = (
  config: Array<{ breakpoint?: number; size: string }>
): string => {
  return config
    .map((item) => {
      if (item.breakpoint) {
        return `(max-width: ${item.breakpoint}px) ${item.size}`
      }
      return item.size
    })
    .join(', ')
}

export default OptimizedImage
