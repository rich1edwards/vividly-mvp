# Vividly MVP - Implementation Guide

## Critical Components Implemented ✅

### 1. Database Seed Scripts ✅
**Location**: `backend/scripts/seed_database.py`

**Includes**:
- Davidson County Metro Schools (district)
- Hillsboro High School
- Early College High School
- 3 admins, 7 teachers, 35 students
- Sample topics, interests, classes
- Learning history examples

**Usage**:
```bash
cd backend
python scripts/seed_database.py
```

**Test Credentials**:
- Admin: `admin@davidsonschools.org` / `Admin123!`
- Teacher: `david.martinez@hillsboro.edu` / `Teacher123!`
- Student: `john.doe.11@student.hillsboro.edu` / `Student123!`

---

### 2. Docker Compose ✅
**Location**: `docker-compose.yml`

**Services**:
- PostgreSQL (database)
- Redis (caching)
- API Gateway (FastAPI)
- Admin Service (FastAPI)
- Content Worker (background jobs)
- Frontend (React + Vite)
- Adminer (DB UI)
- Redis Commander (Redis UI)
- Nginx (reverse proxy - optional)

**Usage**:
```bash
# Start all services
docker-compose up

# Start only database
docker-compose up postgres redis

# Rebuild
docker-compose up --build

# View logs
docker-compose logs -f api-gateway
```

---

### 3. Authentication Middleware ✅
**Location**: `backend/app/middleware/auth.py`

**Features**:
- JWT token generation/validation
- Password hashing (bcrypt, 12 rounds)
- Role-based access control (RBAC)
- Session management
- Login attempt tracking
- Password reset tokens

**Usage**:
```python
from app.middleware.auth import (
    get_current_user,
    require_admin,
    require_teacher,
    hash_password,
    verify_password
)

# Protected endpoint
@app.get("/api/v1/admin/dashboard")
async def admin_dashboard(
    user: User = Depends(require_admin)
):
    return {"message": "Admin dashboard"}
```

---

### 4. Rate Limiting Middleware ✅
**Location**: `backend/app/middleware/rate_limit.py`

**Features**:
- Per-user and per-IP rate limiting
- Token bucket algorithm with Redis
- Configurable limits per endpoint
- Rate limit headers in responses
- Auth endpoint protection (5 attempts/15min)
- Content request limits (10/hour)

**Usage**:
```python
from app.middleware.rate_limit import rate_limit

@app.post("/api/v1/students/content/request")
@rate_limit(limit=10, window_seconds=3600)
async def request_content(request: Request):
    ...
```

---

### 5. OER Content Ingestion ✅
**Location**: `backend/scripts/oer_ingestion/`

**Documentation**: Complete README with pipeline details
**Scripts**: Templates provided for:
- Download OpenStax books
- Parse CNXML to JSON
- Chunk content (500 words)
- Generate embeddings (Vertex AI)
- Create vector index

**Run Pipeline**:
```bash
cd backend/scripts/oer_ingestion
python run_pipeline.py
```

---

## Critical Components To Implement

### 6. UI Design System (shadcn/ui)

**Create**: `frontend/DESIGN_SYSTEM.md`

```markdown
# Vividly Design System

## Component Library: shadcn/ui + Tailwind CSS

### Installation
```bash
cd frontend
npx shadcn-ui@latest init
```

### Color Palette
```css
:root {
  /* Primary - Education/Trust */
  --primary: 217 91% 60%;        /* Blue #4C9AFF */
  --primary-dark: 217 91% 40%;
  --primary-light: 217 91% 80%;

  /* Secondary - Energy/STEM */
  --secondary: 142 76% 36%;      /* Green #16A34A */

  /* Accent - Engagement */
  --accent: 280 89% 60%;         /* Purple #A855F7 */

  /* Neutrals */
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;
  --muted: 210 40% 96%;
  --border: 214 32% 91%;
}
```

### Typography
- **Headings**: Inter (Google Fonts)
- **Body**: Inter
- **Code**: JetBrains Mono

### Core Components
Use shadcn/ui components:
- Button, Card, Dialog, Form
- Input, Select, Checkbox, Radio
- Table, Tabs, Toast, Dropdown
- Progress, Skeleton, Badge

### Installation
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
# ... add as needed
```

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- Focus indicators
- Color contrast ratios >4.5:1

```

---

### 7. Email Templates

**Create**: `backend/templates/emails/`

**student-invitation.html**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to Vividly</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #4C9AFF; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1>Welcome to Vividly!</h1>
    </div>

    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
        <p>Hi {{student_name}},</p>

        <p>Your teacher {{teacher_name}} has invited you to join their class on Vividly!</p>

        <p><strong>Class:</strong> {{class_name}}<br>
        <strong>School:</strong> {{school_name}}</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{invitation_link}}" style="background: #4C9AFF; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Create Your Account
            </a>
        </div>

        <p style="color: #666; font-size: 14px;">This invitation expires in 7 days.</p>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

        <p style="color: #999; font-size: 12px;">
            Vividly - Personalized STEM Learning<br>
            Questions? Contact your teacher at {{teacher_email}}
        </p>
    </div>
</body>
</html>
```

**Other templates**: Create similar for:
- `teacher-welcome.html`
- `admin-welcome.html`
- `password-reset.html`
- `content-ready.html`

---

### 8. Redis to Terraform

**Add to**: `terraform/main.tf`

```hcl
# Redis Instance for Caching
resource "google_redis_instance" "cache" {
  name           = "${var.environment}-vividly-cache"
  tier           = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = var.environment == "prod" ? 5 : 1

  redis_version = "REDIS_7_0"
  display_name  = "Vividly Cache (${var.environment})"

  region                  = var.region
  authorized_network      = google_compute_network.vpc.id
  connect_mode           = "PRIVATE_SERVICE_ACCESS"

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  depends_on = [google_project_service.required_apis]
}

# Output Redis connection
output "redis_host" {
  value     = google_redis_instance.cache.host
  sensitive = true
}

output "redis_port" {
  value = google_redis_instance.cache.port
}
```

---

### 9. Error Tracking (Sentry)

**Add to**: `backend/requirements.txt`
```
sentry-sdk[fastapi]==1.40.0
```

**Configure**: `backend/app/main.py`
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
    integrations=[FastApiIntegration()],
    before_send=lambda event, hint: (
        None if os.getenv("DEBUG") == "true" else event
    )
)

# Add to FastAPI app
@app.exception_handler(Exception)
async def sentry_exception_handler(request: Request, exc: Exception):
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Environment Variables**:
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
```

---

### 10. Cloud CDN Configuration

**Add to**: `terraform/main.tf`

```hcl
# Backend bucket for CDN
resource "google_compute_backend_bucket" "video_cdn" {
  name        = "${var.environment}-vividly-video-cdn"
  bucket_name = google_storage_bucket.generated_content.name
  enable_cdn  = true

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    client_ttl        = 3600      # 1 hour
    default_ttl       = 86400     # 24 hours
    max_ttl           = 2592000   # 30 days
    negative_caching  = true
    serve_while_stale = 86400
  }
}

# URL map for CDN
resource "google_compute_url_map" "cdn_url_map" {
  name            = "${var.environment}-vividly-cdn-map"
  default_service = google_compute_backend_bucket.video_cdn.id
}

# HTTP(S) proxy
resource "google_compute_target_https_proxy" "cdn_proxy" {
  name             = "${var.environment}-vividly-cdn-proxy"
  url_map          = google_compute_url_map.cdn_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.cdn_cert.id]
}

# SSL certificate
resource "google_compute_managed_ssl_certificate" "cdn_cert" {
  name = "${var.environment}-vividly-cdn-cert"

  managed {
    domains = ["cdn-${var.environment}.vividly.edu"]
  }
}

# Forwarding rule
resource "google_compute_global_forwarding_rule" "cdn_forwarding" {
  name       = "${var.environment}-vividly-cdn-forwarding"
  target     = google_compute_target_https_proxy.cdn_proxy.id
  port_range = "443"
}

output "cdn_ip_address" {
  value = google_compute_global_forwarding_rule.cdn_forwarding.ip_address
}
```

---

### 11. API Error Handling (Circuit Breaker)

**Create**: `backend/app/utils/circuit_breaker.py`

```python
"""Circuit breaker pattern for external API calls."""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any
import httpx

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""

        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN. Try again in {self._time_until_retry()}s")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try recovery."""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _time_until_retry(self) -> int:
        """Calculate seconds until retry allowed."""
        if not self.last_failure_time:
            return 0

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        remaining = max(0, self.recovery_timeout - elapsed)
        return int(remaining)


# Usage example
nano_banana_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=httpx.TimeoutException
)

async def call_nano_banana_api(payload: dict):
    """Call video generation API with circuit breaker."""

    async def api_call():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.nanobanana.com/generate",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    return await nano_banana_circuit.call(api_call)
```

---

### 12. Video Player Specification

**Create**: `frontend/components/VideoPlayer/README.md`

```markdown
# Video Player Component

## Features
- HTML5 video with custom controls
- Playback speed (0.5x - 2x)
- Quality selection (auto, 1080p, 720p, 480p)
- Captions/subtitles (VTT)
- Picture-in-picture
- Keyboard shortcuts
- Progress tracking
- Resume from last position

## Usage
```tsx
import { VideoPlayer } from '@/components/VideoPlayer';

<VideoPlayer
  videoUrl="https://cdn.vividly.edu/content_123.mp4"
  captionsUrl="https://cdn.vividly.edu/content_123.vtt"
  title="Newton's Third Law"
  startTime={45}  // Resume from 45s
  onProgress={(time) => saveProgress(time)}
  onComplete={() => markCompleted()}
/>
```

## Implementation
Use video.js or Plyr for robust player:

```bash
npm install video.js @types/video.js
# or
npm install plyr-react
```

## Keyboard Shortcuts
- Space: Play/Pause
- ←/→: Seek backward/forward 10s
- ↑/↓: Volume up/down
- F: Fullscreen
- M: Mute
- C: Toggle captions
```

---

### 13. Cost Monitoring Script

**Create**: `scripts/monitor-costs.sh`

```bash
#!/bin/bash
# GCP Cost Monitoring Script

PROJECT_ID="vividly-dev-rich"
BILLING_ACCOUNT="01C317-04F6FF-882A12"

echo "=== Vividly GCP Cost Monitoring ==="
echo "Project: $PROJECT_ID"
echo

# Current month costs
echo "Current Month Costs:"
gcloud billing projects describe $PROJECT_ID \
  --billing-account=$BILLING_ACCOUNT \
  --format="table(billingAccountName, billingEnabled)"

# Set budget alert if not exists
echo
echo "Setting budget alert..."
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT \
  --display-name="Vividly Dev Monthly Budget" \
  --budget-amount=500USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100 \
  2>/dev/null || echo "Budget already exists"

echo
echo "✓ Cost monitoring configured"
echo "View costs: https://console.cloud.google.com/billing"
```

---

### 14. Feature Flag System

**Add to Database**: `migrations/add_feature_flags.sql`

```sql
-- Feature flags table
CREATE TABLE IF NOT EXISTS feature_flags (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    enabled BOOLEAN DEFAULT false,
    enabled_for_orgs TEXT[],  -- Array of org IDs
    enabled_percentage INTEGER DEFAULT 0 CHECK (enabled_percentage >= 0 AND enabled_percentage <= 100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default flags
INSERT INTO feature_flags (id, name, description, enabled) VALUES
('advanced_analytics', 'Advanced Analytics Dashboard', 'Premium analytics features', false),
('custom_branding', 'Custom Branding', 'Organization custom branding', false),
('video_download', 'Video Download', 'Allow students to download videos', false)
ON CONFLICT (id) DO NOTHING;
```

**Service**: `backend/app/services/feature_flags.py`

```python
"""Feature flag service."""

from sqlalchemy.orm import Session
from app.models import FeatureFlag
import random

def is_feature_enabled(
    feature_id: str,
    org_id: str,
    db: Session
) -> bool:
    """Check if feature is enabled for organization."""

    flag = db.query(FeatureFlag).filter(
        FeatureFlag.id == feature_id
    ).first()

    if not flag or not flag.enabled:
        return False

    # Check if org specifically enabled
    if flag.enabled_for_orgs and org_id in flag.enabled_for_orgs:
        return True

    # Check percentage rollout
    if flag.enabled_percentage > 0:
        # Deterministic random based on org_id
        hash_val = hash(f"{feature_id}:{org_id}") % 100
        return hash_val < flag.enabled_percentage

    return False
```

---

## Implementation Priority

### Week 1-2 (Critical)
1. ✅ Database seed scripts
2. ✅ Docker compose
3. ✅ Authentication middleware
4. ✅ Rate limiting
5. ✅ OER ingestion (documentation)

### Week 3-4 (High Priority)
6. ⏳ UI Design System setup
7. ⏳ Email templates
8. ⏳ Redis to Terraform
9. ⏳ Error tracking (Sentry)
10. ⏳ Cloud CDN
11. ⏳ Circuit breaker
12. ⏳ Video player
13. ⏳ Cost monitoring
14. ⏳ Feature flags

---

## Quick Setup Commands

```bash
# 1. Start infrastructure
docker-compose up -d postgres redis

# 2. Run migrations
cd backend
alembic upgrade head

# 3. Seed database
python scripts/seed_database.py

# 4. Start services
docker-compose up

# 5. Access
# - Frontend: http://localhost:3000
# - API: http://localhost:8080
# - Admin: http://localhost:8081
# - DB UI: http://localhost:8082
# - Redis UI: http://localhost:8083
```

---

## Next Steps

1. Complete remaining implementations (6-14)
2. Run OER content ingestion pipeline
3. Begin API endpoint development
4. Build frontend components
5. Integration testing
6. Deploy to dev environment

---

**Document Version**: 1.0
**Last Updated**: 2024-01-16
**Status**: 5/14 completed, 9/14 documented for implementation
