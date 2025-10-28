# Vividly AI Generation Specifications

**Version:** 1.0 (MVP)
**Last Updated:** October 27, 2025

## Table of Contents

1. [Overview](#overview)
2. [Generation Pipeline](#generation-pipeline)
3. [NLU Service](#nlu-service)
4. [Script Generation](#script-generation)
5. [Audio Generation (TTS)](#audio-generation-tts)
6. [Video Generation](#video-generation)
7. [Prompt Engineering](#prompt-engineering)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Cost Optimization](#cost-optimization)

---

## Overview

The Vividly AI generation pipeline transforms student queries into personalized micro-lessons through four stages:

1. **NLU**: Extract topic from natural language query
2. **Script**: Generate storyboard using RAG + LearnLM
3. **Audio**: Convert script to narration using TTS
4. **Video**: Render animated video from storyboard

### Technology Stack

| Component | Technology | Provider |
|-----------|------------|----------|
| **NLU** | Gemini 1.5 Pro | Google Vertex AI |
| **Embeddings** | text-embedding-gecko@003 | Google Vertex AI |
| **RAG** | Vertex AI Vector Search | Google Cloud |
| **Script Generation** | Gemini 1.5 Pro (LearnLM variant) | Google Vertex AI |
| **TTS** | Neural2 Voices | Google Cloud TTS |
| **Video** | Nano Banana API | External (nano-banana.ai) |

---

## Generation Pipeline

### End-to-End Flow

```
Student Query
     │
     ▼
┌─────────────────────┐
│   NLU Service       │  ← Gemini 1.5 Pro
│   Extract topic_id  │
└──────────┬──────────┘
           │
           ▼
    ┌─────────────┐
    │ Cache Check │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │             │
  Cache         Cache
   HIT          MISS
    │             │
    │             ▼
    │      ┌─────────────────────┐
    │      │ Script Generation   │  ← LearnLM + RAG
    │      │ (Storyboard JSON)   │
    │      └──────────┬──────────┘
    │                 │
    │        ┌────────┴─────────┐
    │        │                  │
    │        ▼                  ▼
    │  ┌──────────┐      ┌──────────┐
    │  │  Audio   │      │  Video   │
    │  │   TTS    │      │  Worker  │
    │  └────┬─────┘      └─────┬────┘
    │       │                  │
    │       ▼                  ▼
    │   [GCS Audio]       [GCS Video]
    │       │                  │
    │       └────────┬─────────┘
    │                │
    └────────────────┤
                     ▼
              Student receives
              "Vivid Learning"
```

### Timing Targets

| Stage | Target Time | P95 Time | Timeout |
|-------|-------------|----------|---------|
| NLU | 2s | 5s | 30s |
| Cache Check | 0.5s | 1s | 5s |
| Script Generation | 5s | 10s | 120s |
| Audio Generation | 3s | 6s | 60s |
| Video Generation | 45s | 90s | 600s |
| **Total (Cache Miss)** | **55s** | **112s** | **815s** |
| **Fast Path (Script+Audio)** | **8s** | **16s** | **190s** |

---

## NLU Service

### Purpose

Extract structured topic information from free-text student queries.

### Input

```json
{
  "query": "Can you explain Newton's third law?",
  "context": {
    "student_grade_level": 10,
    "recent_topics": ["topic_phys_mech_newton_2"],
    "subject_preference": "physics"
  }
}
```

### Output (Successful)

```json
{
  "topic_id": "topic_phys_mech_newton_3",
  "confidence": 0.95,
  "needs_clarification": false
}
```

### Output (Needs Clarification)

```json
{
  "needs_clarification": true,
  "clarification_question": "Which of Newton's laws would you like to learn about?",
  "options": [
    {
      "id": "opt_1",
      "topic_id": "topic_phys_mech_newton_1",
      "title": "First Law (Inertia)",
      "description": "An object at rest stays at rest"
    },
    {
      "id": "opt_2",
      "topic_id": "topic_phys_mech_newton_3",
      "title": "Third Law (Action-Reaction)",
      "description": "Every action has an equal opposite reaction"
    }
  ]
}
```

### Prompt Template

```python
NLU_PROMPT = """You are a topic extraction system for a high school STEM learning platform.

Given a student's query, extract the specific STEM topic they want to learn about.

Available topics are organized hierarchically:
{topic_hierarchy_json}

Student Query: "{query}"

Student Context:
- Grade Level: {grade_level}
- Recent Topics: {recent_topics}
- Subject Preference: {subject_preference}

Instructions:
1. Identify the most specific topic that matches the query
2. If the query is ambiguous, provide 2-3 clarification options
3. Return confidence score (0.0 to 1.0)
4. If confidence < 0.7, request clarification

Output as JSON:
{output_schema}
"""
```

### Implementation

```python
from vertexai.generative_models import GenerativeModel

def extract_topic(query: str, context: dict) -> dict:
    """
    Extract topic from student query using Gemini.
    """
    model = GenerativeModel("gemini-1.5-pro")

    # Load topic hierarchy (cached)
    topic_hierarchy = get_topic_hierarchy()

    # Build prompt
    prompt = NLU_PROMPT.format(
        topic_hierarchy_json=json.dumps(topic_hierarchy, indent=2),
        query=query,
        grade_level=context.get("student_grade_level", "unknown"),
        recent_topics=", ".join(context.get("recent_topics", [])),
        subject_preference=context.get("subject_preference", "any"),
        output_schema=NLU_OUTPUT_SCHEMA
    )

    # Generate with JSON mode
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,  # Low temperature for consistency
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
            "response_mime_type": "application/json"
        }
    )

    result = json.loads(response.text)

    # Validate topic_id exists
    if not result.get("needs_clarification"):
        validate_topic_id(result["topic_id"])

    return result
```

### Error Handling

```python
def extract_topic_with_retry(query: str, context: dict, max_retries: int = 3):
    """Extract topic with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            return extract_topic(query, context)

        except json.JSONDecodeError as e:
            # LLM didn't return valid JSON
            logger.warning(f"NLU JSON parse error (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                # Fallback: use keyword matching
                return fallback_keyword_extraction(query)

        except TopicNotFoundError as e:
            # LLM returned invalid topic_id
            logger.warning(f"Invalid topic_id (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                raise

        except Exception as e:
            # Vertex AI API error
            logger.error(f"NLU service error (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                raise

        # Exponential backoff
        time.sleep(2 ** attempt)
```

---

## Script Generation

### Purpose

Generate a structured storyboard (script) for a 2-4 minute educational video using:
- **RAG**: Retrieve relevant OER content
- **LearnLM**: Generate personalized explanation

### Input

```json
{
  "topic_id": "topic_phys_mech_newton_3",
  "interest_id": "int_basketball",
  "style": "conversational",
  "grade_level": 10
}
```

### Output (Storyboard JSON)

```json
{
  "metadata": {
    "topic_id": "topic_phys_mech_newton_3",
    "topic_title": "Newton's Third Law of Motion",
    "interest": "basketball",
    "duration_seconds": 180,
    "generated_at": "2025-10-27T14:30:00Z"
  },
  "scenes": [
    {
      "scene_number": 1,
      "duration_seconds": 15,
      "narration": "Hey there! Let's talk about Newton's Third Law using something you know well - basketball. Ever wonder what happens when you jump for a rebound?",
      "visual_description": "Animated basketball player preparing to jump on a court",
      "visual_type": "animated_character",
      "background": "basketball_court",
      "text_overlay": "Newton's Third Law: Action & Reaction"
    },
    {
      "scene_number": 2,
      "duration_seconds": 25,
      "narration": "When you push down on the floor with your legs, the floor pushes back up on you with equal force. That's Newton's Third Law: for every action, there's an equal and opposite reaction.",
      "visual_description": "Split screen showing force arrows: player pushing down, floor pushing up",
      "visual_type": "diagram_with_arrows",
      "equations": ["F_player_on_floor = -F_floor_on_player"],
      "annotations": [
        {"type": "arrow", "label": "Action: Push down", "color": "red"},
        {"type": "arrow", "label": "Reaction: Push up", "color": "blue"}
      ]
    },
    {
      "scene_number": 3,
      "duration_seconds": 30,
      "narration": "These forces are called an action-reaction pair. Notice they're equal in strength but opposite in direction. The harder you push down, the harder the floor pushes you up - that's how you jump higher!",
      "visual_description": "Comparison of two players: one pushing harder (jumps higher) vs. one pushing softer (jumps lower)",
      "visual_type": "side_by_side_comparison"
    }
    // ... more scenes ...
  ],
  "key_concepts": [
    "Action-reaction pairs",
    "Equal magnitude forces",
    "Opposite directions",
    "Forces act on different objects"
  ],
  "common_misconceptions_addressed": [
    "Action and reaction do NOT cancel out (they act on different objects)"
  ]
}
```

### RAG Retrieval

```python
def retrieve_oer_content(topic_id: str, num_chunks: int = 10) -> list[dict]:
    """
    Retrieve relevant OER content chunks for topic.
    """
    # Get topic metadata
    topic = get_topic(topic_id)

    # Generate multiple query perspectives
    queries = [
        f"definition and explanation of {topic['title']}",
        f"practical examples of {topic['title']}",
        f"common misconceptions about {topic['title']}"
    ]

    all_chunks = []
    seen_ids = set()

    for query in queries:
        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Query Vector Search
        results = vector_search_endpoint.find_neighbors(
            deployed_index_id="vividly_oer_deployed",
            queries=[query_embedding],
            num_neighbors=num_chunks,
            filter=[
                {"namespace": "topic", "allow_list": [topic_id]},
                {"namespace": "grade_level", "allow_list": [str(topic["grade_level_min"])]}
            ]
        )

        # Fetch metadata and deduplicate
        for neighbor in results[0]:
            if neighbor.id not in seen_ids:
                metadata = fetch_chunk_metadata(neighbor.id)
                all_chunks.append({
                    "chunk_id": neighbor.id,
                    "text": metadata.chunk_text,
                    "similarity": neighbor.distance,
                    "source": metadata.source_id
                })
                seen_ids.add(neighbor.id)

    # Sort by similarity and return top chunks
    all_chunks.sort(key=lambda x: x["similarity"], reverse=True)
    return all_chunks[:num_chunks]
```

### Script Generation Prompt

```python
SCRIPT_GENERATION_PROMPT = """You are an expert STEM educator creating a personalized micro-lesson video script.

**Topic**: {topic_title}
{topic_description}

**Student Interest**: {interest_name}
{interest_description}

**Target Audience**: Grade {grade_level} student (ages {age_range})

**Style**: {style}

**Educational Content (from textbook)**:
{oer_content}

**Your Task**:
Create a 2-3 minute video script that explains this topic using examples and analogies related to {interest_name}.

**Requirements**:
1. Start with a hook that connects to the student's interest
2. Explain the core concept clearly and accurately
3. Use 2-3 concrete examples from {interest_name}
4. Include visual descriptions for each scene (this will be animated)
5. Address common misconceptions
6. Keep language conversational and age-appropriate
7. Total duration: 150-210 seconds

**Output Format**: Return a valid JSON object matching this schema:
{storyboard_schema}

**Important**:
- Each scene narration should be 1-2 sentences (15-30 seconds)
- Visual descriptions must be clear enough for an animator
- Stay scientifically accurate - use the textbook content provided
- Make it engaging but don't oversimplify incorrectly

Generate the storyboard now:
"""
```

### Implementation

```python
def generate_script(
    topic_id: str,
    interest_id: str,
    style: str = "conversational",
    grade_level: int = 10
) -> dict:
    """
    Generate video storyboard using RAG + LearnLM.
    """
    # Retrieve topic and interest
    topic = get_topic(topic_id)
    interest = get_interest(interest_id)

    # RAG: Retrieve relevant OER content
    oer_chunks = retrieve_oer_content(topic_id, num_chunks=5)
    oer_content = "\n\n".join([
        f"[Source {i+1}]: {chunk['text']}"
        for i, chunk in enumerate(oer_chunks)
    ])

    # Build prompt
    prompt = SCRIPT_GENERATION_PROMPT.format(
        topic_title=topic["title"],
        topic_description=topic.get("description", ""),
        interest_name=interest["name"],
        interest_description=interest.get("description", ""),
        grade_level=grade_level,
        age_range=f"{grade_level+13}-{grade_level+14}",
        style=style,
        oer_content=oer_content,
        storyboard_schema=json.dumps(STORYBOARD_SCHEMA, indent=2)
    )

    # Generate with LearnLM
    model = GenerativeModel("gemini-1.5-pro")  # or LearnLM when available

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,  # Creative but controlled
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 4096,
            "response_mime_type": "application/json"
        },
        safety_settings={
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"
        }
    )

    # Parse and validate
    storyboard = json.loads(response.text)
    validate_storyboard(storyboard)

    return storyboard
```

### Quality Checks

```python
def validate_storyboard(storyboard: dict):
    """Validate generated storyboard meets requirements."""

    # Check required fields
    required_fields = ["metadata", "scenes", "key_concepts"]
    for field in required_fields:
        if field not in storyboard:
            raise ValidationError(f"Missing required field: {field}")

    # Check scene count (3-7 scenes for 2-3 min video)
    if not (3 <= len(storyboard["scenes"]) <= 7):
        raise ValidationError(f"Invalid scene count: {len(storyboard['scenes'])}")

    # Check total duration
    total_duration = sum(scene["duration_seconds"] for scene in storyboard["scenes"])
    if not (120 <= total_duration <= 240):
        raise ValidationError(f"Invalid total duration: {total_duration}s")

    # Check each scene
    for i, scene in enumerate(storyboard["scenes"]):
        # Scene must have narration
        if not scene.get("narration"):
            raise ValidationError(f"Scene {i+1} missing narration")

        # Narration length check (rough: 150 words/min speaking rate)
        word_count = len(scene["narration"].split())
        expected_duration = (word_count / 150) * 60  # seconds
        if abs(scene["duration_seconds"] - expected_duration) > 10:
            logger.warning(f"Scene {i+1} duration mismatch: {scene['duration_seconds']}s vs {expected_duration}s")

        # Visual description required
        if not scene.get("visual_description"):
            raise ValidationError(f"Scene {i+1} missing visual_description")

    # Content safety check (keyword-based MVP)
    full_text = " ".join([scene["narration"] for scene in storyboard["scenes"]])
    if contains_inappropriate_content(full_text):
        raise SafetyError("Storyboard contains inappropriate content")

    return True
```

---

## Audio Generation (TTS)

### Purpose

Convert script narration to natural-sounding audio using Google Cloud TTS.

### Input

```json
{
  "storyboard": {...},
  "voice_config": {
    "language_code": "en-US",
    "voice_name": "en-US-Neural2-J",
    "speaking_rate": 0.95,
    "pitch": 0.0
  }
}
```

### Implementation

```python
from google.cloud import texttospeech

def generate_audio(storyboard: dict, voice_config: dict) -> bytes:
    """
    Generate audio file from storyboard narration.
    """
    client = texttospeech.TextToSpeechClient()

    # Combine all narrations with pauses
    ssml_parts = ['<speak>']

    for scene in storyboard["scenes"]:
        # Add narration
        ssml_parts.append(f'<p>{scene["narration"]}</p>')

        # Add pause between scenes (0.5 seconds)
        ssml_parts.append('<break time="500ms"/>')

    ssml_parts.append('</speak>')

    ssml_text = "\n".join(ssml_parts)

    # Configure voice
    voice = texttospeech.VoiceSelectionParams(
        language_code=voice_config["language_code"],
        name=voice_config.get("voice_name", "en-US-Neural2-J")
    )

    # Configure audio
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=voice_config.get("speaking_rate", 0.95),
        pitch=voice_config.get("pitch", 0.0),
        effects_profile_id=["small-bluetooth-speaker-class-device"]
    )

    # Synthesize
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content
```

### Upload to GCS

```python
from google.cloud import storage

def save_audio_to_gcs(audio_bytes: bytes, cache_key: str) -> str:
    """Upload audio to GCS and return public URL."""

    bucket_name = os.getenv("GCS_BUCKET_AUDIO")
    blob_path = f"{cache_key}/audio.mp3"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Upload
    blob.upload_from_string(
        audio_bytes,
        content_type="audio/mpeg"
    )

    # Make publicly readable (or use signed URLs)
    blob.make_public()

    return blob.public_url
```

---

## Video Generation

### Purpose

Render animated video from storyboard using Nano Banana API.

### Nano Banana API Request

```python
import requests

def generate_video(storyboard: dict, audio_url: str) -> str:
    """
    Generate video using Nano Banana API.
    """
    api_key = os.getenv("NANO_BANANA_API_KEY")
    api_url = "https://api.nanobanana.ai/v1/generate"

    # Convert storyboard to Nano Banana format
    scenes = []
    for scene in storyboard["scenes"]:
        scenes.append({
            "duration": scene["duration_seconds"],
            "visual": scene["visual_description"],
            "visual_type": scene.get("visual_type", "animated_character"),
            "background": scene.get("background", "default"),
            "text_overlay": scene.get("text_overlay"),
            "annotations": scene.get("annotations", [])
        })

    payload = {
        "scenes": scenes,
        "audio_url": audio_url,
        "style": "educational_animated",
        "resolution": "1920x1080",
        "fps": 30,
        "metadata": {
            "topic_id": storyboard["metadata"]["topic_id"],
            "client": "vividly"
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Submit job
    response = requests.post(api_url, json=payload, headers=headers)
    response.raise_for_status()

    job_data = response.json()
    job_id = job_data["job_id"]

    # Poll for completion
    video_url = poll_video_completion(job_id, api_key)

    return video_url
```

### Polling Logic

```python
import time

def poll_video_completion(job_id: str, api_key: str, timeout: int = 600) -> str:
    """
    Poll Nano Banana API for video completion.
    """
    status_url = f"https://api.nanobanana.ai/v1/jobs/{job_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(status_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        status = data["status"]

        if status == "completed":
            return data["video_url"]

        elif status == "failed":
            raise VideoGenerationError(f"Video generation failed: {data.get('error')}")

        elif status in ["queued", "processing"]:
            # Wait before next poll (exponential backoff)
            wait_time = min(30, 5 * (1.5 ** (time.time() - start_time) // 30))
            time.sleep(wait_time)

        else:
            raise ValueError(f"Unknown status: {status}")

    raise TimeoutError(f"Video generation timed out after {timeout}s")
```

---

## Prompt Engineering

### Best Practices

1. **Be Specific**: Clearly define output format and constraints
2. **Provide Examples**: Include few-shot examples for consistency
3. **Use JSON Mode**: Request structured output as JSON
4. **Safety First**: Set appropriate safety filters
5. **Iterative Refinement**: Test and refine prompts based on output quality

### Prompt Versioning

```python
PROMPT_VERSIONS = {
    "nlu_v1.0": {
        "model": "gemini-1.5-pro",
        "template": NLU_PROMPT_V1,
        "config": {"temperature": 0.1}
    },
    "script_v1.0": {
        "model": "gemini-1.5-pro",
        "template": SCRIPT_GENERATION_PROMPT_V1,
        "config": {"temperature": 0.7}
    },
    "script_v1.1": {  # Improved version
        "model": "gemini-1.5-pro",
        "template": SCRIPT_GENERATION_PROMPT_V1_1,
        "config": {"temperature": 0.7}
    }
}

# Track which prompt version was used
def generate_script_with_version(topic_id, interest_id, version="script_v1.1"):
    prompt_config = PROMPT_VERSIONS[version]
    # ... use prompt_config
```

---

## Error Handling & Retry Logic

### Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True
)
def generate_script_with_retry(topic_id, interest_id):
    """Generate script with automatic retry on failure."""
    return generate_script(topic_id, interest_id)
```

### Fallback Strategies

```python
def generate_content_with_fallbacks(topic_id, interest_id):
    """
    Try multiple strategies if generation fails.
    """
    try:
        # Primary: Use preferred interest
        return generate_script(topic_id, interest_id)

    except Exception as e:
        logger.warning(f"Failed with interest {interest_id}: {e}")

        # Fallback 1: Try generic interest for this subject
        subject = get_topic_subject(topic_id)
        fallback_interest = get_subject_default_interest(subject)

        try:
            return generate_script(topic_id, fallback_interest)

        except Exception as e:
            logger.error(f"Failed with fallback interest: {e}")

            # Fallback 2: Generate without personalization
            return generate_generic_script(topic_id)
```

---

## Cost Optimization

### Per-Generation Costs (Estimates)

| Component | Cost per Request |
|-----------|------------------|
| NLU (Gemini) | $0.001 |
| Embeddings (RAG) | $0.0001 |
| Vector Search Query | $0.0001 |
| Script Generation (Gemini) | $0.002 |
| TTS (200 chars) | $0.006 |
| Video (Nano Banana) | $0.10 |
| **Total (Cache Miss)** | **~$0.11** |
| **Total (Cache Hit)** | **$0.0001** |

### Caching Impact

- **Target cache hit rate**: 40%
- **Cost with 40% hit rate**: $0.066 per request (40% savings)
- **3,000 requests/month**: ~$200/month vs $330/month

### Optimization Strategies

1. **Aggressive Caching**: Cache by (topic, interest, style)
2. **Batch Processing**: Generate popular content proactively
3. **Model Selection**: Use smaller models for NLU
4. **Rate Limiting**: Prevent abuse/spam requests

---

**Document Control**
- **Owner**: AI/ML Team
- **Last Prompt Update**: October 2025
- **Next Review**: Bi-weekly (during MVP)
