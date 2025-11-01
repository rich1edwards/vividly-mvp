"""
Email Notification Service (Story 3.3.1)

Handles email sending via SendGrid with template rendering and queue management.
"""
import os
import logging
import secrets
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self, sendgrid_client=None):
        """
        Initialize email service.

        Args:
            sendgrid_client: SendGrid client (optional for testing)
        """
        self.sendgrid = sendgrid_client
        self.sender_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@vividly.edu")
        self.sender_name = os.getenv("SENDGRID_FROM_NAME", "Vividly")

        # Email templates
        self.templates = {
            "welcome_student": self._get_welcome_student_template(),
            "welcome_teacher": self._get_welcome_teacher_template(),
            "welcome_admin": self._get_welcome_admin_template(),
            "password_reset": self._get_password_reset_template(),
            "content_ready": self._get_content_ready_template(),
            "account_request_approved": self._get_account_approved_template(),
            "account_request_denied": self._get_account_denied_template(),
        }

        # Track sent emails for rate limiting
        self.sent_count = {}

    def queue_email(
        self,
        recipient_email: str,
        recipient_name: str,
        template: str,
        data: Dict,
        priority: str = "normal",
    ) -> Tuple[str, str]:
        """
        Queue email for sending.

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            template: Template name
            data: Template data
            priority: Send priority (low, normal, high)

        Returns:
            Tuple of (notification_id, status)
        """
        # Generate notification ID
        notification_id = f"notif_{secrets.token_urlsafe(12)}"

        # Check rate limits
        if not self._check_rate_limit(recipient_email):
            logger.warning(f"Rate limit exceeded for {recipient_email}")
            return notification_id, "rate_limited"

        # Validate template
        if template not in self.templates:
            logger.error(f"Unknown template: {template}")
            return notification_id, "invalid_template"

        # In production, queue to Redis/Pub/Sub for async processing
        # For now, send immediately
        try:
            success = self._send_email(
                notification_id=notification_id,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                template=template,
                data=data,
            )

            status = "queued" if success else "failed"
            logger.info(f"Email {notification_id} {status} for {recipient_email}")
            return notification_id, status

        except Exception as e:
            logger.error(f"Failed to queue email: {e}")
            return notification_id, "failed"

    def send_batch(self, notifications: List[Dict]) -> Tuple[str, int, int, List[str]]:
        """
        Send batch of email notifications.

        Args:
            notifications: List of notification dicts

        Returns:
            Tuple of (batch_id, queued_count, failed_count, notification_ids)
        """
        batch_id = f"batch_{secrets.token_urlsafe(8)}"
        notification_ids = []
        queued_count = 0
        failed_count = 0

        for notif in notifications:
            notif_id, status = self.queue_email(
                recipient_email=notif["recipient"]["email"],
                recipient_name=notif["recipient"]["name"],
                template=notif["template"],
                data=notif.get("data", {}),
                priority=notif.get("priority", "normal"),
            )

            notification_ids.append(notif_id)

            if status in ["queued", "sending"]:
                queued_count += 1
            else:
                failed_count += 1

        logger.info(f"Batch {batch_id}: {queued_count} queued, {failed_count} failed")
        return batch_id, queued_count, failed_count, notification_ids

    def get_status(self, notification_id: str) -> Dict:
        """
        Get notification delivery status.

        Args:
            notification_id: Notification ID

        Returns:
            Dict with status information
        """
        # In production, query from database/tracking system
        # For now, return mock status
        return {
            "notification_id": notification_id,
            "status": "delivered",
            "sent_at": datetime.utcnow().isoformat() + "Z",
            "delivered_at": (datetime.utcnow() + timedelta(seconds=2)).isoformat()
            + "Z",
            "opened_at": None,
            "clicked_at": None,
            "error_message": None,
        }

    def _send_email(
        self,
        notification_id: str,
        recipient_email: str,
        recipient_name: str,
        template: str,
        data: Dict,
    ) -> bool:
        """
        Send email via SendGrid.

        Args:
            notification_id: Notification ID
            recipient_email: Recipient email
            recipient_name: Recipient name
            template: Template name
            data: Template data

        Returns:
            bool: True if sent successfully
        """
        try:
            # Render template
            subject, html_body = self._render_template(template, data)

            if not self.sendgrid:
                # Mock sending for testing
                logger.info(f"Mock send to {recipient_email}: {subject}")
                return True

            # In production, send via SendGrid:
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail
            #
            # message = Mail(
            #     from_email=(self.sender_email, self.sender_name),
            #     to_emails=recipient_email,
            #     subject=subject,
            #     html_content=html_body
            # )
            #
            # response = self.sendgrid.send(message)
            # return response.status_code == 202

            return True

        except Exception as e:
            logger.error(f"Failed to send email {notification_id}: {e}")
            return False

    def _render_template(self, template_name: str, data: Dict) -> Tuple[str, str]:
        """
        Render email template.

        Args:
            template_name: Template name
            data: Template data

        Returns:
            Tuple of (subject, html_body)
        """
        template_config = self.templates.get(template_name)
        if not template_config:
            raise ValueError(f"Unknown template: {template_name}")

        subject = Template(template_config["subject"]).render(**data)
        html_body = Template(template_config["html"]).render(**data)

        return subject, html_body

    def _check_rate_limit(self, email: str) -> bool:
        """
        Check if email is within rate limits.

        Args:
            email: Email address

        Returns:
            bool: True if within limits
        """
        # Simple rate limiting: max 10 emails per hour per address
        now = datetime.utcnow()
        hour_key = now.strftime("%Y-%m-%d-%H")
        key = f"{email}:{hour_key}"

        count = self.sent_count.get(key, 0)
        if count >= 10:
            return False

        self.sent_count[key] = count + 1
        return True

    # Email Templates

    def _get_welcome_student_template(self) -> Dict:
        """Get welcome email template for students."""
        return {
            "subject": "Welcome to Vividly! 🎓",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #4F46E5;">Welcome to Vividly, {{ name }}!</h1>
                    <p>We're excited to help you learn through personalized, interest-based content.</p>

                    <h2>Get Started:</h2>
                    <ol>
                        <li>Complete your interest profile</li>
                        <li>Browse available topics</li>
                        <li>Watch your first personalized video</li>
                    </ol>

                    <a href="{{ activation_link }}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
                        Activate Your Account
                    </a>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        If you have questions, reply to this email or contact support.
                    </p>
                </body>
                </html>
            """,
        }

    def _get_welcome_teacher_template(self) -> Dict:
        """Get welcome email template for teachers."""
        return {
            "subject": "Welcome to Vividly - Teacher Account",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #4F46E5;">Welcome, {{ name }}!</h1>
                    <p>Your teacher account is ready. You can now:</p>

                    <ul>
                        <li>Create and manage classes</li>
                        <li>Request student accounts</li>
                        <li>Track student progress</li>
                        <li>Assign content to students</li>
                    </ul>

                    <a href="{{ activation_link }}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
                        Access Your Dashboard
                    </a>
                </body>
                </html>
            """,
        }

    def _get_welcome_admin_template(self) -> Dict:
        """Get welcome email template for admins."""
        return {
            "subject": "Vividly Admin Account Created",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #4F46E5;">Admin Access Granted</h1>
                    <p>Hi {{ name }},</p>
                    <p>Your administrator account has been created.</p>

                    <a href="{{ activation_link }}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
                        Access Admin Panel
                    </a>
                </body>
                </html>
            """,
        }

    def _get_password_reset_template(self) -> Dict:
        """Get password reset email template."""
        return {
            "subject": "Reset Your Vividly Password",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #4F46E5;">Password Reset Request</h1>
                    <p>Hi {{ name }},</p>
                    <p>You requested to reset your password. Click the button below to create a new password:</p>

                    <a href="{{ reset_link }}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
                        Reset Password
                    </a>

                    <p style="color: #666; font-size: 14px;">This link expires in 1 hour.</p>
                    <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                </body>
                </html>
            """,
        }

    def _get_content_ready_template(self) -> Dict:
        """Get content ready notification template."""
        return {
            "subject": "Your Personalized Video is Ready! 🎬",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #4F46E5;">New Content Ready!</h1>
                    <p>Hi {{ name }},</p>
                    <p>Your personalized video for <strong>{{ topic_name }}</strong> ({{ interest }} edition) is ready to watch!</p>

                    <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <img src="{{ thumbnail_url }}" alt="Video thumbnail" style="width: 100%; border-radius: 6px;">
                        <h2 style="margin-top: 10px;">{{ topic_name }}</h2>
                        <p style="color: #666;">Personalized for: {{ interest }}</p>
                    </div>

                    <a href="{{ video_url }}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
                        Watch Now
                    </a>
                </body>
                </html>
            """,
        }

    def _get_account_approved_template(self) -> Dict:
        """Get account request approved template."""
        return {
            "subject": "Account Approved - Welcome to Vividly!",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #10B981;">Account Approved!</h1>
                    <p>Hi {{ student_name }},</p>
                    <p>Your account request has been approved by {{ approver_name }}.</p>

                    <a href="{{ activation_link }}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
                        Activate Account
                    </a>

                    <p>Class: {{ class_name }}</p>
                    <p>Teacher: {{ teacher_name }}</p>
                </body>
                </html>
            """,
        }

    def _get_account_denied_template(self) -> Dict:
        """Get account request denied template."""
        return {
            "subject": "Account Request - Action Required",
            "html": """
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #EF4444;">Account Request Update</h1>
                    <p>Hi {{ teacher_name }},</p>
                    <p>The account request for <strong>{{ student_name }}</strong> requires your attention.</p>

                    <p>Reason: {{ reason }}</p>

                    <p style="color: #666; font-size: 14px;">
                        Please contact your administrator if you have questions.
                    </p>
                </body>
                </html>
            """,
        }
