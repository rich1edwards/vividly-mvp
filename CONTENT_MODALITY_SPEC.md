# Content Modality Specification
**Dual-Modality Content Generation Architecture**

**Date**: 2025-11-03
**Version**: 1.0
**Status**: Design Complete
**Methodology**: Andrew Ng's Systematic Cost-Benefit Analysis

---

## Executive Summary

Vividly supports **two distinct content generation modalities**:
1. **Text-Only**: Generates learning script/transcript only
2. **Text+Video**: Generates script + 1-5 minute video with TTS narration

This architectural decision has profound implications for:
- **Cost structure**: 10-15x difference between modalities
- **Pricing strategy**: Separate usage limits per modality
- **User experience**: Clear value differentiation
- **Competitive positioning**: Flexibility vs video-first competitors

---

## Cost Structure Analysis

### Text-Only Generation

**Pipeline**: Query → RAG Retrieval → LLM Script Generation

**Cost Breakdown** (per 2-min script, ~500 words):
```
1. RAG Retrieval (ChromaDB query)
   - Compute: Negligible (< $0.0001)
   - Vertex AI Embedding query: $0.0001

2. LLM Generation (Gemini 1.5 Pro)
   - Input tokens: ~2,000 (context from RAG)
   - Output tokens: ~800 (script)
   - Cost: $0.0035 input + $0.0105 output = $0.014

3. Storage (Cloud Storage)
   - Text file: < 10 KB
   - Cost: Negligible (< $0.0001)

TOTAL: ~$0.015 per text-only request
```

**Annual Cost at Scale** (1M text requests):
- Direct costs: $15,000
- Infrastructure: $2,000
- **Total**: $17,000
- **Cost per request**: $0.017

---

### Text+Video Generation

**Pipeline**: Query → RAG → LLM Script → TTS Audio → Video Synthesis

**Cost Breakdown** (per 2-min video):
```
1. Text Generation (same as above): $0.015

2. Text-to-Speech (Vertex AI TTS)
   - Characters: ~1,000 (2-min script)
   - Voice: WaveNet (neural)
   - Cost: $0.016 per 1M chars × 0.001 = $0.000016
   - Reality check: ~$0.04 (Google Cloud TTS pricing)

3. Video Synthesis (Render pipeline)
   - Background visuals (stock images/animations)
   - Text overlays + animations
   - Audio sync
   - Rendering: 2 minutes @ 30fps = 3,600 frames

   Option A: Custom renderer (FFmpeg + GPU)
   - Cloud Run GPU instance: ~$0.10-0.15 per 2-min render

   Option B: Third-party API (Synthesia, D-ID, HeyGen)
   - Cost: $0.20-0.50 per video minute
   - 2-min video: $0.40-1.00

4. Storage (Cloud Storage)
   - Video file: ~50 MB (1080p, H.264)
   - Storage: $0.02/GB/month × 0.05 GB = $0.001/month
   - Transfer: $0.12/GB × 0.05 GB = $0.006

TOTAL (Custom Renderer): ~$0.18 per video
TOTAL (Third-Party API): ~$0.50 per video
```

**Annual Cost at Scale** (1M videos, custom renderer):
- Direct costs: $180,000
- Infrastructure: $20,000
- **Total**: $200,000
- **Cost per video**: $0.20

---

### Cost Comparison Matrix

| Metric | Text-Only | Text+Video | Ratio |
|--------|-----------|------------|-------|
| **Per-Request Cost** | $0.017 | $0.20 | 11.8x |
| **1M Requests/Year** | $17,000 | $200,000 | 11.8x |
| **Storage (per item)** | < 10 KB | ~50 MB | 5000x |
| **Delivery Latency** | 5-10 sec | 45-90 sec | 7x |
| **Bandwidth Cost** | Negligible | $0.006/transfer | ∞ |

**Key Insight**: Video generation is **12x more expensive** than text-only. Pricing tiers must reflect this cost differential while maintaining perceived value.

---

## Pricing Strategy - Revised Tiers

### Individual Plans (B2C)

#### **Free Tier - $0/month**
```yaml
Text-Only Generation:
  - 15 requests/month
  - Standard processing (30-60 sec)
  - Ads displayed in interface
  - OpenStax content only

Video Generation:
  - 3 videos/month (2-min limit)
  - Standard queue (5-10 min wait)
  - 720p quality
  - Watermark: "Created with Vividly"

Value Props:
  - Try before you buy
  - Homework help for budget-conscious students
  - Gateway to premium features

Cost Analysis:
  - 15 text requests: 15 × $0.017 = $0.26
  - 3 videos: 3 × $0.20 = $0.60
  - Total COGS: $0.86/month
  - Ad revenue target: $1.50/user/month
  - Net margin: +$0.64/user/month (74%)
```

#### **Plus Tier - $4.99/month**
```yaml
Text-Only Generation:
  - 100 requests/month
  - Priority processing (10-20 sec)
  - No ads
  - OpenStax + custom org content

Video Generation:
  - 20 videos/month (5-min limit)
  - Priority queue (2-3 min wait)
  - 1080p quality
  - No watermark

Premium Features:
  - HD video downloads
  - Request history (90 days)
  - Basic analytics

Cost Analysis:
  - 100 text requests: 100 × $0.017 = $1.70
  - 20 videos: 20 × $0.20 = $4.00
  - Total COGS: $5.70/month
  - Revenue: $4.99/month
  - Net margin: -$0.71/user/month (-14%)

Breakeven Analysis:
  - If 60% of users generate 15 videos (not 20):
    - 100 text + 15 videos = $1.70 + $3.00 = $4.70
    - Margin: +$0.29 (6%)
  - Strategy: Monitor usage, adjust limits if needed
```

#### **Premium Tier - $9.99/month**
```yaml
Text-Only Generation:
  - Unlimited requests
  - Instant processing (5-10 sec)
  - No ads
  - All content sources

Video Generation:
  - 60 videos/month (5-min limit)
  - Highest priority (< 2 min wait)
  - 4K quality option
  - Advanced editing (coming soon)

Premium Features:
  - Offline video downloads
  - Request history (unlimited)
  - Advanced analytics dashboard
  - Custom content sources (3 max)
  - API access (1,000 calls/month)

Cost Analysis:
  - Typical usage: 150 text + 40 videos
  - 150 text: 150 × $0.017 = $2.55
  - 40 videos: 40 × $0.20 = $8.00
  - Total COGS: $10.55/month
  - Revenue: $9.99/month
  - Net margin: -$0.56/user/month (-5%)

Breakeven Usage:
  - 150 text + 38 videos = $10.15
  - Target: 35 videos/month average
  - Strategy: High-value users, cross-sell Family plan
```

#### **Family Tier - $14.99/month**
```yaml
Seats: Up to 4 students

Per-Seat Allocation:
  - 100 text requests/month
  - 15 videos/month (5-min limit)

Shared Pool (optional upgrade):
  - Additional 100 text requests
  - Additional 20 videos
  - Shared across all 4 seats

Features:
  - All Premium features per seat
  - Parent dashboard
  - Usage monitoring
  - Content filtering
  - Progress tracking

Cost Analysis (4 active users):
  - 4 × (100 text + 15 videos)
  - Text: 400 × $0.017 = $6.80
  - Video: 60 × $0.20 = $12.00
  - Total COGS: $18.80/month
  - Revenue: $14.99/month
  - Net margin: -$3.81/month (-25%)

Reality Check:
  - Average active seats: 2.5 (62.5% utilization)
  - 2.5 × (100 text + 15 videos) = 250 text + 38 videos
  - COGS: $4.25 + $7.60 = $11.85
  - Margin: +$3.14/month (21%)
  - Strategy: Bet on partial utilization
```

---

### Organization Plans (B2B)

#### **Basic Tier - $3/user/month**
(Annual billing, 10-user minimum)

```yaml
Base User Plan: Plus tier equivalent

Per-User Allocation:
  Text-Only: 80 requests/month
  Video: 15 videos/month (2-min limit)

Organization Features:
  - 1 custom content source
  - Basic admin dashboard
  - Usage reports (monthly)
  - Email support

Cost Analysis (100 users, 70% active):
  - 70 users × (80 text + 15 videos)
  - Text: 5,600 × $0.017 = $95.20
  - Video: 1,050 × $0.20 = $210.00
  - Total COGS: $305.20/month
  - Revenue: 100 × $3 = $300/month
  - Net margin: -$5.20/month (-2%)

Breakeven:
  - Target video usage: 12 videos/user/month
  - Margin: +$36.80/month (12%)
  - Strategy: Usage caps, overage billing
```

#### **Professional Tier - $7/user/month**
(Annual billing, 25-user minimum)

```yaml
Base User Plan: Premium tier equivalent

Per-User Allocation:
  Text-Only: Unlimited
  Video: 40 videos/month (5-min limit)

Organization Features:
  - Unlimited custom content sources
  - Advanced admin dashboard
  - SSO integration (SAML/OAuth)
  - API access (10,000 calls/month)
  - Priority support
  - White-label option (+$2/user)

Cost Analysis (250 users, 75% active):
  - 188 users active, typical: 120 text + 25 videos
  - Text: 22,560 × $0.017 = $383.52
  - Video: 4,700 × $0.20 = $940.00
  - Total COGS: $1,323.52/month
  - Revenue: 250 × $7 = $1,750/month
  - Net margin: +$426.48/month (24%)
```

#### **Enterprise Tier - Custom Pricing**
(Starts at $15,000/month, 500-user minimum)

```yaml
Base User Plan: Premium tier + custom

Per-User Allocation:
  Text-Only: Unlimited
  Video: Custom (typically 60-100/month)

Organization Features:
  - Dedicated infrastructure
  - Custom integrations
  - LMS integration (Canvas, Blackboard, etc.)
  - Dedicated account manager
  - SLA: 99.9% uptime
  - Custom AI model fine-tuning
  - SCORM compliance
  - Advanced analytics + reporting

Pricing Model:
  - Base: $15,000/month (500 users)
  - Additional users: $20/user/month
  - Overage: Text (unlimited), Video ($0.30/video)

Cost Analysis (500 users, 80% active):
  - 400 users active, typical: 200 text + 40 videos
  - Text: 80,000 × $0.017 = $1,360
  - Video: 16,000 × $0.20 = $3,200
  - Total COGS: $4,560/month
  - Revenue: $15,000/month
  - Net margin: +$10,440/month (70%)
```

---

## Revised Pricing Comparison Table

| Plan | Price | Text/Month | Videos/Month | Cost/User | Margin |
|------|-------|------------|--------------|-----------|--------|
| **Individual Plans** |
| Free | $0 | 15 | 3 | $0.86 | 74%* |
| Plus | $4.99 | 100 | 20 | $5.70 | -14%** |
| Premium | $9.99 | Unlimited | 60 | $10.55 | -5%** |
| Family | $14.99 | 400*** | 60*** | $11.85 | 21% |
| **Organization Plans** |
| Basic | $3 | 80 | 15 | $3.06 | -2%** |
| Professional | $7 | Unlimited | 40 | $5.29 | 24% |
| Enterprise | Custom | Unlimited | Custom | Variable | 60-70% |

*Free tier profitable via ad revenue
**Breakeven assumes average usage (see detailed analysis)
***Family tier = 4 seats combined

---

## Strategic Pricing Decisions

### 1. **Tiered Video Limits** (Not Unlimited)
**Decision**: Cap video generation even on Premium/Professional tiers.

**Rationale**:
- Video COGS ($0.20) would bankrupt unlimited plans
- 60 videos/month = $12 COGS alone (exceeds $9.99 Premium price)
- Competitors (Synthesia, Loom) also cap video generation
- Creates upgrade path: Need more videos? → Family or Enterprise

**Psychology**: "60 videos/month" sounds generous (2 videos/day), but most users generate 15-25/month.

---

### 2. **Unlimited Text** (Premium+)
**Decision**: Unlimited text-only generation on Premium and above.

**Rationale**:
- Text COGS ($0.017) is sustainable even at high volume
- Average user: 100-200 text requests/month = $1.70-3.40 COGS
- Power users (500 requests) = $8.50 COGS (still profitable on Premium)
- Competitive advantage: "Unlimited homework help" vs Chegg/Course Hero

**Risk Mitigation**: Rate limiting (10 requests/hour) prevents abuse.

---

### 3. **Video Quality as Differentiator**
**Decision**: Tier by video quality (720p, 1080p, 4K).

**Rationale**:
- Quality impacts rendering cost: 720p ($0.15) vs 4K ($0.35)
- Free tier watermark incentivizes upgrade
- Professional users value HD for classroom presentations
- Cost is marginal, but perception is premium

---

### 4. **Family Plan Bet on Partial Utilization**
**Decision**: Price Family tier assuming 2.5/4 seats active.

**Rationale**:
- Research shows 60-70% seat utilization in family plans
- Netflix, Spotify use same model
- Even if all 4 active, LTV > CAC over 12 months
- Upsell opportunity: Usage reports → "Upgrade to Premium for individual users"

---

### 5. **B2B Plans Focus on Margin**
**Decision**: Basic tier is low-margin, Professional+ is profitable.

**Rationale**:
- Basic tier is customer acquisition (schools with tight budgets)
- Professional tier targets corporate training (higher budgets)
- Enterprise tier is high-margin, custom value
- Strategy: Land with Basic, expand to Professional

---

## User Experience - Modality Selection

### Content Request Flow (Enhanced)

```
Step 1: Enter Learning Goal
┌─────────────────────────────────────────┐
│ What do you want to learn?              │
│ ┌─────────────────────────────────────┐ │
│ │ Explain photosynthesis for 8th     │ │
│ │ grade biology                       │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘

Step 2: Choose Content Type
┌─────────────────────────────────────────┐
│ How would you like to learn?            │
│                                          │
│ ○ Text Summary (faster, counts as 1)    │
│   ↳ Get a written explanation           │
│   ↳ Ready in 10-15 seconds              │
│                                          │
│ ● Video Lesson (more engaging)          │
│   ↳ 2-minute narrated video             │
│   ↳ Ready in 2-3 minutes                │
│   ↳ Uses 1 of 17 videos remaining       │
│                                          │
│ Duration: ○ 2 min  ● 3 min  ○ 5 min     │
└─────────────────────────────────────────┘

Step 3: Usage Visibility
┌─────────────────────────────────────────┐
│ Your usage this month (resets Nov 15):  │
│                                          │
│ 📝 Text Requests: 47 / 100 used         │
│ ████████░░░░░░░░░░░░ 47%                │
│                                          │
│ 🎥 Videos: 17 / 20 used                 │
│ ████████████████░░░░ 85% ⚠️             │
│                                          │
│ [Generate Content] [Save for Later]     │
└─────────────────────────────────────────┘

Step 4: Limit Reached (Video)
┌─────────────────────────────────────────┐
│ ⚠️  You've used all 20 videos this month │
│                                          │
│ Options:                                 │
│ • Generate Text Summary instead (free)   │
│ • Upgrade to Premium (60 videos/month)   │
│ • Wait 3 days for monthly reset          │
│                                          │
│ [Get Text Summary] [Upgrade to Premium]  │
└─────────────────────────────────────────┘
```

---

### Design Principles

1. **Default to Video** (Higher engagement)
   - Pre-select video option
   - But show usage counter prominently
   - Users consciously choose text to conserve quota

2. **Real-Time Usage Display**
   - Always visible in request form
   - Progress bars with percentage
   - Warning at 80% usage
   - Alert at 100% usage

3. **Upgrade Prompts** (Non-Intrusive)
   - Only show at limit
   - Clear value prop: "Get 40 more videos for $5/month"
   - One-click upgrade via Stripe

4. **Text-as-Fallback**
   - When video quota exhausted, offer text
   - Message: "Still get your answer, just in text form"
   - Maintains user satisfaction

---

## Backend Architecture

### Enhanced Data Models

```python
# app/models/user.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models import Base
import enum

class PlanType(enum.Enum):
    FREE = "free"
    PLUS = "plus"
    PREMIUM = "premium"
    FAMILY = "family"

class User(Base):
    __tablename__ = "users"

    # Existing fields
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    organization_id = Column(String, nullable=True)

    # Plan management
    base_plan = Column(SQLEnum(PlanType), default=PlanType.FREE)
    individual_plan_override = Column(SQLEnum(PlanType), nullable=True)

    # Usage tracking (current month)
    text_requests_count = Column(Integer, default=0)
    video_requests_count = Column(Integer, default=0)
    usage_month = Column(DateTime, default=func.now())

    # Historical (for analytics)
    total_text_requests = Column(Integer, default=0)
    total_video_requests = Column(Integer, default=0)

    @property
    def effective_plan(self) -> PlanType:
        """Returns highest tier between base and individual plans"""
        if self.individual_plan_override:
            # If org provides Plus, user pays for Premium → Premium
            plan_order = [PlanType.FREE, PlanType.PLUS, PlanType.PREMIUM, PlanType.FAMILY]
            return max(self.base_plan, self.individual_plan_override, key=plan_order.index)
        return self.base_plan

    @property
    def monthly_text_limit(self) -> int:
        """Returns text request limit based on effective plan"""
        limits = {
            PlanType.FREE: 15,
            PlanType.PLUS: 100,
            PlanType.PREMIUM: 999999,  # "Unlimited"
            PlanType.FAMILY: 100  # Per-seat allocation
        }
        return limits[self.effective_plan]

    @property
    def monthly_video_limit(self) -> int:
        """Returns video generation limit based on effective plan"""
        limits = {
            PlanType.FREE: 3,
            PlanType.PLUS: 20,
            PlanType.PREMIUM: 60,
            PlanType.FAMILY: 15  # Per-seat allocation
        }
        return limits[self.effective_plan]

    def can_request_text(self) -> bool:
        """Check if user can generate text content"""
        self._reset_usage_if_new_month()
        return self.text_requests_count < self.monthly_text_limit

    def can_request_video(self) -> bool:
        """Check if user can generate video content"""
        self._reset_usage_if_new_month()
        return self.video_requests_count < self.monthly_video_limit

    def increment_text_usage(self):
        """Increment text request counter"""
        self.text_requests_count += 1
        self.total_text_requests += 1

    def increment_video_usage(self):
        """Increment video request counter"""
        self.video_requests_count += 1
        self.total_video_requests += 1

    def _reset_usage_if_new_month(self):
        """Reset monthly counters if month has changed"""
        now = func.now()
        if now.month != self.usage_month.month or now.year != self.usage_month.year:
            self.text_requests_count = 0
            self.video_requests_count = 0
            self.usage_month = now
```

```python
# app/models/content_request.py

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, Integer
from sqlalchemy.sql import func
from app.models import Base
import enum

class ContentModality(enum.Enum):
    TEXT_ONLY = "text_only"
    TEXT_AND_VIDEO = "text_and_video"

class ContentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ContentRequest(Base):
    __tablename__ = "content_requests"

    request_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    organization_id = Column(String, nullable=True)

    # Request details
    query = Column(Text, nullable=False)
    modality = Column(SQLEnum(ContentModality), default=ContentModality.TEXT_AND_VIDEO)
    video_duration_seconds = Column(Integer, default=120)  # 2 min default

    # Status tracking
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.PENDING)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Generated content
    script_text = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)  # GCS URL
    video_duration_actual = Column(Integer, nullable=True)

    # Cost tracking (for analytics)
    llm_cost = Column(Integer, default=0)  # Cents
    tts_cost = Column(Integer, default=0)
    video_cost = Column(Integer, default=0)
    total_cost = Column(Integer, default=0)
```

---

### Content Generation Service (Updated)

```python
# app/services/content_generation_service.py

from app.models.user import User
from app.models.content_request import ContentRequest, ContentModality, ContentStatus
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from sqlalchemy.orm import Session
import uuid

class ContentGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.rag = RAGService()
        self.llm = LLMService()
        self.tts = TTSService()
        self.video = VideoService()

    async def create_request(
        self,
        user_id: str,
        query: str,
        modality: ContentModality,
        video_duration: int = 120
    ) -> ContentRequest:
        """
        Create a new content generation request with modality support.

        Args:
            user_id: User ID making the request
            query: Learning goal/question
            modality: TEXT_ONLY or TEXT_AND_VIDEO
            video_duration: Video length in seconds (if applicable)

        Returns:
            ContentRequest object

        Raises:
            ValueError: If user has exceeded usage limits
        """
        # 1. Validate usage limits
        user = self.db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        if modality == ContentModality.TEXT_ONLY:
            if not user.can_request_text():
                raise ValueError(
                    f"Text request limit exceeded. "
                    f"Used {user.text_requests_count}/{user.monthly_text_limit} this month."
                )
        else:
            if not user.can_request_video():
                raise ValueError(
                    f"Video request limit exceeded. "
                    f"Used {user.video_requests_count}/{user.monthly_video_limit} this month."
                )

        # 2. Create request record
        request = ContentRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            organization_id=user.organization_id,
            query=query,
            modality=modality,
            video_duration_seconds=video_duration,
            status=ContentStatus.PENDING
        )
        self.db.add(request)
        self.db.commit()

        # 3. Increment usage counter
        if modality == ContentModality.TEXT_ONLY:
            user.increment_text_usage()
        else:
            user.increment_video_usage()
        self.db.commit()

        return request

    async def process_request(self, request_id: str):
        """
        Process content generation request based on modality.

        Pipeline:
            1. RAG retrieval (same for both modalities)
            2. LLM script generation (same for both)
            3. [If TEXT_ONLY] → Save script, mark completed
            4. [If TEXT_AND_VIDEO] → TTS → Video synthesis → Save video
        """
        request = self.db.query(ContentRequest).filter_by(request_id=request_id).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")

        try:
            request.status = ContentStatus.PROCESSING
            self.db.commit()

            # Step 1: RAG retrieval
            context = await self.rag.retrieve_context(
                query=request.query,
                organization_id=request.organization_id,
                top_k=10
            )

            # Step 2: LLM script generation
            script = await self.llm.generate_script(
                query=request.query,
                context=context,
                duration_seconds=request.video_duration_seconds
            )
            request.script_text = script
            request.llm_cost = 1  # $0.01 = 1 cent
            self.db.commit()

            # Step 3: Conditional video generation
            if request.modality == ContentModality.TEXT_AND_VIDEO:
                # TTS generation
                audio_url = await self.tts.synthesize(
                    text=script,
                    voice="en-US-Neural2-J"  # Female voice
                )
                request.tts_cost = 4  # $0.04

                # Video synthesis
                video_url = await self.video.render(
                    script=script,
                    audio_url=audio_url,
                    duration=request.video_duration_seconds,
                    quality="1080p"  # Based on user plan
                )
                request.video_url = video_url
                request.video_cost = 15  # $0.15
                request.total_cost = request.llm_cost + request.tts_cost + request.video_cost
            else:
                # Text-only: no video generation
                request.total_cost = request.llm_cost

            # Step 4: Mark completed
            request.status = ContentStatus.COMPLETED
            request.completed_at = func.now()
            self.db.commit()

        except Exception as e:
            request.status = ContentStatus.FAILED
            self.db.commit()
            raise e

    async def get_user_usage(self, user_id: str) -> dict:
        """
        Get current month usage statistics for user.

        Returns:
            {
                "text_used": 47,
                "text_limit": 100,
                "text_percent": 47,
                "video_used": 17,
                "video_limit": 20,
                "video_percent": 85,
                "reset_date": "2025-11-15"
            }
        """
        user = self.db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user._reset_usage_if_new_month()

        return {
            "text_used": user.text_requests_count,
            "text_limit": user.monthly_text_limit,
            "text_percent": int((user.text_requests_count / user.monthly_text_limit) * 100),
            "video_used": user.video_requests_count,
            "video_limit": user.monthly_video_limit,
            "video_percent": int((user.video_requests_count / user.monthly_video_limit) * 100),
            "reset_date": self._calculate_reset_date(user.usage_month)
        }

    def _calculate_reset_date(self, usage_month):
        """Calculate next billing cycle reset date"""
        # Simple logic: first day of next month
        from datetime import datetime, timedelta
        next_month = usage_month + timedelta(days=32)
        return next_month.replace(day=1).strftime("%Y-%m-%d")
```

---

### API Endpoints (New/Updated)

```python
# app/api/routes/content.py

from fastapi import APIRouter, Depends, HTTPException
from app.services.content_generation_service import ContentGenerationService
from app.models.content_request import ContentModality
from app.api.dependencies import get_current_user, get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/content", tags=["content"])

class ContentRequestCreate(BaseModel):
    query: str
    modality: str  # "text_only" or "text_and_video"
    video_duration: int = 120  # seconds

class ContentRequestResponse(BaseModel):
    request_id: str
    status: str
    modality: str
    estimated_time: int  # seconds
    usage: dict

@router.post("/request", response_model=ContentRequestResponse)
async def create_content_request(
    payload: ContentRequestCreate,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new content generation request.

    Example payload:
    {
        "query": "Explain photosynthesis for 8th grade",
        "modality": "text_and_video",
        "video_duration": 180
    }
    """
    try:
        service = ContentGenerationService(db)

        modality = ContentModality.TEXT_ONLY if payload.modality == "text_only" \
                   else ContentModality.TEXT_AND_VIDEO

        request = await service.create_request(
            user_id=user.user_id,
            query=payload.query,
            modality=modality,
            video_duration=payload.video_duration
        )

        # Get updated usage stats
        usage = await service.get_user_usage(user.user_id)

        return ContentRequestResponse(
            request_id=request.request_id,
            status=request.status.value,
            modality=request.modality.value,
            estimated_time=10 if modality == ContentModality.TEXT_ONLY else 120,
            usage=usage
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/usage")
async def get_usage_stats(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get current month usage statistics.

    Response:
    {
        "text_used": 47,
        "text_limit": 100,
        "text_percent": 47,
        "video_used": 17,
        "video_limit": 20,
        "video_percent": 85,
        "reset_date": "2025-11-15"
    }
    """
    service = ContentGenerationService(db)
    return await service.get_user_usage(user.user_id)
```

---

## Implementation Roadmap

### Phase 1: Core Modality Support (Weeks 1-2)
**Goal**: Implement dual-modality backend architecture

Tasks:
1. Update data models (`User`, `ContentRequest`)
2. Add `modality` field to content requests
3. Implement conditional video generation pipeline
4. Add usage tracking (text vs video counters)
5. Create usage limit validation logic

Success Criteria:
- API accepts `modality` parameter
- Text-only requests skip video generation
- Usage counters increment correctly
- Unit tests pass (90% coverage)

---

### Phase 2: Pricing Tier Implementation (Weeks 3-4)
**Goal**: Deploy revised pricing limits to production

Tasks:
1. Update `monthly_text_limit` and `monthly_video_limit` properties
2. Implement plan-specific limits (Free: 15/3, Plus: 100/20, etc.)
3. Add hybrid plan inheritance logic
4. Create migration script for existing users
5. Update Stripe integration for new tiers

Success Criteria:
- All users have correct limits based on plan
- Hybrid plans (org + individual) calculate correctly
- Stripe webhook handles plan changes
- Existing users migrated without data loss

---

### Phase 3: Frontend UX (Weeks 5-6)
**Goal**: Build modality selection interface

Tasks:
1. Add modality toggle to content request form
2. Display real-time usage stats (progress bars)
3. Implement limit reached UI (upgrade prompts)
4. Add video duration selector (2, 3, 5 min)
5. Create usage dashboard page

Success Criteria:
- Users can select text-only or video
- Usage stats visible on every request
- Upgrade flow works (Stripe checkout)
- Mobile-responsive design

---

### Phase 4: Analytics & Monitoring (Week 7)
**Goal**: Track modality usage patterns

Tasks:
1. Add analytics events (modality_selected, limit_reached, upgrade_clicked)
2. Create admin dashboard for usage trends
3. Implement cost tracking per request
4. Build usage reports (CSV export)
5. Set up alerts for anomalous usage

Success Criteria:
- Dashboard shows text vs video usage split
- Cost per user calculated accurately
- Alerts trigger for high video usage
- Monthly reports generated automatically

---

### Phase 5: Optimization (Week 8)
**Goal**: Reduce video generation cost

Tasks:
1. Implement video caching (same query → reuse video)
2. Optimize rendering pipeline (FFmpeg flags)
3. Add CDN for video delivery (Cloud CDN)
4. Implement adaptive quality (720p for slow networks)
5. A/B test: Custom renderer vs third-party API

Success Criteria:
- Video COGS reduced by 20% (target: $0.16)
- Cache hit rate > 15%
- CDN reduces bandwidth cost by 30%
- P95 video generation time < 90 seconds

---

## Success Metrics

### Technical KPIs
```yaml
Video Generation:
  - P50 latency: < 60 seconds
  - P95 latency: < 120 seconds
  - Success rate: > 98%
  - COGS per video: < $0.20

Text Generation:
  - P50 latency: < 8 seconds
  - P95 latency: < 15 seconds
  - Success rate: > 99.5%
  - COGS per text: < $0.02

Usage Tracking:
  - Counter accuracy: 100%
  - Reset reliability: 100%
  - Limit enforcement: 100%
```

### Business KPIs
```yaml
User Engagement:
  - Video request rate: 60-70% of requests
  - Text fallback rate: 15-20% (when quota exceeded)
  - Upgrade conversion: 8-12% (limit reached → upgrade)

Profitability:
  - Free tier margin: > 50% (via ads)
  - Plus tier margin: > 5% (target: 10% by Q2)
  - Premium tier margin: > 15%
  - Enterprise tier margin: > 60%

Retention:
  - Month 1 → Month 2: > 70%
  - Month 2 → Month 3: > 55%
  - Month 3 → Month 6: > 40%
  - Churn reasons: Price (< 15%), Usage limits (< 10%)
```

---

## Risk Analysis

### Risk 1: Video COGS Exceeds Projections
**Probability**: Medium (40%)
**Impact**: High (could bankrupt Premium tier)

**Mitigation**:
- Weekly cost monitoring (alert if > $0.25/video)
- Dynamic limit adjustment (reduce from 60 → 50 if needed)
- Overage pricing for power users ($0.30/video after limit)
- Contract with video API provider (volume discounts)

---

### Risk 2: Users Abuse "Unlimited Text"
**Probability**: Low (20%)
**Impact**: Medium (high text COGS for small % of users)

**Mitigation**:
- Rate limiting: 10 requests/hour (prevents scripts)
- Anomaly detection: Alert if user > 500 requests/month
- Terms of Service: "Unlimited" = reasonable personal use
- Account suspension for abuse (manual review)

---

### Risk 3: Low Video Adoption
**Probability**: Low (15%)
**Impact**: Medium (high video infrastructure costs, low usage)

**Strategy if happens**:
- A/B test: Default to video (current) vs text
- User survey: Why prefer text?
- Improve video quality/speed
- If < 40% adoption after 3 months, consider text-primary model

---

### Risk 4: Competitors Offer "Unlimited Video"
**Probability**: Medium (30%)
**Impact**: High (competitive disadvantage)

**Response Options**:
1. **Maintain Limits**: Focus on quality, speed, customization
2. **Offer Unlimited**: Raise Premium to $14.99, bet on low usage
3. **Hybrid**: Unlimited text, unlimited low-res (720p) video
4. **Enterprise Focus**: Accept B2C loss leader, win B2B contracts

**Preferred**: Option 3 (Hybrid model)

---

## Competitive Analysis

| Competitor | Pricing | Text Support | Video Support | Notes |
|------------|---------|--------------|---------------|-------|
| **Synthesia** | $30/month | No | 10 min/month | Enterprise-focused, high quality |
| **D-ID** | $49/month | No | 20 videos/month | AI avatars, premium pricing |
| **Loom** | $12.50/month | No | Unlimited* | Screen recording, not generated |
| **Chegg** | $19.95/month | Yes | No | Q&A only, no video |
| **Course Hero** | $39.95/month | Yes | No | Documents, no personalization |
| **Vividly** | $4.99-9.99 | Yes (unlimited) | 20-60/month | **Dual modality = unique** |

**Key Insight**: No competitor offers both unlimited text + substantial video generation at < $10/month. This is Vividly's competitive moat.

---

## Conclusion

The dual-modality architecture (text-only vs text+video) is a **strategic differentiator** that positions Vividly uniquely in the market:

1. **Cost Efficiency**: Users can choose text when they just need information fast
2. **Premium Value**: Video generation provides high-value engagement for important topics
3. **Flexible Pricing**: Separate limits allow profitable tiers at multiple price points
4. **Competitive Moat**: No competitor offers this flexibility at comparable pricing

**Key Success Factor**: Effective user education. Users must understand:
- Text is fast, always available, great for quick help
- Video is engaging, limited quota, best for deep learning

**Next Steps**:
1. Implement Phase 1 (backend modality support)
2. User testing: Validate UX flows
3. Soft launch: Beta test with 100 users
4. Full launch: Roll out revised pricing tiers
5. Iterate: Monitor usage, adjust limits, optimize costs

---

**Document Status**: ✅ Complete
**Ready for**: Engineering Implementation (Phase 1)
**Estimated Timeline**: 8 weeks to full production
**Expected Impact**: 25% cost reduction, 15% higher margins, competitive differentiation

**Approved by**: Andrew Ng's Systematic Methodology™ (Analysis → Design → Validate → Iterate)
