"""
Content Generation Module Interface

This is the PUBLIC API for content generation. All code outside this module
should interact ONLY through this interface, never importing internal implementation.

DEPENDENCIES: None (pure data structures)
EXTERNAL CALLS: (implementation handles Vertex AI, GCS, etc.)
DATABASE: (implementation handles ContentMetadata, Topics, etc.)

TOKEN BUDGET: ~500 tokens (can be loaded in any session)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class GenerationStatus(Enum):
    """Status of content generation request"""

    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some modalities succeeded, others failed


class Modality(Enum):
    """Supported content modalities"""

    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGES = "images"


@dataclass
class GenerationRequest:
    """
    Input contract for content generation.

    This is what the module NEEDS to generate content.
    Keep this minimal - only essential information.
    """

    # Required fields
    student_query: str
    student_id: str
    grade_level: int

    # Optional fields
    interest: Optional[str] = None
    requested_modalities: List[str] = field(default_factory=lambda: ["video"])
    preferred_modality: str = "video"

    # Advanced options (for future expansion)
    modality_preferences: Optional[Dict[str, Any]] = None
    custom_context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate request data"""
        if not self.student_query or not self.student_query.strip():
            raise ValueError("student_query cannot be empty")

        if self.grade_level < 1 or self.grade_level > 12:
            raise ValueError("grade_level must be between 1 and 12")

        # Normalize modalities
        valid_modalities = {"text", "audio", "video", "images"}
        self.requested_modalities = [
            m.lower()
            for m in self.requested_modalities
            if m.lower() in valid_modalities
        ]

        if not self.requested_modalities:
            self.requested_modalities = ["video"]  # Default fallback


@dataclass
class GenerationResult:
    """
    Output contract for content generation.

    This is what the module RETURNS after generation.
    Contains everything needed to use the generated content.
    """

    # Status
    status: GenerationStatus
    generation_id: str

    # Generated content (keys match modality types)
    content: Dict[str, Any]  # e.g., {"script": {...}, "audio": {...}, "video": {...}}

    # Metadata
    metadata: Dict[str, Any]  # Timestamps, costs, processing times, etc.

    # Error information (if status is FAILED or PARTIAL)
    error: Optional[str] = None
    failed_modalities: Optional[List[str]] = None

    # Cost tracking
    total_cost_usd: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None

    @property
    def is_successful(self) -> bool:
        """Check if generation was successful"""
        return self.status == GenerationStatus.COMPLETED

    @property
    def has_video(self) -> bool:
        """Check if video was generated"""
        return "video" in self.content and self.content["video"] is not None

    @property
    def has_audio(self) -> bool:
        """Check if audio was generated"""
        return "audio" in self.content and self.content["audio"] is not None

    @property
    def has_script(self) -> bool:
        """Check if script was generated"""
        return "script" in self.content and self.content["script"] is not None


class ContentGenerationInterface:
    """
    The ONLY way to interact with content generation.

    Implementation details are hidden behind this interface.
    This allows us to refactor the implementation without affecting callers.

    Usage:
        from modules.content_generation import create_content_service

        service = create_content_service(dependencies)
        request = GenerationRequest(
            student_query="Explain photosynthesis",
            student_id="student_123",
            grade_level=10,
            requested_modalities=["text", "audio"]
        )
        result = await service.generate(request)

        if result.is_successful:
            print(f"Generated: {list(result.content.keys())}")
            print(f"Cost: ${result.total_cost_usd:.3f}")
    """

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate educational content based on request.

        This is an async operation that may take 10-60 seconds depending
        on requested modalities:
        - Text only: ~5-10 seconds
        - Text + Audio: ~10-15 seconds
        - Text + Audio + Video: ~30-60 seconds

        Args:
            request: GenerationRequest with query and preferences

        Returns:
            GenerationResult with generated content and metadata

        Raises:
            ValueError: If request is invalid
            Exception: If generation fails critically
        """
        raise NotImplementedError("Subclass must implement generate()")

    async def get_generation_status(
        self, generation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get status of a previously started generation.

        Useful for long-running generations or polling.

        Args:
            generation_id: ID returned from generate()

        Returns:
            Status dict with progress information, or None if not found
        """
        raise NotImplementedError("Subclass must implement get_generation_status()")

    async def cancel_generation(self, generation_id: str) -> bool:
        """
        Attempt to cancel an in-progress generation.

        Args:
            generation_id: ID of generation to cancel

        Returns:
            True if cancelled, False if already completed or not found
        """
        raise NotImplementedError("Subclass must implement cancel_generation()")


# Type hints for external use
__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "GenerationStatus",
    "Modality",
    "ContentGenerationInterface",
]
