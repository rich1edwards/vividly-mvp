# Vividly Security Architecture

**Version:** 1.0 (MVP)
**Last Updated:** October 27, 2025
**Classification:** Internal - Security Critical

## Table of Contents

1. [Overview](#overview)
2. [Security Principles](#security-principles)
3. [Authentication](#authentication)
4. [Authorization (RBAC)](#authorization-rbac)
5. [Data Encryption](#data-encryption)
6. [Secrets Management](#secrets-management)
7. [Network Security](#network-security)
8. [Application Security](#application-security)
9. [Compliance](#compliance)
10. [Incident Response](#incident-response)
11. [Security Monitoring](#security-monitoring)
12. [Security Checklist](#security-checklist)

---

## Overview

Vividly handles sensitive student data and must maintain the highest security standards to comply with FERPA, COPPA, and protect student privacy.

### Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Unauthorized data access | Medium | Critical | Authentication, RBAC, encryption |
| Data breach | Low | Critical | Encryption, access logging, monitoring |
| SQL injection | Medium | High | Parameterized queries, ORM |
| XSS attacks | Medium | High | Input sanitization, CSP headers |
| CSRF attacks | Medium | Medium | CSRF tokens, SameSite cookies |
| DDoS | Medium | Medium | Cloud Armor, rate limiting |
| Session hijacking | Low | High | Secure cookies, HTTPS only |
| Credential stuffing | Medium | Medium | Rate limiting, MFA (future) |

---

## Security Principles

### 1. Defense in Depth
Multiple layers of security controls throughout the stack.

### 2. Least Privilege
Users and services have minimum necessary permissions.

### 3. Secure by Default
Security features enabled by default, must opt-out (not opt-in).

### 4. Zero Trust
Never trust, always verify - even internal requests.

### 5. Privacy by Design
Data protection built into system architecture from the start.

---

## Authentication

### JWT-Based Authentication

**Technology**: JSON Web Tokens (JWT)
**Algorithm**: HS256 (HMAC with SHA-256)
**Expiration**: 24 hours

#### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "iss": "vividly-mvp",
    "sub": "user_abc123",
    "user_id": "user_abc123",
    "email": "student@example.com",
    "role": "student",
    "org_id": "org_mnps",
    "school_id": "school_hillsboro_hs",
    "iat": 1730070000,
    "exp": 1730156400
  },
  "signature": "..."
}
```

#### Implementation

```python
# backend/services/auth.py

import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")  # From Secret Manager
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user: User) -> str:
    """Create JWT access token for user."""

    payload = {
        "iss": "vividly-mvp",
        "sub": user.id,
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "org_id": user.org_id,
        "school_id": user.school_id if hasattr(user, 'school_id') else None,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")

    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

def authenticate_user(email: str, password: str) -> User:
    """Authenticate user with email and password."""

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise AuthenticationError("Invalid credentials")

    if not verify_password(password, user.password_hash):
        # Log failed attempt
        log_failed_login_attempt(email)
        raise AuthenticationError("Invalid credentials")

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Log successful login
    log_audit_event("user_login", user_id=user.id)

    return user
```

#### FastAPI Middleware

```python
# backend/middleware/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Extract and verify current user from JWT."""

    token = credentials.credentials

    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )

        return user

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
```

### Password Requirements

```python
import re

PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": False  # Not required for students (MVP)
}

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password meets requirements."""

    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"

    if PASSWORD_REQUIREMENTS["require_uppercase"] and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if PASSWORD_REQUIREMENTS["require_lowercase"] and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if PASSWORD_REQUIREMENTS["require_digit"] and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    if PASSWORD_REQUIREMENTS["require_special"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, "Password meets requirements"
```

### Rate Limiting (Login Protection)

```python
from collections import defaultdict
from datetime import datetime, timedelta

# In-memory rate limiting (use Redis in production)
login_attempts = defaultdict(list)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

def check_login_rate_limit(email: str) -> bool:
    """Check if login attempts exceed rate limit."""

    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    # Clean old attempts
    login_attempts[email] = [
        attempt for attempt in login_attempts[email]
        if attempt > cutoff
    ]

    # Check if locked out
    if len(login_attempts[email]) >= MAX_LOGIN_ATTEMPTS:
        return False

    return True

def log_failed_login_attempt(email: str):
    """Log failed login attempt."""

    login_attempts[email].append(datetime.utcnow())

    # Alert if many failed attempts
    if len(login_attempts[email]) >= MAX_LOGIN_ATTEMPTS:
        send_security_alert(
            "Multiple failed login attempts",
            details={"email": email, "count": len(login_attempts[email])}
        )
```

---

## Authorization (RBAC)

### Role-Based Access Control

#### Role Hierarchy

```
vividly_admin (superuser)
    ├── district_admin
    │   ├── school_admin
    │   │   └── teacher
    │   │       └── student
    │   └── vividly_curriculum
    └── vividly_ops (read-only)
```

#### Permission Matrix

| Resource | Student | Teacher | School Admin | District Admin | Vividly Admin |
|----------|---------|---------|--------------|----------------|---------------|
| Own profile (read) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Own profile (write) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Request content | ✅ | ❌ | ❌ | ❌ | ✅ |
| View own progress | ✅ | ❌ | ❌ | ❌ | ✅ |
| View student progress | ❌ | ✅ (own students) | ✅ (school) | ✅ (district) | ✅ |
| Manage classes | ❌ | ✅ (own) | ✅ (school) | ✅ (district) | ✅ |
| Request student account | ❌ | ✅ | ❌ | ❌ | ✅ |
| Approve student account | ❌ | ❌ | ✅ | ✅ | ✅ |
| Bulk upload students | ❌ | ❌ | ✅ | ✅ | ✅ |
| View KPIs | ❌ | ✅ (class) | ✅ (school) | ✅ (district) | ✅ |
| Manage topics | ❌ | ❌ | ❌ | ❌ | ✅ |

#### Implementation

```python
# backend/middleware/authorization.py

from functools import wraps
from fastapi import HTTPException, status

def require_role(*allowed_roles):
    """Decorator to require specific role(s)."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {allowed_roles}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@app.get("/api/v1/admin/users")
@require_role("district_admin", "school_admin", "vividly_admin")
async def get_users(current_user: User = Depends(get_current_user)):
    """Get users (admin only)."""
    # Implementation
    pass

def check_resource_ownership(user: User, resource: Any) -> bool:
    """Check if user owns or has access to resource."""

    # Student can only access own resources
    if user.role == "student":
        return hasattr(resource, 'student_id') and resource.student_id == user.id

    # Teacher can access students in their classes
    if user.role == "teacher":
        if hasattr(resource, 'student_id'):
            student_classes = db.query(ClassStudents).filter(
                ClassStudents.student_id == resource.student_id
            ).all()
            teacher_classes = db.query(Class).filter(Class.teacher_id == user.id).all()
            teacher_class_ids = [c.id for c in teacher_classes]
            return any(sc.class_id in teacher_class_ids for sc in student_classes)

    # School admin can access resources in their school
    if user.role == "school_admin":
        return resource.school_id == user.school_id

    # District admin can access resources in their district
    if user.role == "district_admin":
        return resource.org_id == user.org_id

    # Vividly admin has full access
    if user.role == "vividly_admin":
        return True

    return False
```

---

## Data Encryption

### Encryption at Rest

#### Google Cloud Services
- **Cloud SQL**: Automatic encryption with Google-managed keys
- **Cloud Storage**: Automatic encryption with Google-managed keys
- **Secret Manager**: Encrypted by default

#### Application-Level Encryption (Future)

```python
from cryptography.fernet import Fernet

# For highly sensitive PII (future enhancement)
ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")  # From Secret Manager
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_field(plaintext: str) -> str:
    """Encrypt sensitive field."""
    return cipher_suite.encrypt(plaintext.encode()).decode()

def decrypt_field(ciphertext: str) -> str:
    """Decrypt sensitive field."""
    return cipher_suite.decrypt(ciphertext.encode()).decode()

# Usage for SSN, etc. (if needed in future)
user.ssn_encrypted = encrypt_field(user.ssn)
```

### Encryption in Transit

#### TLS Configuration

```yaml
# All traffic uses TLS 1.3
min_tls_version: "1.3"
cipher_suites:
  - TLS_AES_128_GCM_SHA256
  - TLS_AES_256_GCM_SHA384
  - TLS_CHACHA20_POLY1305_SHA256

# HSTS header
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

#### Certificate Management

```bash
# Google-managed SSL certificates for Cloud Load Balancer
gcloud compute ssl-certificates create vividly-cert \
    --domains=app.vividly.education,api.vividly.education \
    --global

# Auto-renewal enabled
```

---

## Secrets Management

### Google Secret Manager

All secrets stored in Secret Manager, never in code or environment variables.

```python
# backend/utils/secrets.py

from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id: str, version: str = "latest") -> str:
    """Retrieve secret from Google Secret Manager."""

    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version}"

    response = client.access_secret_version(request={"name": name})
    secret_value = response.payload.data.decode('UTF-8')

    return secret_value

# Usage
JWT_SECRET = get_secret("jwt-secret")
DB_PASSWORD = get_secret("db-password")
NANO_BANANA_API_KEY = get_secret("nano-banana-api-key")
```

### Secret Rotation

```python
def rotate_jwt_secret():
    """Rotate JWT secret (requires coordinated deployment)."""

    # 1. Generate new secret
    new_secret = secrets.token_urlsafe(64)

    # 2. Store in Secret Manager
    client.add_secret_version(
        parent=f"projects/{PROJECT_ID}/secrets/jwt-secret",
        payload={"data": new_secret.encode('UTF-8')}
    )

    # 3. Deploy with dual-verification period (old + new valid)
    # 4. After 24h, disable old version

    logger.info("JWT secret rotated successfully")
```

### Secrets Checklist

- [ ] No secrets in code
- [ ] No secrets in git history
- [ ] All secrets in Secret Manager
- [ ] Secrets rotated quarterly
- [ ] Access audited monthly
- [ ] Secrets never logged

---

## Network Security

### Cloud Armor (WAF)

```yaml
# Cloud Armor security policy
name: vividly-armor-policy
rules:
  - priority: 1000
    description: "Block SQL injection attempts"
    match:
      expr:
        expression: "evaluatePreconfiguredExpr('sqli-stable')"
    action: "deny(403)"

  - priority: 1001
    description: "Block XSS attempts"
    match:
      expr:
        expression: "evaluatePreconfiguredExpr('xss-stable')"
    action: "deny(403)"

  - priority: 2000
    description: "Rate limit per IP"
    match:
      versionedExpr: "SRC_IPS_V1"
      config:
        srcIpRanges: ["*"]
    rateLimitOptions:
      conformAction: "allow"
      exceedAction: "deny(429)"
      rateLimitThreshold:
        count: 1000
        intervalSec: 60

  - priority: 10000
    description: "Default allow"
    match:
      versionedExpr: "SRC_IPS_V1"
      config:
        srcIpRanges: ["*"]
    action: "allow"
```

### VPC Security

```
┌─────────────────────────────────────────────┐
│  Internet                                   │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Cloud Armor (WAF) + Load Balancer          │
│  - DDoS protection                          │
│  - SSL termination                          │
│  - Rate limiting                            │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  VPC (Private Network)                      │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  Cloud Run Services                    │ │
│  │  - Private IPs only                    │ │
│  │  - Ingress: Load Balancer only         │ │
│  │  - Egress: Private Google Access       │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  Cloud SQL                              │ │
│  │  - Private IP only                      │ │
│  │  - No public access                     │ │
│  └────────────────────────────────────────┘ │
│                                              │
└──────────────────────────────────────────────┘
```

### Firewall Rules

```bash
# Allow only necessary traffic
gcloud compute firewall-rules create allow-https \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:443 \
    --source-ranges=0.0.0.0/0

# Block all other ingress by default
gcloud compute firewall-rules create default-deny \
    --direction=INGRESS \
    --action=DENY \
    --rules=all \
    --source-ranges=0.0.0.0/0 \
    --priority=65534
```

---

## Application Security

### Input Validation

```python
from pydantic import BaseModel, validator, EmailStr

class CreateUserRequest(BaseModel):
    """Validated user creation request."""

    email: EmailStr  # Automatically validates email format
    password: str
    first_name: str
    last_name: str
    grade_level: int

    @validator('password')
    def validate_password(cls, v):
        is_valid, message = validate_password(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        # Remove any HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        # Limit length
        if len(v) > 100:
            raise ValueError("Name too long")
        return v.strip()

    @validator('grade_level')
    def validate_grade(cls, v):
        if not (9 <= v <= 12):
            raise ValueError("Grade level must be 9-12")
        return v
```

### SQL Injection Prevention

```python
# ALWAYS use ORM or parameterized queries

# ✅ GOOD: Using SQLAlchemy ORM
users = db.query(User).filter(User.email == email).all()

# ✅ GOOD: Parameterized raw query
db.execute(
    "SELECT * FROM users WHERE email = :email",
    {"email": email}
)

# ❌ BAD: String interpolation (NEVER DO THIS)
# db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### XSS Prevention

```python
# Backend: Sanitize output
from markupsafe import escape

def sanitize_output(text: str) -> str:
    """Escape HTML entities to prevent XSS."""
    return escape(text)

# Frontend: React automatically escapes
// ✅ SAFE: React escapes by default
<div>{userInput}</div>

// ❌ UNSAFE: dangerouslySetInnerHTML
// <div dangerouslySetInnerHTML={{__html: userInput}} />
```

### CSRF Protection

```python
from fastapi_csrf_protect import CsrfProtect

# CSRF protection for state-changing requests
@app.post("/api/v1/users")
async def create_user(
    request: Request,
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # Process request
```

### Content Security Policy

```python
# Security headers middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

# CSP header
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "img-src 'self' data: https://storage.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "connect-src 'self' https://api.vividly.education; "
    "media-src 'self' https://storage.googleapis.com; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = CSP_POLICY
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

---

## Compliance

### FERPA Compliance

```python
# Audit all student data access
@log_data_access
def get_student_progress(student_id: str, accessor: User):
    """Get student progress with audit logging."""

    # Verify accessor has legitimate educational interest
    if not has_educational_interest(accessor, student_id):
        log_security_violation(
            "Unauthorized student data access attempt",
            accessor=accessor.id,
            student=student_id
        )
        raise PermissionError("No educational interest in this student")

    # Log access
    log_audit_event(
        event_type="student_data_access",
        accessor_id=accessor.id,
        accessor_role=accessor.role,
        student_id=student_id,
        data_accessed="progress",
        justification="dashboard_view"
    )

    return db.query(StudentProgress).filter_by(student_id=student_id).all()
```

### COPPA Compliance

```python
# No PII collection from students under 13 without parental consent
# Vividly targets high school (14+), but safety check:

def create_student_account(student_data: dict):
    """Create student account with age verification."""

    # Calculate age from grade level
    estimated_age = student_data["grade_level"] + 5  # Rough estimate

    if estimated_age < 13:
        # Require parental consent workflow
        require_parental_consent(student_data)

    # Minimal PII collection
    student = User(
        email=student_data["email"],  # School email only
        first_name=student_data["first_name"],
        last_name=student_data["last_name"],
        grade_level=student_data["grade_level"],
        # NO: date of birth, address, phone, SSN
    )

    db.add(student)
    db.commit()
```

---

## Incident Response

### Security Incident Playbook

#### 1. Data Breach

```
SEVERITY: P0 (Critical)
RESPONSE TIME: Immediate (< 1 hour)

STEPS:
1. CONTAIN (within 1 hour):
   - Identify compromised systems
   - Revoke compromised credentials
   - Block attacker IP addresses
   - Isolate affected systems

2. ASSESS (within 4 hours):
   - Determine scope of breach
   - Identify affected students/data
   - Document timeline

3. NOTIFY (within 24 hours):
   - Notify affected schools/districts
   - Notify affected students/parents (if required)
   - File breach report with authorities (if required)

4. REMEDIATE (within 1 week):
   - Patch vulnerabilities
   - Rotate all secrets
   - Deploy security updates
   - Conduct security audit

5. POST-MORTEM (within 2 weeks):
   - Root cause analysis
   - Update security controls
   - Update incident response plan
```

#### 2. Unauthorized Access

```
SEVERITY: P1 (High)
RESPONSE TIME: < 4 hours

STEPS:
1. Verify unauthorized access occurred
2. Lock affected user accounts
3. Review audit logs for accessed data
4. Notify affected parties
5. Force password reset
6. Review and strengthen access controls
```

### Incident Logging

```python
def log_security_incident(
    incident_type: str,
    severity: str,
    description: str,
    **details
):
    """Log security incident."""

    incident = SecurityIncident(
        type=incident_type,
        severity=severity,
        description=description,
        details=json.dumps(details),
        detected_at=datetime.utcnow(),
        status="open"
    )

    db.add(incident)
    db.commit()

    # Alert security team
    if severity in ["critical", "high"]:
        send_pagerduty_alert(
            title=f"{severity.upper()} Security Incident: {incident_type}",
            description=description,
            details=details
        )

    # Log to Cloud Logging
    logger.error(
        f"Security Incident: {incident_type}",
        extra={
            "severity": severity,
            "details": details,
            "incident_id": incident.id
        }
    )
```

---

## Security Monitoring

### Metrics to Track

```python
SECURITY_METRICS = {
    "failed_login_attempts": "Count of failed login attempts",
    "unauthorized_access_attempts": "Count of 403 errors",
    "sql_injection_attempts": "Count blocked by Cloud Armor",
    "xss_attempts": "Count blocked by Cloud Armor",
    "rate_limit_violations": "Count of 429 errors",
    "unusual_data_access_patterns": "Anomaly detection",
    "secrets_rotation_age": "Days since last rotation"
}
```

### Anomaly Detection

```python
def detect_unusual_access_pattern(user: User) -> bool:
    """Detect unusual access patterns."""

    # Check for sudden spike in data access
    recent_accesses = get_user_data_accesses(user.id, hours=1)
    typical_accesses = get_user_typical_access_rate(user.id)

    if len(recent_accesses) > typical_accesses * 10:
        log_security_incident(
            "unusual_access_pattern",
            severity="medium",
            description=f"User {user.id} accessing data at 10x normal rate",
            user_id=user.id,
            access_count=len(recent_accesses)
        )
        return True

    # Check for access from unusual location
    current_ip = get_current_ip()
    typical_ips = get_user_typical_ips(user.id)

    if current_ip not in typical_ips:
        # Soft alert (don't block, just log)
        logger.warning(
            f"User {user.id} accessing from new IP: {current_ip}"
        )

    return False
```

---

## Security Checklist

### Pre-Deployment Checklist

- [ ] All secrets in Secret Manager (no hardcoded secrets)
- [ ] HTTPS enforced (HSTS enabled)
- [ ] Authentication required on all endpoints (except login)
- [ ] RBAC implemented and tested
- [ ] Input validation on all user inputs
- [ ] SQL injection protection (ORM/parameterized queries)
- [ ] XSS protection (output escaping)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)
- [ ] Cloud Armor policies deployed
- [ ] Audit logging enabled
- [ ] Security monitoring alerts configured
- [ ] Incident response plan documented
- [ ] Vulnerability scan completed (no critical issues)
- [ ] Penetration test completed (if budget allows)
- [ ] Security review by security team

### Ongoing Security Tasks

**Weekly**:
- [ ] Review security alerts
- [ ] Review failed login attempts
- [ ] Review audit logs for anomalies

**Monthly**:
- [ ] Review and update firewall rules
- [ ] Review IAM permissions (least privilege)
- [ ] Review security monitoring metrics
- [ ] Dependency vulnerability scan

**Quarterly**:
- [ ] Rotate secrets
- [ ] Security training for team
- [ ] Review and update security policies
- [ ] Penetration testing (if budget allows)

**Annually**:
- [ ] Third-party security audit
- [ ] FERPA/COPPA compliance review
- [ ] Disaster recovery drill
- [ ] Update incident response plan

---

**Document Control**
- **Owner**: Security Team
- **Classification**: Internal - Security Critical
- **Last Review**: October 27, 2025
- **Next Review**: Quarterly
- **Approvers**: CTO, Legal, Compliance Officer
