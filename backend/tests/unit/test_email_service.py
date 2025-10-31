"""
Unit tests for email service.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.email_service import EmailService


@pytest.mark.unit
class TestEmailServiceInitialization:
    """Test email service initialization."""

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        service = EmailService()

        assert service.sendgrid is None
        assert service.sender_email == "noreply@vividly.edu"
        assert service.sender_name == "Vividly"
        assert len(service.templates) == 7
        assert "welcome_student" in service.templates
        assert "welcome_teacher" in service.templates
        assert "password_reset" in service.templates

    def test_init_with_custom_client(self):
        """Test initialization with custom SendGrid client."""
        mock_client = Mock()
        service = EmailService(sendgrid_client=mock_client)

        assert service.sendgrid == mock_client

    @patch.dict('os.environ', {'SENDGRID_FROM_EMAIL': 'custom@example.com', 'SENDGRID_FROM_NAME': 'Custom Name'})
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        service = EmailService()

        assert service.sender_email == 'custom@example.com'
        assert service.sender_name == 'Custom Name'


@pytest.mark.unit
class TestQueueEmail:
    """Test email queueing functionality."""

    def test_queue_welcome_student_email(self):
        """Test queuing welcome email for student."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="student@test.com",
            recipient_name="Test Student",
            template="welcome_student",
            data={
                "name": "Test Student",
                "activation_link": "https://vividly.edu/activate/123"
            }
        )

        assert notif_id.startswith("notif_")
        assert status == "queued"

    def test_queue_welcome_teacher_email(self):
        """Test queuing welcome email for teacher."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="teacher@test.com",
            recipient_name="Test Teacher",
            template="welcome_teacher",
            data={
                "name": "Test Teacher",
                "activation_link": "https://vividly.edu/activate/456"
            }
        )

        assert notif_id.startswith("notif_")
        assert status == "queued"

    def test_queue_password_reset_email(self):
        """Test queuing password reset email."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="user@test.com",
            recipient_name="Test User",
            template="password_reset",
            data={
                "name": "Test User",
                "reset_link": "https://vividly.edu/reset/abc123"
            }
        )

        assert notif_id.startswith("notif_")
        assert status == "queued"

    def test_queue_content_ready_email(self):
        """Test queuing content ready notification."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="student@test.com",
            recipient_name="Student",
            template="content_ready",
            data={
                "name": "Student",
                "topic_name": "Photosynthesis",
                "interest": "Basketball",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "video_url": "https://example.com/video/123"
            }
        )

        assert notif_id.startswith("notif_")
        assert status == "queued"

    def test_queue_with_invalid_template(self):
        """Test queuing with invalid template name."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="user@test.com",
            recipient_name="User",
            template="nonexistent_template",
            data={}
        )

        assert notif_id.startswith("notif_")
        assert status == "invalid_template"

    def test_queue_with_priority(self):
        """Test queuing email with priority."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="user@test.com",
            recipient_name="User",
            template="welcome_student",
            data={"name": "User", "activation_link": "http://example.com"},
            priority="high"
        )

        assert status == "queued"

    def test_rate_limiting(self):
        """Test rate limiting prevents too many emails."""
        service = EmailService()
        email = "test@example.com"

        # Send 10 emails (rate limit)
        for i in range(10):
            notif_id, status = service.queue_email(
                recipient_email=email,
                recipient_name="User",
                template="welcome_student",
                data={"name": "User", "activation_link": "http://example.com"}
            )
            assert status == "queued"

        # 11th email should be rate limited
        notif_id, status = service.queue_email(
            recipient_email=email,
            recipient_name="User",
            template="welcome_student",
            data={"name": "User", "activation_link": "http://example.com"}
        )

        assert status == "rate_limited"


@pytest.mark.unit
class TestBatchSending:
    """Test batch email sending."""

    def test_send_batch_all_successful(self):
        """Test sending batch of emails successfully."""
        service = EmailService()

        notifications = [
            {
                "recipient": {"email": f"user{i}@test.com", "name": f"User {i}"},
                "template": "welcome_student",
                "data": {"name": f"User {i}", "activation_link": "http://example.com"}
            }
            for i in range(5)
        ]

        batch_id, queued_count, failed_count, notif_ids = service.send_batch(notifications)

        assert batch_id.startswith("batch_")
        assert queued_count == 5
        assert failed_count == 0
        assert len(notif_ids) == 5

    def test_send_batch_with_failures(self):
        """Test batch sending with some failures (invalid templates)."""
        service = EmailService()

        notifications = [
            {
                "recipient": {"email": "user1@test.com", "name": "User 1"},
                "template": "welcome_student",
                "data": {"name": "User 1", "activation_link": "http://example.com"}
            },
            {
                "recipient": {"email": "user2@test.com", "name": "User 2"},
                "template": "invalid_template",
                "data": {}
            },
            {
                "recipient": {"email": "user3@test.com", "name": "User 3"},
                "template": "welcome_teacher",
                "data": {"name": "User 3", "activation_link": "http://example.com"}
            }
        ]

        batch_id, queued_count, failed_count, notif_ids = service.send_batch(notifications)

        assert queued_count == 2
        assert failed_count == 1
        assert len(notif_ids) == 3

    def test_send_empty_batch(self):
        """Test sending empty batch."""
        service = EmailService()

        batch_id, queued_count, failed_count, notif_ids = service.send_batch([])

        assert batch_id.startswith("batch_")
        assert queued_count == 0
        assert failed_count == 0
        assert len(notif_ids) == 0

    def test_send_batch_with_priorities(self):
        """Test batch sending with different priorities."""
        service = EmailService()

        notifications = [
            {
                "recipient": {"email": "urgent@test.com", "name": "Urgent"},
                "template": "welcome_student",
                "data": {"name": "Urgent", "activation_link": "http://example.com"},
                "priority": "high"
            },
            {
                "recipient": {"email": "normal@test.com", "name": "Normal"},
                "template": "welcome_student",
                "data": {"name": "Normal", "activation_link": "http://example.com"},
                "priority": "normal"
            }
        ]

        batch_id, queued_count, failed_count, notif_ids = service.send_batch(notifications)

        assert queued_count == 2
        assert failed_count == 0


@pytest.mark.unit
class TestEmailStatus:
    """Test email status tracking."""

    def test_get_status(self):
        """Test getting email delivery status."""
        service = EmailService()

        status = service.get_status("notif_123")

        assert status["notification_id"] == "notif_123"
        assert status["status"] == "delivered"
        assert "sent_at" in status
        assert "delivered_at" in status
        assert status["opened_at"] is None
        assert status["clicked_at"] is None
        assert status["error_message"] is None


@pytest.mark.unit
class TestTemplateRendering:
    """Test email template rendering."""

    def test_render_welcome_student_template(self):
        """Test rendering welcome student template."""
        service = EmailService()

        subject, html = service._render_template(
            "welcome_student",
            {
                "name": "John Doe",
                "activation_link": "https://vividly.edu/activate/abc123"
            }
        )

        assert subject == "Welcome to Vividly! 🎓"
        assert "John Doe" in html
        assert "https://vividly.edu/activate/abc123" in html
        assert "Welcome to Vividly" in html

    def test_render_password_reset_template(self):
        """Test rendering password reset template."""
        service = EmailService()

        subject, html = service._render_template(
            "password_reset",
            {
                "name": "Jane Smith",
                "reset_link": "https://vividly.edu/reset/xyz789"
            }
        )

        assert subject == "Reset Your Vividly Password"
        assert "Jane Smith" in html
        assert "https://vividly.edu/reset/xyz789" in html

    def test_render_content_ready_template(self):
        """Test rendering content ready template."""
        service = EmailService()

        subject, html = service._render_template(
            "content_ready",
            {
                "name": "Student",
                "topic_name": "The Water Cycle",
                "interest": "Surfing",
                "thumbnail_url": "https://cdn.vividly.edu/thumb.jpg",
                "video_url": "https://vividly.edu/watch/123"
            }
        )

        assert "Your Personalized Video is Ready!" in subject
        assert "The Water Cycle" in html
        assert "Surfing" in html

    def test_render_account_approved_template(self):
        """Test rendering account approved template."""
        service = EmailService()

        subject, html = service._render_template(
            "account_request_approved",
            {
                "student_name": "Alice",
                "approver_name": "Mr. Smith",
                "activation_link": "https://vividly.edu/activate/student123",
                "class_name": "Math 101",
                "teacher_name": "Mr. Smith"
            }
        )

        assert "Account Approved" in subject
        assert "Alice" in html
        assert "Mr. Smith" in html
        assert "Math 101" in html

    def test_render_unknown_template(self):
        """Test rendering unknown template raises error."""
        service = EmailService()

        with pytest.raises(ValueError, match="Unknown template"):
            service._render_template("unknown_template", {})


@pytest.mark.unit
class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_check_within_limit(self):
        """Test rate limit check when within limits."""
        service = EmailService()

        # First email should be allowed
        assert service._check_rate_limit("test@example.com") is True

    def test_rate_limit_check_at_limit(self):
        """Test rate limit check at exactly the limit."""
        service = EmailService()
        email = "test@example.com"

        # Send 10 emails (the limit)
        for i in range(10):
            assert service._check_rate_limit(email) is True

        # 11th should be blocked
        assert service._check_rate_limit(email) is False

    def test_rate_limit_different_emails(self):
        """Test rate limiting is per email address."""
        service = EmailService()

        # Send 10 emails to first address
        for i in range(10):
            assert service._check_rate_limit("email1@test.com") is True

        # Different email should still be allowed
        assert service._check_rate_limit("email2@test.com") is True

    def test_rate_limit_hour_key_format(self):
        """Test rate limit uses hour-based keys."""
        service = EmailService()
        email = "test@example.com"

        # Check that rate limit tracking uses hour-based keys
        service._check_rate_limit(email)

        now = datetime.utcnow()
        hour_key = now.strftime("%Y-%m-%d-%H")
        expected_key = f"{email}:{hour_key}"

        assert expected_key in service.sent_count


@pytest.mark.unit
class TestEmailSending:
    """Test email sending functionality."""

    def test_send_email_without_client(self):
        """Test sending email without SendGrid client (mock mode)."""
        service = EmailService(sendgrid_client=None)

        result = service._send_email(
            notification_id="notif_123",
            recipient_email="test@example.com",
            recipient_name="Test User",
            template="welcome_student",
            data={"name": "Test User", "activation_link": "http://example.com"}
        )

        assert result is True

    def test_send_email_with_mock_client(self):
        """Test sending email with mocked SendGrid client."""
        mock_client = Mock()
        service = EmailService(sendgrid_client=mock_client)

        result = service._send_email(
            notification_id="notif_456",
            recipient_email="test@example.com",
            recipient_name="Test User",
            template="welcome_teacher",
            data={"name": "Test User", "activation_link": "http://example.com"}
        )

        assert result is True

    def test_send_email_with_invalid_template_data(self):
        """Test sending email with incomplete template data still succeeds."""
        service = EmailService()

        # Jinja2 handles missing variables gracefully (renders as empty)
        result = service._send_email(
            notification_id="notif_789",
            recipient_email="test@example.com",
            recipient_name="Test User",
            template="welcome_student",
            data={}  # Missing 'name' and 'activation_link'
        )

        # Should still succeed (Jinja2 doesn't fail on missing vars)
        assert result is True


@pytest.mark.unit
class TestAllTemplates:
    """Test all email templates are valid."""

    def test_all_templates_have_subject_and_html(self):
        """Test all templates have required fields."""
        service = EmailService()

        for template_name, template_config in service.templates.items():
            assert "subject" in template_config, f"Template {template_name} missing subject"
            assert "html" in template_config, f"Template {template_name} missing html"
            assert isinstance(template_config["subject"], str)
            assert isinstance(template_config["html"], str)
            assert len(template_config["subject"]) > 0
            assert len(template_config["html"]) > 0

    def test_welcome_admin_template_exists(self):
        """Test welcome admin template exists and is valid."""
        service = EmailService()

        template = service.templates["welcome_admin"]

        assert "subject" in template
        assert "Admin" in template["subject"]

    def test_account_denied_template_exists(self):
        """Test account denied template exists and is valid."""
        service = EmailService()

        template = service.templates["account_request_denied"]

        assert "subject" in template
        assert template["subject"] == "Account Request - Action Required"


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_queue_email_with_empty_data(self):
        """Test queuing email with minimal data."""
        service = EmailService()

        # Jinja2 handles missing variables gracefully (renders as empty)
        notif_id, status = service.queue_email(
            recipient_email="test@example.com",
            recipient_name="User",
            template="welcome_student",
            data={}
        )

        assert notif_id.startswith("notif_")
        assert status == "queued"

    def test_queue_email_with_special_characters(self):
        """Test queuing email with special characters in data."""
        service = EmailService()

        notif_id, status = service.queue_email(
            recipient_email="test@example.com",
            recipient_name="User <script>alert('xss')</script>",
            template="welcome_student",
            data={
                "name": "User <b>Bold</b>",
                "activation_link": "https://example.com"
            }
        )

        # Should still queue (Jinja2 handles escaping)
        assert status == "queued"

    def test_notification_id_uniqueness(self):
        """Test that notification IDs are unique."""
        service = EmailService()

        ids = []
        for i in range(100):
            notif_id, status = service.queue_email(
                recipient_email=f"user{i}@test.com",
                recipient_name=f"User {i}",
                template="welcome_student",
                data={"name": f"User {i}", "activation_link": "http://example.com"}
            )
            ids.append(notif_id)

        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_batch_id_uniqueness(self):
        """Test that batch IDs are unique."""
        service = EmailService()

        batch_ids = []
        for i in range(50):
            batch_id, _, _, _ = service.send_batch([])
            batch_ids.append(batch_id)

        # All batch IDs should be unique
        assert len(batch_ids) == len(set(batch_ids))
