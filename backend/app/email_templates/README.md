# Email Templates

HTML email templates for Vividly user communications.

## Templates

### 1. Student Invitation (`student_invitation.html`)

**Purpose**: Sent when a teacher invites a student to join a class

**Variables**:
- `{{ student_name }}` - Student's full name
- `{{ teacher_name }}` - Inviting teacher's name
- `{{ class_name }}` - Class name
- `{{ activation_link }}` - Account activation URL
- `{{ student_email }}` - Student's email address
- `{{ temp_password }}` - Temporary password

**Usage**:
```python
from app.services.email_service import send_student_invitation

send_student_invitation(
    student_email="john.doe@student.example.com",
    student_name="John Doe",
    teacher_name="Ms. Smith",
    class_name="Physics 101",
    temp_password="TempPass123!"
)
```

---

### 2. Teacher Welcome (`teacher_welcome.html`)

**Purpose**: Sent when a new teacher account is created

**Variables**:
- `{{ teacher_name }}` - Teacher's full name
- `{{ organization_name }}` - School/district name
- `{{ dashboard_link }}` - Teacher dashboard URL
- `{{ help_center_link }}` - Help center URL

**Usage**:
```python
from app.services.email_service import send_teacher_welcome

send_teacher_welcome(
    teacher_email="teacher@example.com",
    teacher_name="Jane Smith",
    organization_name="Hillsboro High School"
)
```

---

### 3. Admin Welcome (`admin_welcome.html`)

**Purpose**: Sent when a new administrator account is created

**Variables**:
- `{{ admin_name }}` - Admin's full name
- `{{ organization_name }}` - School/district name
- `{{ admin_dashboard_link }}` - Admin dashboard URL

**Usage**:
```python
from app.services.email_service import send_admin_welcome

send_admin_welcome(
    admin_email="admin@example.com",
    admin_name="Dr. Johnson",
    organization_name="Davidson County Metro Schools"
)
```

---

### 4. Password Reset (`password_reset.html`)

**Purpose**: Sent when a user requests a password reset

**Variables**:
- `{{ user_name }}` - User's full name
- `{{ user_email }}` - User's email address
- `{{ reset_link }}` - Password reset URL (expires in 1 hour)

**Usage**:
```python
from app.services.email_service import send_password_reset

send_password_reset(
    user_email="user@example.com",
    user_name="John Doe",
    reset_token="abc123..."
)
```

---

### 5. Content Ready (`content_ready.html`)

**Purpose**: Sent when a personalized video is ready for viewing

**Variables**:
- `{{ student_name }}` - Student's full name
- `{{ video_title }}` - Video title
- `{{ subject }}` - Subject (Physics, Chemistry, Biology, CS)
- `{{ topic }}` - Specific topic
- `{{ duration }}` - Video duration in minutes
- `{{ primary_interest }}` - Student's primary interest used for personalization
- `{{ video_link }}` - Direct link to video
- `{{ personalization_reason }}` - Explanation of why this video fits the student
- `{{ teacher_name }}` - Teacher who requested the content
- `{{ class_name }}` - Class name

**Usage**:
```python
from app.services.email_service import send_content_ready_notification

send_content_ready_notification(
    student_email="student@example.com",
    student_name="John Doe",
    video_title="Newton's Laws in Action",
    subject="Physics",
    topic="Newton's Laws of Motion",
    duration=8,
    primary_interest="Basketball",
    personalization_reason="This video uses basketball examples to explain force and motion..."
)
```

---

## Email Service Integration

Create an email service module to use these templates:

```python
# backend/app/services/email_service.py

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATES_DIR = Path(__file__).parent.parent / "email_templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

def render_template(template_name: str, **context) -> str:
    """Render email template with context variables."""
    template = jinja_env.get_template(template_name)
    return template.render(**context)

def send_email(to_email: str, subject: str, html_content: str):
    """Send HTML email via SMTP."""
    # Implementation depends on email provider (SendGrid, AWS SES, etc.)
    pass
```

---

## Testing Templates

To preview templates locally:

```bash
cd backend/app/email_templates

# Install dependencies
pip install jinja2

# Preview template
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('student_invitation.html')
print(template.render(
    student_name='John Doe',
    teacher_name='Ms. Smith',
    class_name='Physics 101',
    activation_link='https://vividly.edu/activate/abc123',
    student_email='john@example.com',
    temp_password='TempPass123!'
))
" > preview.html

# Open in browser
open preview.html
```

---

## Design Guidelines

### Colors
- **Primary Blue**: `#4C9AFF` - Primary actions, links
- **Secondary Green**: `#16A34A` - Success states (teacher)
- **Accent Purple**: `#A855F7` - AI features (admin)
- **Orange**: `#F97316` - Warnings
- **Gray Scale**: `#111827` to `#F9FAFB` - Text and backgrounds

### Typography
- **Headings**: System fonts, bold weights
- **Body Text**: 16px, line-height 1.6
- **Small Text**: 14px for metadata

### Layout
- **Max Width**: 600px (email client safe)
- **Padding**: 40px sides, responsive on mobile
- **Border Radius**: 8px for cards, 6px for buttons

### Accessibility
- Semantic HTML
- Alt text for images (when added)
- High contrast text (WCAG AA compliant)
- Responsive design for mobile

---

## Email Provider Setup

### Option 1: SendGrid

```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email_sendgrid(to_email: str, subject: str, html_content: str):
    message = Mail(
        from_email='noreply@vividly.edu',
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    response = sg.send(message)
```

### Option 2: AWS SES

```python
import boto3

def send_email_ses(to_email: str, subject: str, html_content: str):
    ses = boto3.client('ses', region_name='us-east-1')
    
    response = ses.send_email(
        Source='noreply@vividly.edu',
        Destination={'ToAddresses': [to_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': html_content}}
        }
    )
```

---

## Future Templates

Consider adding:
- **Progress Report**: Weekly student progress summaries
- **Class Summary**: Monthly class analytics for teachers
- **System Updates**: Maintenance notifications
- **Content Request Confirmation**: Acknowledge content requests
- **Achievement Unlocked**: Student milestone celebrations

---

**Last Updated**: 2025-10-28
