"""飞书推送"""
import requests
import logging

logger = logging.getLogger(__name__)

def send_to_feishu(webhook_url: str, content: str):
    """发送到飞书"""
    try:
        resp = requests.post(webhook_url, json={"text": content}, timeout=5)
        logger.info(f"Sent to Feishu: {resp.status_code}")
    except Exception as e:
        logger.error(f"Feishu error: {e}")
