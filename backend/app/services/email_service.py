"""Email service for sending password reset emails."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "localhost")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM", "Inner Garden <noreply@innergarden.app>")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.enabled = os.getenv("SMTP_ENABLED", "true").lower() == "true"

    def _parse_from_address(self) -> tuple[str, str]:
        """Parse SMTP_FROM into name and email address."""
        from_str = self.from_email
        if "<" in from_str and from_str.endswith(">"):
            # Format: "Name <email@example.com>"
            name = from_str[: from_str.index("<")].strip().strip('"')
            email_addr = from_str[from_str.index("<") + 1 : -1].strip()
            return name, email_addr
        return "", from_str

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text fallback (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email sending disabled. Would send to: {to_email}")
            return True  # Pretend success for development

        try:
            msg = EmailMessage()
            from_name, from_addr = self._parse_from_address()
            msg["From"] = formataddr((from_name, from_addr))
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.set_content(text_content or html_content)
            msg.add_alternative(html_content, subtype="html")

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_password_reset_email(
        self, to_email: str, username: str, reset_link: str
    ) -> bool:
        """Send a password reset email.

        Args:
            to_email: Recipient email address
            username: User's username
            reset_link: Password reset link with token

        Returns:
            True if email was sent successfully
        """
        subject = "重置您的 Inner Garden 密码"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; padding: 20px 0; border-bottom: 1px solid #eee; }}
        .header h1 {{ margin: 0; color: #8fb8ff; }}
        .content {{ padding: 30px 0; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #8fb8ff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .button:hover {{ background: #7aa0e0; }}
        .footer {{ text-align: center; padding: 20px 0; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Inner Garden</h1>
        </div>
        <div class="content">
            <p>你好，{username}，</p>
            <p>我们收到了您的密码重置请求。如果这是您本人操作，请点击下面的按钮重置密码：</p>
            <center>
                <a href="{reset_link}" class="button">重置密码</a>
            </center>
            <p>或者复制以下链接到浏览器地址栏：</p>
            <p style="word-break: break-all; color: #666; font-size: 14px;">{reset_link}</p>
            <div class="warning">
                <strong>⚠️ 重要提示：</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>此链接仅在 <strong>30 分钟内</strong> 有效</li>
                    <li>点击链接后只能使用 <strong>一次</strong></li>
                    <li>如果您没有请求重置密码，请忽略此邮件</li>
                </ul>
            </div>
            <p>祝好，<br>Inner Garden 团队</p>
        </div>
        <div class="footer">
            <p>这是一封自动发送的邮件，请直接回复。</p>
            <p>Inner Garden - 情绪日记与自我觉察工具</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
你好 {username}，

我们收到了您的密码重置请求。如果这是您本人操作，请访问以下链接重置密码：

{reset_link}

此链接在 30 分钟内有效，且只能使用一次。

如果您没有请求重置密码，请忽略此邮件。

祝好，
Inner Garden 团队
"""

        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
