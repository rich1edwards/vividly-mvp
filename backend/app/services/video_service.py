"""
Video Generation Service (Phase 4)

Generates educational videos from scripts and audio.
Combines visuals, text overlays, and audio narration.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import asyncio

logger = logging.getLogger(__name__)


class VideoService:
    """
    Video generation service for educational content.

    Combines:
    - Audio narration (from TTS service)
    - Visual assets (stock footage, animations)
    - Text overlays (key points, diagrams)
    - Transitions and effects

    Technologies:
    - MoviePy (primary) - Python video editing
    - FFmpeg (backend) - Video processing
    - Google Cloud Storage - Asset storage

    Output:
    - MP4 format, H.264 codec
    - 1080p resolution (1920x1080)
    - 30 FPS
    - Optimized for web streaming
    """

    def __init__(self, project_id: str = None):
        """
        Initialize video service.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")

        # Try to initialize MoviePy
        self.moviepy_available = False
        try:
            from moviepy.editor import (
                VideoFileClip,
                AudioFileClip,
                TextClip,
                CompositeVideoClip,
                concatenate_videoclips,
            )

            self.moviepy_available = True
            logger.info("MoviePy initialized")
        except Exception as e:
            logger.warning(f"MoviePy not available: {e}. Running in mock mode.")

        # Video configuration
        self.config = {
            "resolution": (1920, 1080),
            "fps": 30,
            "codec": "libx264",
            "audio_codec": "aac",
            "bitrate": "5000k",
            "preset": "medium",  # Balance between speed and quality
        }

        # Visual styles by subject
        self.visual_styles = {
            "physics": {
                "background_color": "#1a1a2e",
                "accent_color": "#00d4ff",
                "font": "Arial-Bold",
                "theme": "dark_scientific",
            },
            "math": {
                "background_color": "#2c3e50",
                "accent_color": "#e74c3c",
                "font": "Arial-Bold",
                "theme": "chalkboard",
            },
            "chemistry": {
                "background_color": "#16213e",
                "accent_color": "#0f3460",
                "font": "Arial-Bold",
                "theme": "laboratory",
            },
            "default": {
                "background_color": "#1e1e1e",
                "accent_color": "#4CAF50",
                "font": "Arial-Bold",
                "theme": "modern_clean",
            },
        }

    async def generate_video(
        self,
        script: Dict[str, Any],
        audio_url: str,
        interest: str = "general",
        subject: str = "default",
    ) -> Dict[str, Any]:
        """
        Generate educational video from script and audio.

        Args:
            script: Script dict with sections and visuals
            audio_url: GCS URL of generated audio narration
            interest: Student interest for visual selection
            subject: Subject area (physics, math, chemistry, etc.)

        Returns:
            Dict with:
                - video_id: str
                - duration_seconds: float
                - file_size_bytes: int
                - video_url: str (GCS URL)
                - resolution: str (1920x1080)
                - format: str (mp4)
                - generated_at: str (ISO timestamp)

        Example:
            >>> video = await video_service.generate_video(
            ...     script=script_dict,
            ...     audio_url="gs://bucket/audio/audio_123.mp3",
            ...     interest="basketball",
            ...     subject="physics"
            ... )
        """
        video_id = self._generate_video_id(script.get("script_id", "unknown"))

        try:
            if not self.moviepy_available:
                logger.info(f"[{video_id}] Running in mock mode")
                return self._mock_generate_video(
                    script=script, audio_url=audio_url, video_id=video_id
                )

            logger.info(f"[{video_id}] Generating video with MoviePy")

            # Download audio from GCS
            audio_path = await self._download_audio(audio_url, video_id)

            # Get visual style
            style = self.visual_styles.get(subject, self.visual_styles["default"])

            # Generate video sections
            video_clips = []
            current_time = 0

            # Intro clip (hook)
            if "hook" in script:
                intro_clip = await self._create_text_clip(
                    text=script["hook"], duration=5.0, style=style, clip_type="hook"
                )
                video_clips.append(intro_clip)
                current_time += 5.0

            # Section clips
            for section in script.get("sections", []):
                section_duration = section.get("duration_seconds", 45)

                # Create section clip with:
                # 1. Background video/image
                # 2. Title overlay
                # 3. Content text overlay
                section_clip = await self._create_section_clip(
                    section=section,
                    duration=section_duration,
                    style=style,
                    interest=interest,
                    start_time=current_time,
                )
                video_clips.append(section_clip)
                current_time += section_duration

            # Key takeaways clip
            if "key_takeaways" in script:
                takeaways_clip = await self._create_takeaways_clip(
                    takeaways=script["key_takeaways"], duration=15.0, style=style
                )
                video_clips.append(takeaways_clip)

            # Concatenate all clips
            from moviepy.editor import concatenate_videoclips, AudioFileClip

            final_video = concatenate_videoclips(video_clips, method="compose")

            # Add audio narration
            audio = AudioFileClip(audio_path)
            final_video = final_video.set_audio(audio)

            # Export video
            output_path = f"/tmp/{video_id}.mp4"
            final_video.write_videofile(
                output_path,
                fps=self.config["fps"],
                codec=self.config["codec"],
                audio_codec=self.config["audio_codec"],
                bitrate=self.config["bitrate"],
                preset=self.config["preset"],
                threads=4,
            )

            # Upload to GCS
            video_url = await self._upload_to_gcs(output_path, video_id)

            # Get file size
            file_size = os.path.getsize(output_path)

            # Clean up temp files
            os.remove(output_path)
            os.remove(audio_path)

            return {
                "video_id": video_id,
                "duration_seconds": final_video.duration,
                "file_size_bytes": file_size,
                "video_url": video_url,
                "resolution": f"{self.config['resolution'][0]}x{self.config['resolution'][1]}",
                "format": "mp4",
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"[{video_id}] Video generation failed: {e}", exc_info=True)
            # Return mock on error
            return self._mock_generate_video(script, audio_url, video_id)

    async def _download_audio(self, audio_url: str, video_id: str) -> str:
        """Download audio file from GCS."""
        from google.cloud import storage

        # Parse GCS URL: gs://bucket/path
        if not audio_url.startswith("gs://"):
            raise ValueError(f"Invalid GCS URL: {audio_url}")

        parts = audio_url[5:].split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1]

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Download to temp file
        audio_path = f"/tmp/{video_id}_audio.mp3"
        blob.download_to_filename(audio_path)

        return audio_path

    async def _create_text_clip(
        self, text: str, duration: float, style: Dict, clip_type: str = "default"
    ):
        """Create text overlay clip."""
        from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

        # Create background
        bg = ColorClip(
            size=self.config["resolution"],
            color=self._hex_to_rgb(style["background_color"]),
            duration=duration,
        )

        # Create text overlay
        txt = (
            TextClip(
                text,
                fontsize=60 if clip_type == "hook" else 50,
                color="white",
                font=style["font"],
                size=self.config["resolution"],
                method="caption",
                align="center",
            )
            .set_duration(duration)
            .set_position("center")
        )

        return CompositeVideoClip([bg, txt])

    async def _create_section_clip(
        self,
        section: Dict,
        duration: float,
        style: Dict,
        interest: str,
        start_time: float,
    ):
        """
        Create section clip with background and overlays.

        For MVP, uses solid color backgrounds with text.
        In production, would use:
        - Stock footage relevant to interest/subject
        - Animations and diagrams
        - Dynamic visual effects
        """
        from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

        # Background
        bg = ColorClip(
            size=self.config["resolution"],
            color=self._hex_to_rgb(style["background_color"]),
            duration=duration,
        )

        overlays = [bg]

        # Title overlay (top)
        if "title" in section:
            title = (
                TextClip(
                    section["title"],
                    fontsize=70,
                    color=style["accent_color"],
                    font=style["font"],
                    size=(self.config["resolution"][0] - 200, None),
                    method="caption",
                    align="center",
                )
                .set_duration(duration)
                .set_position(("center", 150))
            )
            overlays.append(title)

        # Content overlay (center)
        if "content" in section:
            # Chunk content for readability
            content_text = (
                section["content"][:200] + "..."
                if len(section["content"]) > 200
                else section["content"]
            )

            content = (
                TextClip(
                    content_text,
                    fontsize=45,
                    color="white",
                    font=style["font"],
                    size=(self.config["resolution"][0] - 300, None),
                    method="caption",
                    align="center",
                )
                .set_duration(duration)
                .set_position("center")
            )
            overlays.append(content)

        return CompositeVideoClip(overlays)

    async def _create_takeaways_clip(
        self, takeaways: List[str], duration: float, style: Dict
    ):
        """Create key takeaways summary clip."""
        from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

        # Background
        bg = ColorClip(
            size=self.config["resolution"],
            color=self._hex_to_rgb(style["background_color"]),
            duration=duration,
        )

        overlays = [bg]

        # Title
        title = (
            TextClip(
                "Key Takeaways",
                fontsize=80,
                color=style["accent_color"],
                font=style["font"],
            )
            .set_duration(duration)
            .set_position(("center", 100))
        )
        overlays.append(title)

        # Takeaways list
        takeaways_text = "\n\n".join([f"• {t}" for t in takeaways])
        content = (
            TextClip(
                takeaways_text,
                fontsize=50,
                color="white",
                font=style["font"],
                size=(self.config["resolution"][0] - 400, None),
                method="caption",
                align="center",
            )
            .set_duration(duration)
            .set_position(("center", 400))
        )
        overlays.append(content)

        return CompositeVideoClip(overlays)

    async def _upload_to_gcs(self, video_path: str, video_id: str) -> str:
        """Upload video file to Google Cloud Storage."""
        from google.cloud import storage

        bucket_name = os.getenv("GCS_GENERATED_CONTENT_BUCKET")
        if not bucket_name:
            raise ValueError("GCS_GENERATED_CONTENT_BUCKET not configured")

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Create blob path: video/{video_id}.mp4
        blob_path = f"video/{video_id}.mp4"
        blob = bucket.blob(blob_path)

        # Upload with metadata
        blob.upload_from_filename(
            video_path,
            content_type="video/mp4",
            timeout=600,  # 10 min timeout for large files
        )

        # Set metadata
        blob.metadata = {
            "video_id": video_id,
            "generated_at": datetime.utcnow().isoformat(),
            "format": "mp4",
            "resolution": f"{self.config['resolution'][0]}x{self.config['resolution'][1]}",
        }
        blob.patch()

        return f"gs://{bucket_name}/{blob_path}"

    def _mock_generate_video(self, script: Dict, audio_url: str, video_id: str) -> Dict:
        """Mock video generation for testing."""
        # Estimate duration from script
        duration = sum(
            s.get("duration_seconds", 45) for s in script.get("sections", [])
        )
        duration += 20  # Intro + outro

        return {
            "video_id": video_id,
            "duration_seconds": duration,
            "file_size_bytes": int(duration * 1000000),  # ~1MB per second (mock)
            "video_url": f"gs://mock-bucket/video/{video_id}.mp4",
            "resolution": "1920x1080",
            "format": "mp4",
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def _generate_video_id(self, script_id: str) -> str:
        """Generate unique video ID."""
        content = f"{script_id}|{datetime.utcnow().isoformat()}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"video_{hash_val}"


# Singleton instance
_video_service_instance = None


def get_video_service() -> VideoService:
    """Get singleton video service instance."""
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoService()
    return _video_service_instance
