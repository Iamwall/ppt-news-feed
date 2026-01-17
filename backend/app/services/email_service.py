"""Email sending service."""
from typing import List, Optional
import asyncio

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


class EmailService:
    """Service for sending newsletter emails."""
    
    def __init__(self):
        self.use_sendgrid = bool(settings.sendgrid_api_key)
        
        if self.use_sendgrid:
            self.sg_client = SendGridAPIClient(settings.sendgrid_api_key)
    
    async def send_newsletter(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> List[dict]:
        """Send newsletter to recipients."""
        results = []
        
        for recipient in recipients:
            try:
                if self.use_sendgrid:
                    await self._send_via_sendgrid(
                        recipient, subject, html_content, text_content
                    )
                else:
                    await self._send_via_smtp(
                        recipient, subject, html_content, text_content
                    )
                results.append({"email": recipient, "success": True})
            except Exception as e:
                results.append({"email": recipient, "success": False, "error": str(e)})
        
        return results
    
    async def _send_via_sendgrid(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
    ):
        """Send email via SendGrid."""
        message = Mail(
            from_email=settings.email_from,
            to_emails=recipient,
            subject=subject,
            html_content=html_content,
        )
        
        if text_content:
            message.add_content(Content("text/plain", text_content))
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.sg_client.send(message)
        )
    
    async def _send_via_smtp(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
    ):
        """Send email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = recipient
        
        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        
        msg.attach(MIMEText(html_content, "html"))
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._smtp_send(msg, recipient)
        )
    
    def _smtp_send(self, msg: MIMEMultipart, recipient: str):
        """Synchronous SMTP send."""
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, recipient, msg.as_string())
