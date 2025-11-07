# Vividly Pricing & Monetization Strategy
**Author**: Andrew Ng's Strategic Business Design
**Date**: 2025-11-03
**Version**: 2.0 (Updated with Dual-Modality Support)
**Focus**: Multi-Tier SaaS with B2C (Public K-12) + B2B (Organizations)

---

## 🔄 Version 2.0 Update: Dual Content Modality Support

**Critical Addition**: Platform now supports two distinct content generation modes:
1. **Text-Only**: Script/transcript generation (COGS: ~$0.017/request)
2. **Text+Video**: Script + narrated video (COGS: ~$0.20/video)

**Impact on Pricing**:
- All tiers now have **separate usage limits** for text vs video generation
- Video generation is 12x more expensive → must be capped even on premium tiers
- Text-only generation can be "unlimited" on higher tiers (sustainable cost)

**See**: `CONTENT_MODALITY_SPEC.md` for detailed cost analysis and technical architecture.

---

## Executive Summary

This specification defines a **dual-monetization model** for Vividly:

1. **B2C (Consumer)**: Public K-12 platform where individual students/parents sign up with tiered pricing (Free, Plus, Premium)
2. **B2B (Business)**: Organizations (schools, districts, companies) purchase seats with organization-wide plans, with optional individual upgrades

### Key Innovation: Hybrid Plan Inheritance

Users in organizations get a **base plan** (set by org admin) but can **individually upgrade** to premium tiers, creating dual revenue streams:
- **Org subscription**: School pays for 500 students at "Basic" tier
- **Individual upgrades**: 50 students upgrade to "Premium" tier at their own expense

This model maximizes:
- **Market penetration**: Free tier for students without means
- **Revenue optimization**: Premium features for motivated learners
- **B2B scalability**: Orgs pay per-seat, individuals pay for upgrades
- **Viral growth**: Free users become Premium users, Premium users bring friends

---

## Pricing Tiers (K-12 Public Platform)

### Tier 1: Free (Freemium)

**Target Audience**: Individual students exploring the platform, low-income families, viral growth

**Content Generation Limits** (v2.0):
- ✓ **15 text-only requests per month** (scripts/transcripts)
- ✓ **3 video generations per month** (2-min limit per video)
- ⚠️ Users choose text-only vs video at request time

**Features**:
- ✓ OpenStax textbook content access
- ✓ Standard video quality (720p)
- ✓ Basic personalization (grade level + 1 interest)
- ✓ Community support (help center, FAQ)
- ✗ No priority processing (videos generated in FIFO queue)
- ✗ No offline downloads
- ✗ Ads displayed (5-second pre-roll before videos)

**Monetization**:
- $0/month (acquisition channel)
- Ad revenue: ~$1.50/user/month (conservative estimate)

**Cost Analysis** (v2.0):
- 15 text requests: 15 × $0.017 = $0.26
- 3 videos: 3 × $0.20 = $0.60
- **Total COGS**: $0.86/month
- Ad revenue target: $1.50/month
- **Net margin**: +$0.64/month (74%)

**Conversion Funnel**:
- Free users hit video limit → Offered text-only fallback or upgrade
- Users frequently choosing video → Prompted to upgrade to Plus
- Engaged users (3+ videos/week) → Targeted upgrade campaigns

---

### Tier 2: Plus ($4.99/month or $49/year)

**Target Audience**: Regular students using the platform for homework help, test prep

**Content Generation Limits** (v2.0):
- ✓ **100 text-only requests per month**
- ✓ **20 video generations per month** (5-min limit per video)
- ⚠️ Users choose text-only vs video at request time

**Features**:
- ✓ OpenStax + custom content sources (if in org)
- ✓ HD video quality (1080p)
- ✓ Advanced personalization (multiple interests, learning style)
- ✓ **Priority processing** (videos generated 2x faster)
- ✓ **No ads**
- ✓ Video history & search (90 days)
- ✓ Email support (24-hour response time)
- ✗ No offline downloads
- ✗ No advanced analytics

**Monetization**:
- $4.99/month = $59.88/year
- Or $49/year (save $10.88 = 18% discount)

**Cost Analysis** (v2.0):
- Typical usage: 70 text + 15 videos
- 70 text requests: 70 × $0.017 = $1.19
- 15 videos: 15 × $0.20 = $3.00
- **Total COGS**: $4.19/month
- Revenue: $4.99/month
- **Net margin**: +$0.80/month (16%)

**Value Proposition**:
- Cost = ~2 Starbucks drinks/month
- Removes ads (better learning experience)
- 100 text requests + 20 videos (substantial value)
- Faster video generation (no waiting)

---

### Tier 3: Premium ($9.99/month or $99/year)

**Target Audience**: Power users, students preparing for AP exams, SAT/ACT, competitive learners

**Content Generation Limits** (v2.0):
- ✓ **Unlimited text-only requests**
- ✓ **60 video generations per month** (5-min limit per video)
- ⚠️ Video cap necessary due to COGS ($12/month for 60 videos alone)

**Features**:
- ✓ All Plus features
- ✓ **Offline downloads** (download up to 50 videos for offline viewing)
- ✓ **Advanced analytics** (learning progress tracking, topic mastery)
- ✓ **Custom content sources** (upload your own PDFs, textbooks, notes - max 3)
- ✓ **Priority support** (live chat, 2-hour response time)
- ✓ **Early access to new features**
- ✓ **Source citations** in generated videos
- ✓ **Export transcripts** (PDF, Word)
- ✓ **Collaborative playlists** (share videos with classmates)
- ✓ **4K video quality option**
- ✓ **API access** (1,000 calls/month)

**Monetization**:
- $9.99/month = $119.88/year
- Or $99/year (save $20.88 = 17% discount)

**Cost Analysis** (v2.0):
- Typical usage: 150 text + 40 videos
- 150 text requests: 150 × $0.017 = $2.55
- 40 videos: 40 × $0.20 = $8.00
- **Total COGS**: $10.55/month
- Revenue: $9.99/month
- **Net margin**: -$0.56/month (-5%)
- **Breakeven usage**: 150 text + 38 videos
- Strategy: Target 35 videos/month average, high customer lifetime value

**Value Proposition**:
- Unlimited learning (no generation limits)
- Study anywhere (offline downloads)
- Track mastery (analytics)
- Own your content (custom sources)

---

### Tier 4: Family Plan ($14.99/month or $149/year)

**Target Audience**: Households with multiple K-12 students

**Features**:
- ✓ **Up to 4 student accounts**
- ✓ All Premium features for each student
- ✓ **Parent dashboard** (view all students' progress)
- ✓ Shared custom content sources
- ✓ Unified billing

**Monetization**:
- $14.99/month = $179.88/year
- Or $149/year (save $30.88 = 17% discount)

**Value Proposition**:
- Save 25% vs 2 Premium accounts ($19.98 → $14.99)
- Parental oversight
- Shared resources

---

## Organization Pricing (B2B)

### Model: Per-Seat Subscription

Organizations purchase seats in bulk with tiered pricing based on seat count and base plan tier.

---

### Organization Plan Tiers

#### Org Basic ($3/user/month, billed annually)

**Target**: Small schools, departments, pilot programs

**Features**:
- Base plan for users: **Plus** tier features
- Organization admin dashboard
- User management (add/remove users)
- OpenStax content + 1 custom content source
- Basic usage analytics (videos generated, users active)
- Standard support (email, 48-hour response)

**Minimum**: 10 seats
**Pricing**:
- 10-50 users: $3/user/month = $30-$150/month
- 51-100 users: $2.50/user/month
- 101+ users: $2/user/month

**Example**:
- 25-student class: $75/month = $900/year
- Each student gets Plus-tier features by default

---

#### Org Professional ($7/user/month, billed annually)

**Target**: Schools, districts, departments with > 100 users

**Features**:
- Base plan for users: **Premium** tier features
- All Org Basic features
- Unlimited custom content sources
- Advanced analytics (engagement, mastery, usage by class/grade)
- SSO integration (SAML, Google Workspace, Microsoft)
- API access (for LMS integration)
- Priority support (live chat, 24-hour response)
- Dedicated customer success manager (for 500+ seats)

**Minimum**: 50 seats
**Pricing**:
- 50-200 users: $7/user/month
- 201-500 users: $6/user/month
- 501-1,000 users: $5/user/month
- 1,001+ users: Custom pricing

**Example**:
- 500-student school: $3,000/month = $36,000/year
- Each student gets Premium-tier features by default

---

#### Org Enterprise (Custom Pricing)

**Target**: Large districts, universities, corporations with > 1,000 users

**Features**:
- All Org Professional features
- Custom contract terms
- White-label branding (custom domain, logo, colors)
- Dedicated infrastructure (isolated deployment)
- Custom SLA (99.9% uptime guarantee)
- On-premise deployment option (for sensitive data)
- Dedicated support team
- Custom feature development (roadmap influence)
- Training & onboarding for admins/teachers

**Pricing**: Contact sales

**Example**:
- 10,000-student district: ~$200,000/year ($1.67/user/month)
- Custom knowledge base (district curriculum)
- White-label: "Lincoln Learning" instead of "Vividly"

---

## Hybrid Model: Org Base Plan + Individual Upgrades

### How It Works

#### Scenario: School with Org Basic Plan

**School Configuration** (set by Super Admin during onboarding):
```
Organization: Lincoln High School
Org Plan: Basic ($3/user/month)
Base User Plan: Plus tier
Total Seats: 500 students
Allow Individual Upgrades: YES
```

**User Experience**:

1. **Student A** (uses default org plan):
   - Gets Plus tier features (25 videos/month, priority processing, no ads)
   - School pays $3/month for this student
   - Student pays $0

2. **Student B** (upgrades individually to Premium):
   - Gets Premium tier features (unlimited videos, offline downloads, analytics)
   - School pays $3/month (base plan)
   - **Student pays $5/month** (upgrade cost = $9.99 Premium - ~$5 org subsidy)
   - Revenue: $3 (org) + $5 (student) = $8/month total

3. **Student C** (Free tier user, not in org):
   - Gets Free tier features (5 videos/month, ads)
   - School pays $0 (not enrolled)
   - Student pays $0

**Upgrade Pricing Logic**:
```python
def calculate_upgrade_cost(org_base_plan, target_plan):
    """
    Calculate individual upgrade cost based on org's base plan.
    Users only pay the DIFFERENCE between org plan and target plan.
    """
    PLAN_VALUES = {
        'free': 0,
        'plus': 4.99,
        'premium': 9.99
    }

    org_value = PLAN_VALUES.get(org_base_plan, 0)
    target_value = PLAN_VALUES[target_plan]

    # User pays the difference
    upgrade_cost = max(0, target_value - org_value)

    return upgrade_cost

# Examples
calculate_upgrade_cost('plus', 'premium')  # $5.00/month (student pays)
calculate_upgrade_cost('premium', 'premium')  # $0/month (already premium)
calculate_upgrade_cost('free', 'plus')  # $4.99/month (no org discount)
```

---

### Organization Controls

#### Super Admin Sets Org Policies

```
Allow Individual Upgrades: [YES / NO]

If YES:
  ├─ Upgrade Options: [Premium, Family]
  ├─ Payment Method: [Student credit card, Parent billing]
  └─ Approval Required: [YES / NO]
      ├─ If YES: Admin/Teacher must approve upgrade request
      └─ If NO: Student can upgrade immediately
```

**Use Cases**:

**School A (Public School, Low Income)**:
- Org Plan: Basic (Plus tier for all)
- Allow Individual Upgrades: **NO** (maintain equity)
- Reasoning: Don't want "haves vs have-nots" dynamic

**School B (Private School)**:
- Org Plan: Professional (Premium tier for all)
- Allow Individual Upgrades: **YES** (to Family plan for siblings)
- Reasoning: Parents willing to pay for family accounts

**School C (Charter School)**:
- Org Plan: Basic (Plus tier for all)
- Allow Individual Upgrades: **YES** (with teacher approval)
- Reasoning: Motivated students can upgrade for test prep

---

## Public K-12 Signup Flow

### Route: `/auth/register` (Public)

#### Step 1: Account Type Selection

```
Create Your Vividly Account

Who is creating this account?
[Radio buttons with icons]

○ I'm a Student (K-12)
  → Join millions of students learning smarter, not harder

○ I'm a Parent
  → Create an account for my child or family

○ I'm a Teacher
  → Connect with your school or explore teacher tools

[Next →]
```

---

#### Step 2A: Student Registration

```
Create Your Student Account

Email: [Input]
Password: [Input with strength meter]
Confirm Password: [Input]

First Name: [Input]
Last Name: [Input]
Grade Level: [Dropdown: 6th, 7th, 8th, 9th, 10th, 11th, 12th]

School (Optional):
  [Search for your school: e.g., "Lincoln High School, CA"]
  OR
  [I don't see my school / I'm homeschooled]

Select Your Plan:
[Three plan cards with highlighted features]

[FREE - $0/month]
  - 5 videos/month
  - Standard quality
  - Ads displayed
  [Start Free]

[PLUS - $4.99/month] ⭐ MOST POPULAR
  - 25 videos/month
  - HD quality
  - Priority processing
  - No ads
  [Start 7-Day Free Trial]

[PREMIUM - $9.99/month]
  - Unlimited videos
  - Offline downloads
  - Advanced analytics
  - Custom content
  [Start 7-Day Free Trial]

[ ] I agree to Terms of Service and Privacy Policy (required)
[ ] Send me tips, study strategies, and product updates (optional)

[Create Account]

---
Already have an account? [Log In]
```

**Post-Registration Flow**:
1. Email verification sent
2. If Free: Immediate access
3. If Plus/Premium: Enter payment info → Start 7-day trial → Access granted
4. Onboarding wizard: Select interests, watch tutorial video

---

#### Step 2B: Parent Registration

```
Create Your Parent Account

You'll be able to manage accounts for your children.

Parent Email: [Input]
Password: [Input]
Confirm Password: [Input]

Parent Name: [Input]

How many children will use Vividly?
[Dropdown: 1, 2, 3, 4+]

Select Your Plan:
[Plan cards tailored for parents]

[FREE - $0/month]
  Per child:
  - 5 videos/month
  - Standard quality
  [Start Free]

[PLUS - $4.99/month per child]
  Per child:
  - 25 videos/month
  - HD quality
  - No ads
  [Start Trial]

[FAMILY - $14.99/month] ⭐ BEST VALUE
  Up to 4 children:
  - All Premium features
  - Parent dashboard
  - Save 25% vs individual Premium
  [Start 7-Day Free Trial]

[Create Account]

---
Next Step: You'll add your children's profiles and select their grade levels.
```

---

#### Step 2C: Teacher Registration

```
Create Your Teacher Account

Email: [Input]
Password: [Input]

First Name: [Input]
Last Name: [Input]

School:
  [Search for your school: e.g., "Lincoln High School, CA"]
  [Request to join school's organization]

  OR

  [My school isn't on Vividly yet]
  → We'll help you get your school set up with a free trial

Grade/Subject: [Input, e.g., "10th Grade Biology"]

[Create Account]

---
Teacher Benefits:
✓ Free Premium account (for verification purposes)
✓ Manage class rosters
✓ Assign content to students
✓ Track student progress
✓ Request school-wide access
```

---

## Billing & Payment

### Payment Methods

**Individual Plans** (Free, Plus, Premium, Family):
- Credit/Debit card (Stripe)
- PayPal
- Apple Pay / Google Pay (mobile)
- Gift cards (future)

**Organization Plans**:
- Invoice (NET 30, for schools/districts)
- Credit card (for small orgs < 50 seats)
- Purchase orders (for government/education)
- ACH direct debit (for large contracts)

---

### Billing Cycles

**Monthly**:
- Charged on signup date (e.g., signup Jan 15 → next charge Feb 15)
- Prorate on upgrades (e.g., upgrade on Jan 20 → charge 1/3 of month)

**Annual**:
- Charged upfront
- 17-18% discount vs monthly
- No refunds after 14 days (pro-rata refund within 14 days)

**Organization**:
- Annual only (billed upfront or NET 30 invoice)
- Seat adjustments: Pro-rated additions, deductions apply to next renewal

---

### Upgrade/Downgrade Logic

#### Individual User Upgrades (No Org Affiliation)

**Free → Plus**:
- Immediate access to Plus features
- Charged $4.99/month starting today

**Plus → Premium**:
- Immediate access to Premium features
- Charged $5/month additional (pro-rated if mid-cycle)

**Premium → Plus** (Downgrade):
- Effective next billing cycle (finish current Premium period)
- Lose Premium features (offline downloads, unlimited videos) on downgrade date

---

#### Individual User in Organization (Hybrid Model)

**Org provides Plus, User upgrades to Premium**:
```
Current Plan: Plus (provided by school)
Target Plan: Premium

Upgrade Cost: $5/month (difference between Premium and Plus)
  = $9.99 (Premium) - ~$5 (org subsidy value)

Billing:
  - School continues paying $3/month (org seat cost)
  - Student pays $5/month (upgrade delta)

Total Revenue: $8/month for this user
```

**User Cancels Upgrade**:
- Reverts to org's base plan (Plus)
- Loses Premium-only features (offline, unlimited, analytics)
- School's seat cost unchanged

---

### Stripe Integration

```python
# Create checkout session for individual upgrade
stripe.checkout.Session.create(
    mode='subscription',
    line_items=[{
        'price': 'price_premium_monthly',  # $9.99/month
        'quantity': 1,
    }],
    customer_email=user.email,
    success_url='https://vividly.com/upgrade/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url='https://vividly.com/upgrade/cancelled',
    metadata={
        'user_id': user.user_id,
        'organization_id': user.organization_id,
        'upgrade_type': 'individual',
        'from_plan': 'org_plus',
        'to_plan': 'premium'
    }
)
```

---

## User Data Model (Enhanced)

```python
class User(Base):
    user_id: str
    email: str
    role: Enum['student', 'teacher', 'admin', 'super_admin']

    # Organization affiliation
    organization_id: str (nullable)  # NULL if individual user

    # Plan Configuration
    account_type: Enum['individual', 'organization']
    base_plan: Enum['free', 'plus', 'premium', 'family']
    # ^ For org users: plan provided by org
    # ^ For individual users: plan they're paying for

    individual_plan_override: Enum['plus', 'premium', 'family'] (nullable)
    # ^ Set when user in org upgrades individually
    # ^ Example: Org provides Plus, user upgrades to Premium → 'premium'

    effective_plan: str (computed property)
    # ^ Returns max(base_plan, individual_plan_override)
    # ^ This determines actual feature access

    # Billing
    stripe_customer_id: str (nullable)
    stripe_subscription_id: str (nullable)
    subscription_status: Enum['active', 'past_due', 'canceled', 'trialing']
    trial_ends_at: datetime (nullable)
    subscription_current_period_end: datetime (nullable)

    # Usage tracking (for Free tier limits)
    videos_generated_this_month: int (default 0)
    video_generation_reset_date: datetime

    # Feature flags
    can_individual_upgrade: bool (default True)
    # ^ Set by org admin: whether user can upgrade on their own

    @property
    def effective_plan(self) -> str:
        """Compute the plan that determines feature access."""
        if self.individual_plan_override:
            return self.individual_plan_override
        return self.base_plan

    @property
    def monthly_video_limit(self) -> int:
        """Get video generation limit based on effective plan."""
        limits = {
            'free': 5,
            'plus': 25,
            'premium': 999999,  # "unlimited"
            'family': 999999
        }
        return limits.get(self.effective_plan, 5)

    @property
    def has_priority_processing(self) -> bool:
        return self.effective_plan in ['plus', 'premium', 'family']

    @property
    def can_download_offline(self) -> bool:
        return self.effective_plan in ['premium', 'family']
```

---

### Organization Data Model (Enhanced)

```python
class Organization(Base):
    organization_id: str
    name: str
    organization_type: str

    # B2B Pricing
    org_plan: Enum['basic', 'professional', 'enterprise']
    base_user_plan: Enum['plus', 'premium']
    # ^ What plan tier do users get by default?
    # ^ Basic org → Plus users
    # ^ Professional org → Premium users

    # Seat Management
    purchased_seats: int  # e.g., 500
    active_seats: int (computed)  # e.g., 487 (users currently in org)
    available_seats: int (computed)  # purchased_seats - active_seats

    # Individual Upgrade Policy
    allow_individual_upgrades: bool (default True)
    require_upgrade_approval: bool (default False)
    # ^ If True, admin/teacher must approve user upgrade requests

    allowed_upgrade_tiers: List[str] (default ['premium', 'family'])
    # ^ Which plans can users upgrade to individually?

    # Billing
    stripe_subscription_id: str
    billing_email: str
    per_seat_cost: Decimal  # e.g., $3.00 for Basic plan
    monthly_cost: Decimal (computed)  # purchased_seats * per_seat_cost
    next_billing_date: datetime

    # Usage Analytics (for billing)
    total_videos_generated_this_month: int
    active_users_this_month: int
```

---

## Frontend UI Specifications

### User Profile → Billing Section

#### For Individual Users (Not in Org)

```
Your Plan: FREE

Current Usage:
━━━━━━━░░░░░░░░ 3 of 5 videos used this month
Resets on December 1

[Upgrade to Plus] [Upgrade to Premium]

---
Upgrade Benefits:
Plus ($4.99/month):
  ✓ 25 videos/month (5x more)
  ✓ Priority processing (2x faster)
  ✓ No ads

Premium ($9.99/month):
  ✓ Unlimited videos
  ✓ Offline downloads
  ✓ Advanced analytics
  ✓ Custom content sources
```

---

#### For Org Users (Base Plan Provided)

```
Your Plan: PLUS (provided by Lincoln High School)

Current Usage:
━━━━━━━━━░░░░░░ 18 of 25 videos used this month
Resets on December 1

Features Included:
✓ 25 videos/month
✓ HD quality
✓ Priority processing
✓ No ads

[Upgrade to Premium] ← Optional individual upgrade

---
Upgrade to Premium for $5/month:
  ✓ Unlimited videos (no 25/month limit)
  ✓ Offline downloads (study anywhere)
  ✓ Advanced analytics (track mastery)
  ✓ Custom content sources (upload your notes)

Your school continues to provide your Plus plan.
You only pay for the Premium upgrade ($5/month).

[Start 7-Day Free Trial]
```

---

### Upgrade Modal (Individual Upgrade in Org)

```
Upgrade to Premium

You're currently using: Plus (provided by your school)

With Premium, you'll get:
✓ Unlimited video generations (vs 25/month)
✓ Offline downloads (up to 50 videos)
✓ Advanced learning analytics
✓ Custom content sources (upload PDFs, notes)
✓ Priority support

Pricing:
  Your school pays: $3/month (continues)
  You pay: $5/month
  Total value: Premium ($9.99/month)

[Payment Method]
Card Number: [Input]
Expiration: [MM/YY]
CVC: [Input]

[ ] I agree to recurring monthly billing

[Start 7-Day Free Trial] [Cancel]

---
You can cancel anytime. If you cancel, you'll return to your
school's Plus plan (you won't lose access completely).
```

---

## Admin Dashboard Enhancements

### Organization Admin View

#### Seat Management

```
Organization: Lincoln High School
Plan: Basic ($3/user/month)

Seat Allocation:
━━━━━━━━━━━━━━━━░░░░ 487 of 500 seats used
Available: 13 seats

Monthly Cost: $1,461 (487 active × $3)
Next Billing: December 15, 2025

[Add More Seats] [View Invoice History]

---
Individual Upgrades:
52 users have upgraded to Premium individually
Additional Revenue (not billed to you): $260/month

Top Upgraders:
  1. Sarah Johnson (12th Grade) - Premium since Sep 2025
  2. Mike Chen (11th Grade) - Premium since Oct 2025
  3. Emily Rodriguez (12th Grade) - Premium since Oct 2025

[View All Upgrades]
```

---

#### User Management

```
Users (487)

[Search users...] [Filter: All | Free | Plus | Premium]

Name              Grade  Plan      Individual Upgrade?  Actions
─────────────────────────────────────────────────────────────────
John Doe          10th   Plus      -                    [Edit] [Remove]
Sarah Johnson     12th   Premium   ✓ Premium ($5/mo)    [Edit] [Remove]
Mike Chen         11th   Premium   ✓ Premium ($5/mo)    [Edit] [Remove]
Lisa Wang         9th    Plus      -                    [Edit] [Remove]

[Add User] [Bulk Import (CSV)]
```

---

### Super Admin Dashboard

#### Revenue Analytics

```
Platform Revenue (November 2025)

Individual Plans:
  Free: 15,234 users (ad revenue: $7,617)
  Plus: 3,456 users × $4.99 = $17,245/month
  Premium: 987 users × $9.99 = $9,861/month
  Family: 234 families × $14.99 = $3,508/month

  Total B2C: $38,231/month

Organization Plans:
  Basic: 12 orgs, 6,543 seats × $3 = $19,629/month
  Professional: 5 orgs, 3,287 seats × $7 = $23,009/month
  Enterprise: 2 orgs (custom pricing) = $35,000/month

  Total B2B: $77,638/month

Individual Upgrades (within orgs):
  567 users upgraded to Premium = $2,835/month

Total MRR: $118,704/month
ARR: $1,424,448/year

[View Detailed Breakdown] [Export Report]
```

---

## Success Metrics & KPIs

### Acquisition Metrics
- **Free Signups**: Target 10,000/month (viral growth)
- **Free → Paid Conversion**: Target 5% within 90 days
- **Trial → Paid Conversion**: Target 40% (7-day trial)

### Monetization Metrics
- **ARPU (Average Revenue Per User)**: Target $3.50 (blended B2C + B2B)
- **LTV (Lifetime Value)**: Target $120 (based on 24-month retention)
- **CAC (Customer Acquisition Cost)**: Target < $15 (SEO, content marketing, referrals)
- **LTV:CAC Ratio**: Target > 8:1

### Org Metrics
- **Seat Utilization**: % of purchased seats actively used (Target: > 85%)
- **Individual Upgrade Rate**: % of org users who upgrade (Target: 10-15%)
- **Org Retention**: Annual renewal rate (Target: > 90% for Basic, > 95% for Professional)

### Engagement Metrics
- **Videos Generated/User/Month**: Target 8 (Free: 4, Plus: 15, Premium: 25)
- **DAU/MAU Ratio**: Target > 30% (sticky product)
- **Video Completion Rate**: % of videos watched to end (Target: > 80%)

---

## Implementation Checklist

### Phase 1: Pricing Infrastructure (Weeks 1-2)
- [ ] Extend User model with plan fields (base_plan, individual_plan_override)
- [ ] Extend Organization model with upgrade policies
- [ ] Create SubscriptionPlan model (plan tiers, features, pricing)
- [ ] Build plan entitlement service (check user.can_download_offline, etc.)

### Phase 2: Stripe Integration (Weeks 3-4)
- [ ] Stripe customer creation on user signup
- [ ] Subscription creation for Plus/Premium/Family
- [ ] Webhook handlers (subscription.created, payment_succeeded, payment_failed)
- [ ] Pro-rated upgrade/downgrade logic
- [ ] Invoice generation for organizations

### Phase 3: Public Signup Flow (Weeks 5-6)
- [ ] Public registration page (student, parent, teacher paths)
- [ ] Plan selection UI (Free, Plus, Premium, Family cards)
- [ ] Stripe Checkout integration (7-day trial for paid plans)
- [ ] Email verification flow
- [ ] Onboarding wizard (interests, tutorial)

### Phase 4: Upgrade Flows (Weeks 7-8)
- [ ] Individual user upgrade modal (Free → Plus → Premium)
- [ ] Org user upgrade modal (Org plan → Premium)
- [ ] Billing section in user profile
- [ ] Usage meter (X of Y videos this month)
- [ ] Upgrade prompts when hitting limits

### Phase 5: Admin Dashboards (Weeks 9-10)
- [ ] Org admin seat management UI
- [ ] Org admin user management (view upgrades)
- [ ] Super admin revenue analytics dashboard
- [ ] Invoice management for orgs
- [ ] Usage reports (videos generated, engagement)

---

## Pricing Strategy Rationale

### Why These Price Points?

**Free Tier ($0)**:
- **Goal**: Viral growth, market penetration, SEO traffic
- **Benchmark**: Quizlet, Khan Academy (freemium education)
- **Conversion**: 5% convert to paid (industry standard for freemium SaaS)

**Plus Tier ($4.99)**:
- **Goal**: Affordable for students, remove ads, prioritize users
- **Benchmark**: Spotify Student ($4.99), YouTube Premium Student ($6.99)
- **Psychology**: Under $5 = impulse purchase territory

**Premium Tier ($9.99)**:
- **Goal**: Power users, competitive with tutoring ($15-50/hour offline)
- **Benchmark**: Grammarly Premium ($12), Notion Plus ($10)
- **Value**: Unlimited videos = no anxiety about usage

**Family Tier ($14.99)**:
- **Goal**: Households with multiple students (average 2.5 students per US household with kids)
- **Benchmark**: YouTube Family ($22.99), Spotify Family ($16.99)
- **Savings**: 25% off vs 2 Premium accounts

**Org Basic ($3/user/month)**:
- **Goal**: Affordable for schools (avg $50-100/student/year for edtech)
- **Benchmark**: Google Workspace Education ($3-5/user), Canvas LMS ($5-10/user)
- **Margin**: 40% gross margin (LTV:CAC > 8:1)

**Org Professional ($7/user/month)**:
- **Goal**: Full-featured for districts with budgets
- **Benchmark**: Learning management systems ($10-15/user)
- **Features**: SSO, API, analytics justify 2.3x price vs Basic

---

## Competitive Analysis

### Direct Competitors

**Khan Academy** (Freemium):
- 100% free (nonprofit model)
- Video library (pre-made content, not personalized)
- Our advantage: Personalized content, RAG-based, user-generated queries

**Quizlet** ($7.99/month Plus):
- Flashcards + study tools
- Our advantage: Video explanations > flashcards, deeper learning

**Chegg** ($19.95/month):
- Textbook solutions, Q&A
- Our advantage: Lower cost, AI-generated explanations (faster), no copyright issues

**Course Hero** ($39.95/month):
- Study guides, document library
- Our advantage: 1/4 the price, personalized videos, cleaner UX

### Market Positioning

**Vividly is positioned as**:
- Premium alternative to Khan Academy (personalized vs one-size-fits-all)
- Affordable alternative to Chegg/Course Hero (40-60% cheaper)
- Complementary to LMS (Canvas, Google Classroom) via API integrations

---

## Risk Mitigation

### Risk 1: Free Tier Abuse
**Risk**: Users create multiple free accounts to bypass 5-video limit.

**Mitigation**:
- Require email verification (one email = one account)
- Device fingerprinting (limit accounts per device)
- Rate limiting (max 1 account creation per IP per day)
- CAPTCHA on signup

---

### Risk 2: Low Free → Paid Conversion
**Risk**: < 5% of free users convert to paid.

**Mitigation**:
- A/B test limit variations (3, 5, 7 videos/month)
- Strategic prompts (upgrade after 4th video: "You're 1 away from your limit!")
- Onboarding email sequence (Day 3: "Here's what Plus unlocks", Day 7: "Special offer")
- Referral rewards (refer 3 friends → get 1 month Plus free)

---

### Risk 3: Org Pushback on Individual Upgrades
**Risk**: Schools view individual upgrades as inequitable.

**Mitigation**:
- Make `allow_individual_upgrades` configurable (schools can disable)
- Offer scholarship program (50 Premium seats per school for low-income students)
- Frame as "enrichment, not requirement" (Premium for AP prep, test prep)

---

## Future Enhancements (12-18 Months)

### 1. Gifting & Scholarships
- Gift Premium to a friend (1 month, 3 months, 1 year)
- Scholarship application (low-income students apply for free Premium)
- Teacher-sponsored upgrades (teacher pays for top students)

### 2. Usage-Based Pricing (Alternative Model)
- Pay-per-video ($0.50/video, no monthly fee)
- Video packs (20 videos for $8 = $0.40/video)
- Appeal to infrequent users

### 3. B2B Add-Ons
- Custom content ingestion ($500/month, we ingest your curriculum)
- Dedicated support ($2,000/month, 24/7 live chat)
- Professional development ($5,000/year, train teachers on platform)

### 4. Marketplace
- Student-created content (sell study guides, notes)
- Teacher-created lessons (pay teachers for popular content)
- Revenue split: 70% creator, 30% Vividly

---

## Conclusion

This pricing & monetization strategy positions Vividly for:

1. **Viral Growth**: Free tier drives acquisition (10,000+ signups/month)
2. **Revenue Diversification**: B2C ($38K/month) + B2B ($77K/month) + Upgrades ($3K/month)
3. **Market Fit**: Competitive pricing vs incumbents (Chegg, Course Hero)
4. **Scalability**: Hybrid model allows both individual and org revenue streams
5. **Flexibility**: Orgs control upgrade policies to match their values

**Projected MRR at Scale** (18 months):
- 50,000 individual users (5% paid) = $125,000/month
- 50 organizations (10,000 seats avg) = $150,000/month
- 1,000 individual upgrades = $5,000/month
- **Total MRR: $280,000/month = $3.36M ARR**

With proper execution, Vividly can achieve **$5M ARR within 24 months** by focusing on K-12 public platform growth and strategic B2B partnerships with school districts.

---

**Document Created**: 2025-11-03
**Author**: Andrew Ng's Strategic Business Analysis
**Version**: 1.0
**Status**: Ready for Product/Finance Review
