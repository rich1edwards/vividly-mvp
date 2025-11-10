/**
 * Video Thumbnail Component
 *
 * Optimized thumbnail component specifically for video content:
 * - Lazy loading with Intersection Observer
 * - Responsive srcset for different screen sizes
 * - WebP format support with JPEG fallback
 * - Blur placeholder before load
 * - Error handling with gradient fallback
 * - Aspect ratio preservation (16:9 video standard)
 * - Play icon fallback
 * - Layout shift prevention
 * - Accessibility features
 */

import React, { useState } from 'react'
import { Play } from 'lucide-react'
import { OptimizedImage, generateSrcSet, generateSizes } from './OptimizedImage'
import { cn } from '@/lib/utils'

export interface VideoThumbnailProps {
  /** Thumbnail image URL */
  src?: string | null
  /** Alt text (defaults to "Video thumbnail") */
  alt?: string
  /** Video title for better accessibility */
  videoTitle?: string
  /** Duration badge text (e.g., "5:23") */
  duration?: string
  /** Show play icon overlay on hover */
  showPlayButton?: boolean
  /** Enable hover effect */
  enableHover?: boolean
  /** Loading priority (eager for above-fold thumbnails) */
  priority?: boolean
  /** Custom className for container */
  className?: string
  /** Custom className for image */
  imageClassName?: string
  /** Aspect ratio (default: 16/9 for video) */
  aspectRatio?: number
  /** Size variant for responsive images */
  size?: 'small' | 'medium' | 'large'
  /** Callback when thumbnail loads */
  onLoad?: () => void
  /** Callback when thumbnail fails to load */
  onError?: () => void
}

/**
 * Get responsive image configuration based on size variant
 */
const getSizeConfig = (size: 'small' | 'medium' | 'large') => {
  switch (size) {
    case 'small':
      return {
        widths: [192, 384], // 192px (1x), 384px (2x) for small thumbnails
        sizes: generateSizes([{ size: '192px' }])
      }
    case 'medium':
      return {
        widths: [320, 640, 960], // 320px, 640px, 960px for medium thumbnails
        sizes: generateSizes([
          { breakpoint: 640, size: '100vw' },
          { breakpoint: 1024, size: '50vw' },
          { size: '320px' }
        ])
      }
    case 'large':
      return {
        widths: [640, 960, 1280, 1920], // 640px to 1920px for large hero thumbnails
        sizes: generateSizes([
          { breakpoint: 640, size: '100vw' },
          { breakpoint: 1024, size: '75vw' },
          { size: '640px' }
        ])
      }
  }
}

/**
 * VideoThumbnail Component
 *
 * Optimized for video thumbnail display with responsive images and lazy loading
 */
export const VideoThumbnail: React.FC<VideoThumbnailProps> = ({
  src,
  alt,
  videoTitle,
  duration,
  showPlayButton = true,
  enableHover = true,
  priority = false,
  className,
  imageClassName,
  aspectRatio = 16 / 9,
  size = 'medium',
  onLoad,
  onError
}) => {
  const [isHovered, setIsHovered] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)

  const sizeConfig = getSizeConfig(size)
  const altText = alt || videoTitle ? `Thumbnail for ${videoTitle}` : 'Video thumbnail'

  /**
   * Handle image load
   */
  const handleLoad = () => {
    setImageLoaded(true)
    onLoad?.()
  }

  /**
   * Handle image error
   */
  const handleError = () => {
    onError?.()
  }

  /**
   * Render fallback gradient with play icon when no thumbnail
   */
  const renderFallback = () => (
    <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-vividly-blue/20 to-vividly-purple/20">
      <Play className="w-12 h-12 text-vividly-blue/40" strokeWidth={1.5} aria-hidden="true" />
    </div>
  )

  return (
    <div
      className={cn(
        'relative overflow-hidden bg-muted',
        enableHover && 'group',
        className
      )}
      onMouseEnter={() => enableHover && setIsHovered(true)}
      onMouseLeave={() => enableHover && setIsHovered(false)}
      style={{ aspectRatio: aspectRatio.toString() }}
    >
      {/* Thumbnail Image or Fallback */}
      {src ? (
        <OptimizedImage
          src={src}
          alt={altText}
          srcSet={generateSrcSet(src, sizeConfig.widths)}
          sizes={sizeConfig.sizes}
          aspectRatio={aspectRatio}
          fallbackSrc={undefined} // Will show gradient fallback instead
          objectFit="cover"
          lazy={!priority}
          priority={priority}
          onLoad={handleLoad}
          onError={handleError}
          className={cn('absolute inset-0', imageClassName)}
          containerClassName="absolute inset-0"
        />
      ) : (
        renderFallback()
      )}

      {/* Play Button Overlay (on hover) */}
      {showPlayButton && imageLoaded && (
        <div
          className={cn(
            'absolute inset-0 bg-black/40 flex items-center justify-center transition-opacity duration-200',
            enableHover && isHovered ? 'opacity-100' : 'opacity-0'
          )}
          aria-hidden="true"
        >
          <div className="bg-white rounded-full p-3 transform transition-transform duration-200 group-hover:scale-110 shadow-lg">
            <Play className="w-8 h-8 text-vividly-blue fill-vividly-blue" />
          </div>
        </div>
      )}

      {/* Duration Badge */}
      {duration && (
        <div
          className="absolute bottom-2 right-2 bg-black/80 text-white text-xs font-mono px-2 py-1 rounded backdrop-blur-sm"
          aria-label={`Duration: ${duration}`}
        >
          {duration}
        </div>
      )}
    </div>
  )
}

/**
 * Skeleton Loading Component for VideoThumbnail
 */
export const VideoThumbnailSkeleton: React.FC<{
  aspectRatio?: number
  className?: string
}> = ({ aspectRatio = 16 / 9, className }) => {
  return (
    <div
      className={cn(
        'relative overflow-hidden bg-muted animate-pulse',
        className
      )}
      style={{ aspectRatio: aspectRatio.toString() }}
      aria-busy="true"
      aria-label="Loading video thumbnail"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-muted to-muted/50" />
      <div className="absolute inset-0 flex items-center justify-center">
        <Play className="w-12 h-12 text-muted-foreground/20" strokeWidth={1.5} aria-hidden="true" />
      </div>
    </div>
  )
}

export default VideoThumbnail
