/**
 * VideoPlayer Component
 *
 * Comprehensive video player for Vividly personalized learning videos.
 * Built with Plyr for accessibility and cross-browser support.
 *
 * Features:
 * - Playback speed control (0.5x - 2x)
 * - Quality selection (if multiple sources provided)
 * - Closed captions/subtitles
 * - Picture-in-Picture
 * - Keyboard shortcuts
 * - Progress tracking and analytics
 * - Resume from last position
 * - Engagement metrics (pause, rewind, completion)
 *
 * @see https://github.com/sampotts/plyr
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import Plyr from 'plyr';
import 'plyr/dist/plyr.css';

interface VideoSource {
  src: string;
  type: string;  // e.g., 'video/mp4'
  size?: number; // e.g., 720, 1080 for quality selection
}

interface VideoTrack {
  kind: 'captions' | 'subtitles';
  label: string;
  srclang: string;
  src: string;
  default?: boolean;
}

interface ProgressData {
  currentTime: number;
  duration: number;
  percentComplete: number;
}

interface AnalyticsEvent {
  type: 'play' | 'pause' | 'ended' | 'seeked' | 'ratechange' | 'qualitychange';
  timestamp: number;
  currentTime: number;
  metadata?: Record<string, any>;
}

export interface VideoPlayerProps {
  /** Video sources (multiple for quality selection) */
  sources: VideoSource[];

  /** Optional caption/subtitle tracks */
  tracks?: VideoTrack[];

  /** Video poster image URL */
  poster?: string;

  /** Content ID for tracking */
  contentId: string;

  /** Student ID for progress tracking */
  studentId: string;

  /** Resume from this position (seconds) */
  startTime?: number;

  /** Progress update interval (seconds) */
  progressInterval?: number;

  /** Callback when video progress updates */
  onProgress?: (data: ProgressData) => void;

  /** Callback when video ends */
  onComplete?: () => void;

  /** Callback for analytics events */
  onAnalytics?: (event: AnalyticsEvent) => void;

  /** Additional Plyr options */
  options?: Plyr.Options;

  /** Custom CSS classes */
  className?: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  sources,
  tracks = [],
  poster,
  contentId,
  studentId,
  startTime = 0,
  progressInterval = 10,
  onProgress,
  onComplete,
  onAnalytics,
  options = {},
  className = '',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<Plyr | null>(null);
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastProgressTimeRef = useRef<number>(0);

  const [isReady, setIsReady] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  /**
   * Send analytics event
   */
  const sendAnalyticsEvent = useCallback(
    (
      type: AnalyticsEvent['type'],
      metadata?: Record<string, any>
    ) => {
      if (!playerRef.current || !onAnalytics) return;

      const event: AnalyticsEvent = {
        type,
        timestamp: Date.now(),
        currentTime: playerRef.current.currentTime,
        metadata: {
          contentId,
          studentId,
          duration: playerRef.current.duration,
          ...metadata,
        },
      };

      onAnalytics(event);
    },
    [contentId, studentId, onAnalytics]
  );

  /**
   * Track video progress
   */
  const trackProgress = useCallback(() => {
    if (!playerRef.current || !onProgress) return;

    const currentTime = playerRef.current.currentTime;
    const duration = playerRef.current.duration;

    // Only track if enough time has passed
    if (currentTime - lastProgressTimeRef.current >= progressInterval) {
      const progressData: ProgressData = {
        currentTime,
        duration,
        percentComplete: (currentTime / duration) * 100,
      };

      onProgress(progressData);
      lastProgressTimeRef.current = currentTime;
    }
  }, [onProgress, progressInterval]);

  /**
   * Start progress tracking interval
   */
  const startProgressTracking = useCallback(() => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }

    progressTimerRef.current = setInterval(() => {
      trackProgress();
    }, 1000); // Check every second
  }, [trackProgress]);

  /**
   * Stop progress tracking interval
   */
  const stopProgressTracking = useCallback(() => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  /**
   * Initialize Plyr player
   */
  useEffect(() => {
    if (!videoRef.current) return;

    const plyrOptions: Plyr.Options = {
      controls: [
        'play-large',
        'play',
        'progress',
        'current-time',
        'duration',
        'mute',
        'volume',
        'captions',
        'settings',
        'pip',
        'fullscreen',
      ],
      settings: ['captions', 'quality', 'speed'],
      speed: {
        selected: 1,
        options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
      },
      quality: {
        default: sources.find((s) => s.size === 720)?.size || sources[0].size,
        options: sources.map((s) => s.size).filter((size) => size !== undefined) as number[],
        forced: true,
        onChange: (quality: number) => {
          sendAnalyticsEvent('qualitychange', { quality });
        },
      },
      captions: {
        active: tracks.some((t) => t.default),
        language: 'auto',
        update: true,
      },
      keyboard: {
        focused: true,
        global: false,
      },
      tooltips: {
        controls: true,
        seek: true,
      },
      ...options,
    };

    // Initialize Plyr
    const player = new Plyr(videoRef.current, plyrOptions);
    playerRef.current = player;

    // Event listeners
    player.on('ready', () => {
      setIsReady(true);

      // Resume from saved position
      if (startTime > 0) {
        player.currentTime = startTime;
      }
    });

    player.on('play', () => {
      if (!hasStarted) {
        setHasStarted(true);
        sendAnalyticsEvent('play', { isFirstPlay: true });
      } else {
        sendAnalyticsEvent('play', { isFirstPlay: false });
      }
      startProgressTracking();
    });

    player.on('pause', () => {
      sendAnalyticsEvent('pause');
      stopProgressTracking();
    });

    player.on('ended', () => {
      sendAnalyticsEvent('ended', { completionRate: 100 });
      stopProgressTracking();

      // Final progress update
      trackProgress();

      if (onComplete) {
        onComplete();
      }
    });

    player.on('seeked', () => {
      sendAnalyticsEvent('seeked', {
        from: lastProgressTimeRef.current,
        to: player.currentTime,
      });
    });

    player.on('ratechange', () => {
      sendAnalyticsEvent('ratechange', { rate: player.speed });
    });

    player.on('qualitychange', (event: any) => {
      sendAnalyticsEvent('qualitychange', { quality: event.detail.quality });
    });

    // Cleanup
    return () => {
      stopProgressTracking();
      player.destroy();
    };
  }, [
    sources,
    tracks,
    startTime,
    hasStarted,
    options,
    onComplete,
    sendAnalyticsEvent,
    startProgressTracking,
    stopProgressTracking,
    trackProgress,
  ]);

  return (
    <div className={`vividly-video-player ${className}`}>
      <video
        ref={videoRef}
        poster={poster}
        playsInline
        crossOrigin="anonymous"
        data-content-id={contentId}
        data-student-id={studentId}
      >
        {/* Video sources */}
        {sources.map((source, index) => (
          <source
            key={index}
            src={source.src}
            type={source.type}
            size={source.size}
          />
        ))}

        {/* Caption/subtitle tracks */}
        {tracks.map((track, index) => (
          <track
            key={index}
            kind={track.kind}
            label={track.label}
            srcLang={track.srclang}
            src={track.src}
            default={track.default}
          />
        ))}
      </video>

      {/* Loading state */}
      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50">
          <div className="text-white">Loading video...</div>
        </div>
      )}
    </div>
  );
};

/**
 * Hook for tracking video progress
 *
 * Usage:
 *   const { saveProgress, getLastProgress } = useVideoProgress(contentId, studentId);
 */
export const useVideoProgress = (contentId: string, studentId: string) => {
  const [lastProgress, setLastProgress] = useState<ProgressData | null>(null);

  /**
   * Save progress to backend
   */
  const saveProgress = useCallback(
    async (data: ProgressData) => {
      try {
        const response = await fetch('/api/v1/progress', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            content_id: contentId,
            student_id: studentId,
            current_time: data.currentTime,
            duration: data.duration,
            percent_complete: data.percentComplete,
            timestamp: new Date().toISOString(),
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to save progress');
        }

        setLastProgress(data);
      } catch (error) {
        console.error('Error saving video progress:', error);
      }
    },
    [contentId, studentId]
  );

  /**
   * Get last saved progress from backend
   */
  const getLastProgress = useCallback(async (): Promise<number> => {
    try {
      const response = await fetch(
        `/api/v1/progress/${contentId}/${studentId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        return 0;
      }

      const data = await response.json();
      return data.current_time || 0;
    } catch (error) {
      console.error('Error fetching video progress:', error);
      return 0;
    }
  }, [contentId, studentId]);

  return {
    saveProgress,
    getLastProgress,
    lastProgress,
  };
};

/**
 * Hook for tracking video analytics
 *
 * Usage:
 *   const { trackEvent } = useVideoAnalytics(contentId, studentId);
 */
export const useVideoAnalytics = (contentId: string, studentId: string) => {
  const trackEvent = useCallback(
    async (event: AnalyticsEvent) => {
      try {
        await fetch('/api/v1/analytics/video', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            ...event,
            content_id: contentId,
            student_id: studentId,
          }),
        });
      } catch (error) {
        console.error('Error tracking video analytics:', error);
      }
    },
    [contentId, studentId]
  );

  return { trackEvent };
};

export default VideoPlayer;
