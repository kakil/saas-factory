"""
Email utility service.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any

from fastapi import BackgroundTasks
from jinja2 import Template

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails
    """
    
    def __init__(self):
        """Initialize the email service"""
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        self.use_tls = settings.SMTP_TLS
        
    def _create_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> MIMEMultipart:
        """
        Create an email message.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            
        Returns:
            The email message
        """
        message = MIMEMultipart()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
            
        if is_html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
            
        return message
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            
        Returns:
            Whether the email was sent successfully
        """
        if not self.host or not self.port:
            logger.warning("SMTP server not configured, unable to send email")
            return False
            
        try:
            message = self._create_message(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
                cc=cc,
                bcc=bcc,
            )
            
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(
                    self.from_email,
                    recipients,
                    message.as_string()
                )
                
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def render_template(
        self,
        template_str: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Render a template string with the given context.
        
        Args:
            template_str: The template string
            context: The context for template rendering
            
        Returns:
            The rendered template
        """
        template = Template(template_str)
        return template.render(**context)
    
    async def send_email_async(
        self,
        background_tasks: BackgroundTasks,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> None:
        """
        Send an email asynchronously using background tasks.
        
        Args:
            background_tasks: FastAPI background tasks
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
        """
        background_tasks.add_task(
            self.send_email,
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html,
            cc=cc,
            bcc=bcc,
        )
        
    async def send_template_email_async(
        self,
        background_tasks: BackgroundTasks,
        to_email: str,
        subject: str,
        template_str: str,
        context: Dict[str, Any],
        is_html: bool = True,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> None:
        """
        Render a template and send it as an email asynchronously.
        
        Args:
            background_tasks: FastAPI background tasks
            to_email: Recipient email address
            subject: Email subject
            template_str: The template string
            context: The context for template rendering
            is_html: Whether the template is HTML
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
        """
        body = self.render_template(template_str, context)
        await self.send_email_async(
            background_tasks=background_tasks,
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html,
            cc=cc,
            bcc=bcc,
        )


# Create a singleton instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """
    Get the email service instance.
    
    Returns:
        The email service
    """
    return email_service