"""
Content Generation Module

This module handles educational content generation with support for multiple modalities
(text, audio, video). It provides a clean interface for generating personalized content
from student queries.

PUBLIC API (use these):
    - GenerationRequest: Input data structure
    - GenerationResult: Output data structure
    - GenerationStatus: Status enum
    - ContentGenerationInterface: Service interface
    - create_content_service: Factory function

PRIVATE (do not import):
    - service.py: Implementation details
    - steps/*: Internal pipeline stages

Usage:
    from modules.content_generation import create_content_service, GenerationRequest

    service = create_content_service(dependencies)
    request = GenerationRequest(...)
    result = await service.generate(request)
"""

from .interface import (
    ContentGenerationInterface,
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    Modality,
)

# Factory function (to be implemented during migration)
def create_content_service(dependencies: dict) -> ContentGenerationInterface:
    """
    Create a content generation service instance.

    This is the recommended way to instantiate the service. It uses
    dependency injection to provide all required external services.

    Args:
        dependencies: Dict containing:
            - vertex_client: Vertex AI client
            - storage_client: GCS client
            - text_to_speech_client: TTS client
            - db_session: Database session
            - (other dependencies as needed)

    Returns:
        ContentGenerationInterface implementation

    Example:
        from modules.content_generation import create_content_service

        service = create_content_service({
            'vertex_client': vertex_ai_client,
            'storage_client': gcs_client,
            'text_to_speech_client': tts_client,
            'db_session': db.session,
        })

        result = await service.generate(request)
    """
    # TODO: Import and instantiate actual service during migration
    # from .service import ContentGenerationService
    # return ContentGenerationService(**dependencies)

    raise NotImplementedError(
        "ContentGenerationService not yet migrated. "
        "Use app.services.content_generation_service.ContentGenerationService "
        "until migration is complete."
    )


__all__ = [
    "ContentGenerationInterface",
    "GenerationRequest",
    "GenerationResult",
    "GenerationStatus",
    "Modality",
    "create_content_service",
]

__version__ = "0.1.0"  # Module version (semantic versioning)
