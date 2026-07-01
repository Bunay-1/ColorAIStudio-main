"""
ICAP Alerting System — Push Notifications (Slack, Email, SMS)
==========================================================
Модул за изпращане на алерти при критични отклонения.
Подобрено с rate limiting, deduplication и escalation logic.
"""

import os
import json
import logging
import requests
import smtplib
import time
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("AlertingSystem")

class AlertingSystem:
    def __init__(self):
        self.slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
        self.email_config = {
            "smtp_server": os.environ.get("SMTP_SERVER"),
            "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
            "sender_email": os.environ.get("SENDER_EMAIL"),
            "sender_password": os.environ.get("SENDER_PASSWORD"),
            "recipient_email": os.environ.get("RECIPIENT_EMAIL")
        }
        # SMS API (напр. Twilio)
        self.sms_config = {
            "account_sid": os.environ.get("TWILIO_ACCOUNT_SID"),
            "auth_token": os.environ.get("TWILIO_AUTH_TOKEN"),
            "from_number": os.environ.get("TWILIO_FROM_NUMBER"),
            "to_number": os.environ.get("TWILIO_TO_NUMBER")
        }
        
        # Rate limiting
        self.rate_limits = {
            "CRITICAL": {"max_per_hour": 10, "history": deque()},
            "WARNING": {"max_per_hour": 30, "history": deque()},
            "INFO": {"max_per_hour": 60, "history": deque()}
        }
        
        # Alert deduplication (prevent duplicate alerts within time window)
        self.alert_history = defaultdict(deque)  # message_hash -> timestamps
        self.dedup_window = 300  # 5 minutes
        
        # Alert escalation
        self.escalation_counts = defaultdict(int)
        self.escalation_threshold = 3
        
        # Alert statistics
        self.alert_stats = defaultdict(int)
        self.alert_history_log = deque(maxlen=1000)

    def _generate_alert_hash(self, message: str, level: str) -> str:
        """Generate hash for alert deduplication."""
        content = f"{level}:{message}"
        return hashlib.md5(content.encode()).hexdigest()

    def _check_rate_limit(self, level: str) -> bool:
        """Check if alert should be rate limited."""
        now = time.time()
        hour_ago = now - 3600
        
        # Clean old entries
        while self.rate_limits[level]["history"] and self.rate_limits[level]["history"][0] < hour_ago:
            self.rate_limits[level]["history"].popleft()
        
        # Check limit
        if len(self.rate_limits[level]["history"]) >= self.rate_limits[level]["max_per_hour"]:
            logger.warning(f"Rate limit exceeded for {level} alerts")
            return False
        
        self.rate_limits[level]["history"].append(now)
        return True

    def _check_deduplication(self, message: str, level: str) -> bool:
        """Check if alert is a duplicate within dedup window."""
        alert_hash = self._generate_alert_hash(message, level)
        now = time.time()
        
        # Clean old entries
        if alert_hash in self.alert_history:
            while self.alert_history[alert_hash] and self.alert_history[alert_hash][0] < now - self.dedup_window:
                self.alert_history[alert_hash].popleft()
        
        # Check if duplicate
        if alert_hash in self.alert_history and len(self.alert_history[alert_hash]) > 0:
            logger.info(f"Duplicate alert suppressed: {message[:50]}...")
            return False
        
        self.alert_history[alert_hash].append(now)
        return True

    def _escalate_if_needed(self, message: str, level: str):
        """Escalate alert if threshold exceeded."""
        alert_hash = self._generate_alert_hash(message, level)
        self.escalation_counts[alert_hash] += 1
        
        if self.escalation_counts[alert_hash] >= self.escalation_threshold:
            logger.warning(f"Alert escalation triggered for: {message[:50]}...")
            # Could add escalation logic here (e.g., send to different channel)
            self.escalation_counts[alert_hash] = 0  # Reset after escalation

    def send_alert(self, message: str, level: str = "CRITICAL", force: bool = False):
        """
        Изпраща алерти през всички конфигурирани канали.
        
        Args:
            message: Alert message
            level: Alert level (CRITICAL, WARNING, INFO)
            force: Bypass rate limiting and deduplication
        """
        # Validate level
        if level not in self.rate_limits:
            level = "CRITICAL"
        
        # Rate limiting check
        if not force and not self._check_rate_limit(level):
            logger.info(f"Alert rate limited: {message[:50]}...")
            return
        
        # Deduplication check
        if not force and not self._check_deduplication(message, level):
            return
        
        # Log alert
        logger.info(f"🚨 [ALERT {level}]: {message}")
        self.alert_stats[level] += 1
        self.alert_history_log.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })
        
        # Check for escalation
        self._escalate_if_needed(message, level)

        # 1. Slack
        if self.slack_webhook:
            try:
                payload = {"text": f"*[{level}] ICAP Industrial Alert*\n{message}"}
                requests.post(self.slack_webhook, json=payload, timeout=5)
            except Exception as e:
                logger.error(f"Slack Alert Error: {e}")

        # 2. Email (only for CRITICAL and WARNING)
        if level in ["CRITICAL", "WARNING"] and all(self.email_config.values()):
            try:
                msg = MIMEMultipart()
                msg['From'] = self.email_config['sender_email']
                msg['To'] = self.email_config['recipient_email']
                msg['Subject'] = f"[{level}] ICAP Industrial Alert"
                msg.attach(MIMEText(message, 'plain'))

                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
                server.quit()
            except Exception as e:
                logger.error(f"Email Alert Error: {e}")

        # 3. SMS (only for CRITICAL)
        if level == "CRITICAL" and all(self.sms_config.values()):
            try:
                from twilio.rest import Client
                client = Client(self.sms_config['account_sid'], self.sms_config['auth_token'])
                client.messages.create(
                    body=f"[{level}] ICAP: {message}",
                    from_=self.sms_config['from_number'],
                    to=self.sms_config['to_number']
                )
            except Exception as e:
                logger.error(f"SMS Alert Error: {e}")

    def get_alert_stats(self) -> Dict:
        """Get alert statistics."""
        return {
            "total_alerts": sum(self.alert_stats.values()),
            "by_level": dict(self.alert_stats),
            "recent_alerts": list(self.alert_history_log)[-10:] if self.alert_history_log else []
        }

    def reset_stats(self):
        """Reset alert statistics."""
        self.alert_stats.clear()
        self.escalation_counts.clear()
        logger.info("Alert statistics reset")

alert_system = AlertingSystem()
