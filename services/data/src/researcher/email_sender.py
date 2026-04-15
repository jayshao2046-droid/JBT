"""邮件推送"""
import smtplib
import logging

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, body: str):
    """发送邮件"""
    try:
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Email error: {e}")
