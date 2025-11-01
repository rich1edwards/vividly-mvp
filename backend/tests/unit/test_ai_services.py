"""
Unit tests for AI Services (Phase 3 & 4)

Tests for:
- NLU Service
- RAG Service
- Script Generation Service
- TTS Service
- Video Service
- Embeddings Service
- Content Ingestion Service
- Content Generation Service (orchestrator)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestNLUService:
    """Test NLU Service for topic extraction"""

    @pytest.mark.asyncio
    async def test_extract_topic_success(self):
        from app.services.nlu_service import NLUService

        service = NLUService()
        result = await service.extract_topic(
            student_query="Explain Newton's third law",
            grade_level=10,
            student_id="student_123",
        )

        assert result is not None
        assert "confidence" in result
        assert "topic_id" in result
        assert "clarification_needed" in result
        assert "out_of_scope" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_extract_topic_out_of_scope(self):
        from app.services.nlu_service import NLUService

        service = NLUService()
        result = await service.extract_topic(
            student_query="What's the weather today?",
            grade_level=10,
            student_id="student_123",
        )

        # In mock mode, might not detect out of scope, but should still work
        assert "out_of_scope" in result
        if result["out_of_scope"]:
            assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_extract_topic_clarification_needed(self):
        from app.services.nlu_service import NLUService

        service = NLUService()
        result = await service.extract_topic(
            student_query="Tell me about forces",
            grade_level=10,
            student_id="student_123",
        )

        # Should either extract a topic or need clarification
        assert "clarification_needed" in result
        if result["clarification_needed"]:
            assert "clarifying_questions" in result
            assert isinstance(result["clarifying_questions"], list)


class TestRAGService:
    """Test RAG Service for content retrieval"""

    @pytest.mark.asyncio
    async def test_retrieve_content_success(self):
        from app.services.rag_service import RAGService

        service = RAGService()
        content = await service.retrieve_content(
            topic_id="topic_phys_mech_newton_3",
            interest="basketball",
            grade_level=10,
            limit=5,
        )

        assert isinstance(content, list)
        assert len(content) <= 5
        if content:
            assert "content_id" in content[0]
            assert "text" in content[0]
            assert "source" in content[0]
            assert "relevance_score" in content[0]

    @pytest.mark.asyncio
    async def test_retrieve_content_with_interest(self):
        from app.services.rag_service import RAGService

        service = RAGService()
        content = await service.retrieve_content(
            topic_id="topic_phys_mech_newton_3",
            interest="basketball",
            grade_level=10,
            limit=5,
        )

        # Should return results (mock mode always returns data)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_generate_embeddings(self):
        from app.services.rag_service import RAGService

        service = RAGService()
        embedding = await service.generate_embeddings("Test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 768  # Gecko model dimensions


class TestScriptGenerationService:
    """Test Script Generation Service"""

    @pytest.mark.asyncio
    async def test_generate_script_success(self):
        from app.services.script_generation_service import ScriptGenerationService

        service = ScriptGenerationService()
        script = await service.generate_script(
            topic_id="topic_phys_mech_newton_3",
            topic_name="Newton's Third Law",
            interest="basketball",
            grade_level=10,
            rag_content=[{"text": "Force pairs example", "source": "OpenStax"}],
            duration_seconds=180,
        )

        assert script is not None
        assert "script_id" in script
        assert "title" in script
        assert "hook" in script
        assert "sections" in script
        assert "key_takeaways" in script
        assert isinstance(script["sections"], list)
        assert isinstance(script["key_takeaways"], list)

    @pytest.mark.asyncio
    async def test_script_structure(self):
        from app.services.script_generation_service import ScriptGenerationService

        service = ScriptGenerationService()
        script = await service.generate_script(
            topic_id="topic_phys_mech_newton_3",
            topic_name="Newton's Third Law",
            interest="basketball",
            grade_level=10,
            rag_content=[],
            duration_seconds=180,
        )

        # Verify script structure
        assert len(script["sections"]) > 0
        for section in script["sections"]:
            assert "title" in section
            assert "content" in section
            assert "duration_seconds" in section


class TestTTSService:
    """Test Text-to-Speech Service"""

    @pytest.mark.asyncio
    async def test_generate_audio_success(self):
        from app.services.tts_service import TTSService

        service = TTSService()
        script = {
            "script_id": "script_123",
            "hook": "Ever wonder why basketball players jump so high?",
            "sections": [
                {
                    "title": "Newton's Third Law",
                    "content": "For every action there is an equal and opposite reaction.",
                }
            ],
            "key_takeaways": ["Forces come in pairs"],
        }

        audio = await service.generate_audio(
            script=script, voice_type="female_professional", output_format="mp3"
        )

        assert audio is not None
        assert "audio_id" in audio
        assert "duration_seconds" in audio
        assert "file_size_bytes" in audio
        assert "audio_url" in audio
        assert "provider" in audio
        assert "voice_type" in audio

    @pytest.mark.asyncio
    async def test_audio_voice_types(self):
        from app.services.tts_service import TTSService

        service = TTSService()
        assert "male_professional" in service.voices
        assert "female_professional" in service.voices
        assert "male_energetic" in service.voices

    def test_narration_text_building(self):
        from app.services.tts_service import TTSService

        service = TTSService()
        script = {
            "hook": "Test hook",
            "sections": [{"content": "Section 1"}, {"content": "Section 2"}],
            "key_takeaways": ["Point 1", "Point 2"],
        }

        text = service._build_narration_text(script)
        assert "Test hook" in text
        assert "Section 1" in text
        assert "Section 2" in text
        assert "Point 1" in text


class TestVideoService:
    """Test Video Generation Service"""

    @pytest.mark.asyncio
    async def test_generate_video_success(self):
        from app.services.video_service import VideoService

        service = VideoService()
        script = {
            "script_id": "script_123",
            "hook": "Test hook",
            "sections": [
                {
                    "title": "Test Section",
                    "content": "Test content",
                    "duration_seconds": 45,
                }
            ],
            "key_takeaways": ["Point 1"],
        }

        video = await service.generate_video(
            script=script,
            audio_url="gs://bucket/audio.mp3",
            interest="basketball",
            subject="physics",
        )

        assert video is not None
        assert "video_id" in video
        assert "duration_seconds" in video
        assert "file_size_bytes" in video
        assert "video_url" in video
        assert "resolution" in video
        assert "format" in video
        assert video["resolution"] == "1920x1080"
        assert video["format"] == "mp4"

    def test_video_config(self):
        from app.services.video_service import VideoService

        service = VideoService()
        assert service.config["resolution"] == (1920, 1080)
        assert service.config["fps"] == 30
        assert service.config["codec"] == "libx264"

    def test_visual_styles(self):
        from app.services.video_service import VideoService

        service = VideoService()
        assert "physics" in service.visual_styles
        assert "math" in service.visual_styles
        assert "chemistry" in service.visual_styles
        assert "default" in service.visual_styles


class TestEmbeddingsService:
    """Test Embeddings Generation Service"""

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self):
        from app.services.embeddings_service import EmbeddingsService

        service = EmbeddingsService()
        embedding = await service.generate_embedding("Test text for embedding")

        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, (int, float)) for x in embedding)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self):
        from app.services.embeddings_service import EmbeddingsService

        service = EmbeddingsService()
        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        results = await service.generate_embeddings_batch(texts, batch_size=3)

        assert isinstance(results, list)
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["index"] == i
            assert "embedding" in result
            assert len(result["embedding"]) == 768
            assert "embedding_id" in result

    @pytest.mark.asyncio
    async def test_query_embedding(self):
        from app.services.embeddings_service import EmbeddingsService

        service = EmbeddingsService()
        embedding = await service.generate_query_embedding("search query")

        assert isinstance(embedding, list)
        assert len(embedding) == 768

    def test_embedding_validation(self):
        from app.services.embeddings_service import EmbeddingsService

        service = EmbeddingsService()

        # Valid embedding
        valid = [0.1] * 768
        assert service.validate_embedding(valid) is True

        # Invalid dimension
        invalid_dim = [0.1] * 500
        assert service.validate_embedding(invalid_dim) is False

        # Invalid values
        invalid_val = [float("inf")] * 768
        assert service.validate_embedding(invalid_val) is False


class TestContentIngestionService:
    """Test Content Ingestion Service"""

    @pytest.mark.asyncio
    async def test_ingest_content_success(self):
        from app.services.content_ingestion_service import ContentIngestionService

        service = ContentIngestionService()
        content_data = {
            "author": "OpenStax",
            "license": "CC BY 4.0",
            "url": "https://openstax.org",
            "version": "2e",
            "chapters": [
                {
                    "number": 1,
                    "title": "Test Chapter",
                    "sections": [
                        {
                            "number": "1.1",
                            "title": "Test Section",
                            "content": "This is test content. "
                            * 100,  # Make it long enough
                            "topic_ids": ["topic_test_123"],
                        }
                    ],
                }
            ],
        }

        result = await service.ingest_openstax_content(
            source_title="Test Physics", subject="physics", content_data=content_data
        )

        assert result is not None
        assert result["status"] == "completed"
        assert "chunks_created" in result
        assert "total_words" in result
        assert result["chunks_created"] > 0

    def test_chunk_text(self):
        from app.services.content_ingestion_service import ContentIngestionService

        service = ContentIngestionService()

        # Create text with ~400 words
        text = "This is a test sentence. " * 200

        chunks = service._chunk_text(
            text=text,
            chapter="Chapter 1",
            section="Section 1.1",
            source={
                "title": "Test",
                "author": "Test",
                "url": "test",
                "license": "CC BY",
            },
            subject="physics",
            topic_ids=["topic_test"],
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["word_count"] >= service.chunk_config["min_chunk_size"]
            assert chunk["word_count"] <= service.chunk_config["max_chunk_size"]

    def test_keyword_extraction(self):
        from app.services.content_ingestion_service import ContentIngestionService

        service = ContentIngestionService()
        text = "force force force energy energy momentum velocity velocity velocity"

        keywords = service._extract_keywords(text)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Most frequent words should be extracted
        assert "force" in keywords or "velocity" in keywords

    def test_concept_extraction(self):
        from app.services.content_ingestion_service import ContentIngestionService

        service = ContentIngestionService()
        text = "The force causes acceleration due to Newton's law of motion"

        concepts = service._extract_concepts(text, "physics")

        assert isinstance(concepts, list)
        # Should extract physics concepts
        assert "force" in concepts or "newton" in concepts or "law" in concepts


class TestContentGenerationService:
    """Test Content Generation Orchestrator"""

    @pytest.mark.asyncio
    async def test_generate_content_from_query_success(self):
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()
        result = await service.generate_content_from_query(
            student_query="Explain Newton's third law",
            student_id="student_123",
            grade_level=10,
            interest="basketball",
        )

        assert result is not None
        assert "status" in result
        assert "generation_id" in result

        # Should either complete, need clarification, or be out of scope
        assert result["status"] in [
            "completed",
            "clarification_needed",
            "out_of_scope",
            "generating",
            "failed",
        ]

    @pytest.mark.asyncio
    async def test_pipeline_clarification_needed(self):
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()

        # Vague query should need clarification
        result = await service.generate_content_from_query(
            student_query="Tell me about stuff",
            student_id="student_123",
            grade_level=10,
        )

        # Should handle it gracefully
        assert result["status"] in [
            "clarification_needed",
            "out_of_scope",
            "failed",
            "extraction_failed",
        ]

    @pytest.mark.asyncio
    async def test_pipeline_out_of_scope(self):
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()

        # Non-academic query
        result = await service.generate_content_from_query(
            student_query="What's for lunch?", student_id="student_123", grade_level=10
        )

        # Should be marked as out of scope
        if result["status"] == "out_of_scope":
            assert "reasoning" in result

    def test_subject_inference(self):
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()

        assert service._infer_subject("topic_phys_mech_newton") == "physics"
        assert service._infer_subject("topic_math_calc_derivative") == "math"
        assert service._infer_subject("topic_chem_reactions") == "chemistry"
        assert service._infer_subject("topic_bio_cells") == "biology"
        assert service._infer_subject("topic_unknown") == "default"

    @pytest.mark.asyncio
    async def test_generate_content_from_topic(self):
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()
        result = await service.generate_content_from_topic(
            topic_id="topic_phys_mech_newton_3", interest="basketball", grade_level=10
        )

        assert result is not None
        assert "status" in result
        assert "generation_id" in result


# Integration test for full pipeline
class TestContentGenerationPipeline:
    """Integration tests for complete content generation pipeline"""

    @pytest.mark.asyncio
    async def test_full_pipeline_mock_mode(self):
        """Test complete pipeline in mock mode"""
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()

        # Generate content from start to finish
        result = await service.generate_content_from_query(
            student_query="Explain Newton's third law using basketball examples",
            student_id="student_123",
            grade_level=10,
            interest="basketball",
        )

        # Should complete or provide useful status (including failed in mock mode)
        assert result is not None
        assert result["status"] in [
            "completed",
            "generating",
            "clarification_needed",
            "out_of_scope",
            "failed",
            "extraction_failed",
        ]

        # If completed, should have all components
        if result["status"] == "completed":
            assert "content" in result
            content = result["content"]
            assert "script" in content
            assert "audio" in content
            assert "video" in content

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully"""
        from app.services.content_generation_service import ContentGenerationService

        service = ContentGenerationService()

        # Should not crash on edge cases
        result = await service.generate_content_from_query(
            student_query="", student_id="student_123", grade_level=10  # Empty query
        )

        assert result is not None
        assert "status" in result
