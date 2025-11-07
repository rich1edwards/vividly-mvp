# Sprint 3: Production Monitoring & Observability - Implementation Plan

**Following Andrew Ng's Methodology: Build it right, test everything, think about the future**

## Executive Summary

Sprint 3 implements **infrastructure-level monitoring** to complete the observability layer for Vividly. Building on Sprint 1 (Authentication) and Sprint 2 (Rate Limiting & Security), this sprint integrates GCP Cloud Monitoring for metrics, structured logging, and alerting.

### Strategic Context

**Existing**: Application-level monitoring (`app/api/v1/endpoints/monitoring.py`, `app/routes/monitoring_dashboard.py`)
- Request tracking and lifecycle
- Dashboard for content generation pipeline
- Circuit breaker stats

**Missing** (Per Sprint 2 documentation):
- GCP Cloud Monitoring integration
- Custom metrics for rate limiting
- Custom metrics for authentication
- Structured logging throughout application
- Production alerting policies
- Infrastructure health monitoring

This sprint completes the observability stack.

## Current State Analysis

### ✅ What Exists
1. **Request Monitoring** - Full pipeline tracking for content generation
2. **Dashboard API** - Real-time monitoring endpoints
3. **Basic Logging** - `import logging` in 10+ files
4. **Circuit Breakers** - Resilience patterns implemented

### ❌ What's Missing (Sprint 3 Scope)
1. **GCP Cloud Monitoring Integration** - No metrics sent to GCP
2. **Structured Logging** - Using plain `logging`, not structured
3. **Custom Metrics** - No rate_limit_hits, auth_failures, etc.
4. **Alerting Policies** - No automated alerts for production issues
5. **Health Checks** - Basic endpoint exists but incomplete
6. **Tracing** - No distributed tracing

## Design Philosophy: Pragmatic + Production-Ready

Following Andrew Ng's "Start simple, scale when needed" and Sprint 2's precedent:

1. **Leverage GCP Native Tools**
   - Cloud Monitoring (formerly Stackdriver)
   - Cloud Logging (structured logs)
   - Built-in dashboards
   - Uptime checks

2. **Don't Over-Engineer**
   - Use Google Cloud libraries (not custom implementations)
   - Focus on critical metrics first
   - Add complexity only when needed

3. **Build for Current Scale**
   - Single-instance deployments (like Sprint 2's in-memory rate limiting)
   - Clear upgrade path to distributed systems
   - Documented scaling considerations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vividly Application                       │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Auth        │  │  Rate Limit  │  │  Content     │      │
│  │  Events      │  │  Events      │  │  Generation  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘              │
│                            │                                  │
│                   ┌────────▼────────┐                        │
│                   │  Monitoring     │                        │
│                   │  Service        │                        │
│                   │  (New)          │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼─────────────────────────────────┘
                             │
                 ┌───────────┼───────────┐
                 │           │           │
                 ▼           ▼           ▼
         ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
         │   Cloud     │ │   Cloud     │ │   Error     │
         │  Monitoring │ │  Logging    │ │  Reporting  │
         │  (Metrics)  │ │(Structured) │ │  (Sentry)   │
         └─────────────┘ └─────────────┘ └─────────────┘
                 │           │           │
                 └───────────┼───────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  GCP Alerting   │
                   │  Policies       │
                   └─────────────────┘
```

## Implementation Phases

### Phase 1: Structured Logging Foundation ⭐ START HERE
**Goal**: Replace plain logging with structured, searchable logs

**Files to Create**:
- `app/core/logging.py` - Structured logging setup
  - JSON formatter for production
  - Contextual logging (request_id, user_id, etc.)
  - Log levels configuration
  - GCP Cloud Logging integration

**Files to Modify**:
- Update all services to use structured logger
- Add correlation IDs to all requests
- Include metadata (service, environment, version)

**Testing**:
- Test log output format
- Verify searchability in GCP Logs Explorer
- Test log levels (DEBUG, INFO, WARNING, ERROR)

### Phase 2: GCP Cloud Monitoring Integration
**Goal**: Send custom metrics to GCP for visibility and alerting

**Files to Create**:
- `app/core/metrics.py` - Metrics client wrapper
  - Initialize Cloud Monitoring client
  - Helper functions for counter, gauge, histogram
  - Metric naming conventions
  - Resource descriptors (service, instance, etc.)

**Metrics to Track** (Per Sprint 2 documentation):

#### Rate Limiting Metrics
```python
# From Sprint 2 docs: RATE_LIMITING_SYSTEM.md
- rate_limit_hits_total (Counter)
  - Labels: endpoint, ip_address
  - Description: Total rate limit checks performed

- rate_limit_exceeded_total (Counter)
  - Labels: endpoint, ip_address
  - Description: Count of 429 responses returned

- brute_force_lockouts_total (Counter)
  - Labels: ip_address, email
  - Description: Account lockouts triggered

- rate_limit_middleware_latency_ms (Histogram)
  - Labels: endpoint
  - Description: Middleware processing time
```

#### Authentication Metrics
```python
- auth_login_attempts_total (Counter)
  - Labels: status (success/failure), user_role
  - Description: Login attempts

- auth_login_failures_total (Counter)
  - Labels: reason (invalid_password, user_not_found, account_locked)
  - Description: Failed login attempts

- auth_token_refresh_total (Counter)
  - Labels: status (success/failure)
  - Description: Token refresh operations

- auth_session_duration_seconds (Histogram)
  - Description: Session lifetime

- auth_active_sessions (Gauge)
  - Labels: user_role
  - Description: Current active sessions
```

#### System Health Metrics
```python
- http_request_total (Counter)
  - Labels: method, endpoint, status_code
  - Description: HTTP requests processed

- http_request_duration_seconds (Histogram)
  - Labels: method, endpoint
  - Description: Request processing time

- content_generation_requests_total (Counter)
  - Labels: status (pending, completed, failed)
  - Description: Content generation requests

- content_generation_duration_seconds (Histogram)
  - Labels: stage
  - Description: Time per generation stage
```

**Implementation**:
```python
from google.cloud import monitoring_v3
from app.core.metrics import metrics_client

# In rate limiting middleware
@metrics_client.counter('rate_limit_exceeded_total',
                       labels={'endpoint': path, 'ip_address': client_ip})
def record_rate_limit_exceeded():
    pass

# In authentication service
@metrics_client.counter('auth_login_attempts_total',
                       labels={'status': 'success', 'user_role': user.role})
def record_login_attempt():
    pass
```

### Phase 3: Alerting Policies
**Goal**: Automated alerts for production issues

**Alerting Policies to Create** (Per Sprint 2 docs):

#### High Priority Alerts
1. **Brute Force Attack**
   - Condition: >5 lockouts from single IP in 1 hour
   - Action: PagerDuty + Email to security team
   - Documentation: Investigation runbook

2. **DDoS Attempt**
   - Condition: >1000 rate limit hits in 5 minutes
   - Action: PagerDuty + Enable CDN rate limiting
   - Documentation: Mitigation playbook

3. **Service Down**
   - Condition: Health check fails for 2 minutes
   - Action: PagerDuty + Auto-restart (if configured)
   - Documentation: Recovery procedures

4. **High Error Rate**
   - Condition: >5% 5xx responses in 5 minutes
   - Action: PagerDuty + Email to eng team
   - Documentation: Error investigation guide

#### Medium Priority Alerts
5. **Elevated Rate Limiting**
   - Condition: 429 responses >10% of total traffic
   - Action: Email to eng team
   - Review: Check for legitimate spikes

6. **Performance Degradation**
   - Condition: P95 latency >2 seconds for 10 minutes
   - Action: Email to eng team
   - Review: Performance profiling

7. **Database Connection Issues**
   - Condition: Connection pool >80% utilized
   - Action: Email to eng team
   - Review: Scale database or optimize queries

8. **Authentication Failures Spike**
   - Condition: >100 failed logins in 10 minutes
   - Action: Email to security team
   - Review: Check for credential stuffing

**Implementation**:
- Terraform configurations for alerting policies
- Notification channels (email, PagerDuty, Slack)
- Severity levels and escalation paths

### Phase 4: Health Checks & Uptime Monitoring
**Goal**: Proactive detection of service issues

**Files to Create**:
- `app/api/v1/endpoints/health.py` (enhance existing)
  - Liveness check (is service running?)
  - Readiness check (is service ready to serve traffic?)
  - Dependency checks (database, Redis, external APIs)
  - Version and build info

**Health Check Endpoints**:
```python
GET /health - Basic liveness (200 OK)
GET /health/ready - Readiness check
  - Database connectivity
  - Redis connectivity (if used)
  - Required services available

GET /health/detailed - Comprehensive health
  - All dependency status
  - Resource utilization
  - Recent error rates
  - Build version, commit SHA
```

**GCP Uptime Checks**:
- Monitor `/health` from multiple regions
- Alert if unavailable for >2 minutes
- Public uptime dashboard

### Phase 5: Dashboards
**Goal**: Visibility into system health

**Dashboards to Create**:

1. **System Overview Dashboard**
   - Request rate (QPS)
   - Error rate (%)
   - P50/P95/P99 latency
   - Active users
   - Resource utilization (CPU, memory)

2. **Authentication Dashboard**
   - Login success/failure rate
   - Active sessions
   - Token refresh rate
   - Brute force lockouts
   - Session duration distribution

3. **Rate Limiting Dashboard**
   - Rate limit hits by endpoint
   - 429 responses by endpoint
   - Top rate-limited IPs
   - Middleware latency
   - Brute force attempts

4. **Content Generation Dashboard**
   - Requests by stage
   - Success/failure rates
   - Average duration per stage
   - Queue depth
   - Error types distribution

**Implementation**:
- JSON configurations for GCP dashboards
- Terraform for infrastructure-as-code
- Export/import scripts

## Testing Strategy

### Unit Tests
- Test metrics client initialization
- Test metric recording (mock GCP client)
- Test structured logging output format
- Test health check logic

### Integration Tests
- Test actual metric submission to GCP (test project)
- Verify logs appear in GCP Logs Explorer
- Test alert policy triggers
- Test health check endpoints

### Load Tests
- Verify metrics don't impact performance
- Test logging at high volume
- Verify metric aggregation accuracy

### CI/CD Tests
- Validate metric names and labels
- Check alert policy syntax
- Verify dashboard JSON validity
- Test health check responses

## Dependencies

### New Python Packages
```txt
# Add to requirements.txt
google-cloud-monitoring>=2.15.0
google-cloud-logging>=3.5.0
google-cloud-error-reporting>=1.9.0
opentelemetry-api>=1.20.0  # Future: distributed tracing
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-fastapi>=0.41b0
```

### GCP Services to Enable
```bash
# Cloud Monitoring API
gcloud services enable monitoring.googleapis.com

# Cloud Logging API
gcloud services enable logging.googleapis.com

# Error Reporting API
gcloud services enable clouderrorreporting.googleapis.com

# Cloud Trace API (Future)
gcloud services enable cloudtrace.googleapis.com
```

### IAM Permissions Needed
```yaml
roles/monitoring.metricWriter     # Write custom metrics
roles/logging.logWriter           # Write logs
roles/errorreporting.writer       # Write error reports
roles/monitoring.alertPolicyEditor  # Create/edit alert policies (Terraform)
```

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── logging.py              # NEW: Structured logging
│   │   ├── metrics.py              # NEW: GCP Cloud Monitoring
│   │   ├── health.py               # NEW: Health check logic
│   │   └── monitoring_middleware.py # NEW: Metrics middleware
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── health.py       # MODIFIED: Enhanced health checks
│   └── middleware/
│       └── security.py             # MODIFIED: Add metrics to existing middleware
├── tests/
│   ├── test_logging.py             # NEW: Structured logging tests
│   ├── test_metrics.py             # NEW: Metrics client tests
│   └── test_health.py              # NEW: Health check tests
├── docs/
│   └── MONITORING_SYSTEM.md        # NEW: Complete documentation
├── terraform/
│   ├── monitoring/
│   │   ├── dashboards.tf           # NEW: Dashboard configurations
│   │   ├── alert_policies.tf       # NEW: Alerting policies
│   │   └── uptime_checks.tf        # NEW: Uptime monitoring
└── .github/
    └── workflows/
        └── monitoring-tests.yml     # NEW: CI/CD for monitoring
```

## Success Metrics

### Functional Excellence
- ✅ All critical metrics flowing to GCP
- ✅ Structured logs searchable in GCP Logs Explorer
- ✅ Alerts trigger correctly (verified in staging)
- ✅ Health checks return accurate status
- ✅ Dashboards show real-time data

### Quality Standards
- ✅ 80%+ test coverage for monitoring code
- ✅ All tests passing in CI/CD
- ✅ Load tests confirm <5ms overhead per request
- ✅ No false positive alerts in 1 week of staging

### Operational Readiness
- ✅ Runbooks for all alerts
- ✅ On-call playbooks documented
- ✅ Metrics retention configured (30 days)
- ✅ Log retention configured (30 days)
- ✅ Cost monitoring in place

## Migration Strategy

### Week 1: Foundation
- Create structured logging module
- Update 5-10 high-traffic endpoints
- Test in development environment
- Verify logs in GCP

### Week 2: Metrics
- Create metrics client
- Add rate limiting metrics
- Add authentication metrics
- Deploy to staging
- Verify metrics in GCP

### Week 3: Alerts & Dashboards
- Create alert policies
- Build dashboards
- Test alerts in staging
- Create runbooks
- Train team

### Week 4: Production Rollout
- Deploy to production (canary)
- Monitor for issues
- Roll out to all instances
- Document lessons learned

## Cost Considerations

### Estimated Monthly Costs (Low-Medium Traffic)
- **Cloud Monitoring**: $0.50-2.00 (first 150MB free)
- **Cloud Logging**: $0.50-5.00 (first 50GB free)
- **Uptime Checks**: $0.30-1.00
- **Alerting**: Free (notifications via email/PagerDuty separate cost)

**Total**: ~$1-8/month at current scale

### Cost Optimization
- Sample high-volume logs (keep 10% of DEBUG logs)
- Aggregate metrics before sending
- Use default metrics where possible
- Set retention policies appropriately

## Andrew Ng's Principles Applied

### 1. ✅ Build it Right
- Use GCP native tools (not custom implementations)
- Industry-standard structured logging (JSON)
- OWASP-recommended metrics
- Reusable, modular design

### 2. ✅ Test Everything
- Unit tests for all monitoring code
- Integration tests with GCP
- Load testing for performance impact
- Alert policy testing in staging

### 3. ✅ Think About the Future
- Upgrade path to distributed tracing
- Scalable metric aggregation
- Documented cost optimization strategies
- Clear migration path to OpenTelemetry

## Comparison with Sprint 2

| Aspect | Sprint 2 (Rate Limiting) | Sprint 3 (Monitoring) |
|--------|-------------------------|---------------------|
| **Approach** | Leverage existing middleware | Integrate with GCP native services |
| **Storage** | In-memory → Redis path | GCP Cloud Monitoring (managed) |
| **Testing** | 600+ lines, 5 test classes | Similar comprehensive approach |
| **CI/CD** | GitHub Actions workflow | GitHub Actions + Terraform validation |
| **Documentation** | 650+ lines | Similar comprehensive docs |
| **Principle** | Pragmatic, production-ready | Pragmatic, production-ready |

## Next Session Handoff

When continuing this work:
1. Start with Phase 1: Structured Logging
2. Create `app/core/logging.py`
3. Update 2-3 services as examples
4. Test logging output
5. Move to Phase 2: Metrics

## References

### Internal Documentation
- [Sprint 1: Authentication](./SPRINT_1_AUTHENTICATION_COMPLETE.md)
- [Sprint 2: Rate Limiting](./SPRINT_2_RATE_LIMITING_COMPLETE.md)
- [Rate Limiting System Docs](./backend/docs/RATE_LIMITING_SYSTEM.md)

### External Resources
- [GCP Cloud Monitoring](https://cloud.google.com/monitoring/docs)
- [GCP Cloud Logging](https://cloud.google.com/logging/docs)
- [Structured Logging Best Practices](https://cloud.google.com/logging/docs/structured-logging)
- [OpenTelemetry](https://opentelemetry.io/)

---

**Status**: 🎯 **READY TO START** - Phase 1 implementation can begin

**Built following Andrew Ng's methodology:**
- ✅ **Build it right**: GCP native tools, industry standards
- ✅ **Test everything**: Comprehensive testing plan in place
- ✅ **Think about the future**: Clear upgrade paths documented
