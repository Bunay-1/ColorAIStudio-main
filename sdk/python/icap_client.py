"""
ICAP Enterprise Python Client SDK
================================
Python SDK for interacting with ICAP Enterprise API.
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("ICAP_Client")

@dataclass
class ICAPConfig:
    """ICAP client configuration."""
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    tenant_id: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True

class ICAPClient:
    """Main ICAP client for API interactions."""
    
    def __init__(self, config: ICAPConfig):
        """
        Initialize ICAP client.
        
        Args:
            config: ICAP configuration
        """
        self.config = config
        self.session = requests.Session()
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with ICAP API."""
        if self.config.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.config.api_key}"})
        elif self.config.username and self.config.password:
            try:
                response = self.session.post(
                    f"{self.config.base_url}/auth/login",
                    json={
                        "username": self.config.username,
                        "password": self.config.password
                    },
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                response.raise_for_status()
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                logger.info("Authentication successful")
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                raise
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated request to ICAP API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
        
        Returns:
            Response data
        """
        url = f"{self.config.base_url}{endpoint}"
        
        # Add tenant header if configured
        if self.config.tenant_id:
            self.session.headers.update({"X-Tenant-ID": self.config.tenant_id})
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    # Authentication
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login to ICAP API.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            Login response with token
        """
        return self._request("POST", "/auth/login", json={
            "username": username,
            "password": password
        })
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            New token response
        """
        return self._request("POST", "/auth/refresh", json={
            "refresh_token": refresh_token
        })
    
    def logout(self) -> Dict[str, Any]:
        """Logout from ICAP API."""
        return self._request("POST", "/auth/logout")
    
    # Color Analysis
    def analyze_color(self, lab_values: List[float], method: str = "delta_e_2000") -> Dict[str, Any]:
        """
        Analyze color values.
        
        Args:
            lab_values: LAB color values [L, a, b]
            method: Analysis method (delta_e_2000, delta_e_76, etc.)
        
        Returns:
            Color analysis results
        """
        return self._request("POST", "/color/analyze", json={
            "lab_values": lab_values,
            "method": method
        })
    
    def predict_trend(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict color trend from historical data.
        
        Args:
            historical_data: Historical color measurements
        
        Returns:
            Trend prediction results
        """
        return self._request("POST", "/color/trend", json={
            "historical_data": historical_data
        })
    
    # Vision Analysis
    def detect_defects(self, image_path: str) -> Dict[str, Any]:
        """
        Detect defects in image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Defect detection results
        """
        with open(image_path, 'rb') as f:
            return self._request("POST", "/vision/detect", files={"file": f})
    
    def multi_view_fusion(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Perform multi-view fusion defect detection.
        
        Args:
            image_paths: List of image file paths
        
        Returns:
            Fused detection results
        """
        files = [("files", open(path, 'rb')) for path in image_paths]
        try:
            return self._request("POST", "/vision/fusion", files=files)
        finally:
            for _, f in files:
                f.close()
    
    # RAG System
    def index_document(self, document_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Index document in RAG system.
        
        Args:
            document_path: Path to document file
            metadata: Optional metadata
        
        Returns:
            Indexing results
        """
        with open(document_path, 'rb') as f:
            return self._request("POST", "/rag/index", files={"file": f}, data={"metadata": metadata})
    
    def query_rag(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query RAG system.
        
        Args:
            query: Query string
            top_k: Number of top results
        
        Returns:
            Query results
        """
        return self._request("POST", "/rag/query", json={
            "query": query,
            "top_k": top_k
        })
    
    # Notifications
    def create_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a notification.
        
        Args:
            notification: Notification data
        
        Returns:
            Created notification
        """
        return self._request("POST", "/notifications", json=notification)
    
    def list_notifications(self, limit: int = 50) -> Dict[str, Any]:
        """
        List notifications.
        
        Args:
            limit: Maximum number of notifications
        
        Returns:
            List of notifications
        """
        return self._request("GET", f"/notifications?limit={limit}")
    
    def create_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an alert.
        
        Args:
            alert: Alert data
        
        Returns:
            Created alert
        """
        return self._request("POST", "/notifications/alerts", json=alert)
    
    # Analytics
    def get_metrics(self, metric_type: str, period: str = "24h") -> Dict[str, Any]:
        """
        Get analytics metrics.
        
        Args:
            metric_type: Type of metric (color_analysis, user_activity, etc.)
            period: Time period (24h, 7d, 30d)
        
        Returns:
            Metrics data
        """
        return self._request("GET", f"/analytics/metrics/{metric_type}?period={period}")
    
    def generate_report(self, report_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate analytics report.
        
        Args:
            report_type: Type of report
            params: Report parameters
        
        Returns:
            Generated report
        """
        return self._request("POST", "/analytics/reports", json={
            "report_type": report_type,
            "params": params
        })
    
    # Webhooks
    def create_webhook(self, webhook: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a webhook.
        
        Args:
            webhook: Webhook data
        
        Returns:
            Created webhook
        """
        return self._request("POST", "/webhooks", json=webhook)
    
    def list_webhooks(self) -> Dict[str, Any]:
        """List webhooks."""
        return self._request("GET", "/webhooks")
    
    def trigger_webhook_event(self, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a webhook event.
        
        Args:
            event: Event type
            payload: Event payload
        
        Returns:
            Trigger results
        """
        return self._request("POST", "/webhooks/trigger", json={
            "event": event,
            "payload": payload
        })
    
    # Compliance
    def generate_compliance_report(self, standard: str, title: str, description: str) -> Dict[str, Any]:
        """
        Generate compliance report.
        
        Args:
            standard: Compliance standard (gdpr, soc2, hipaa, etc.)
            title: Report title
            description: Report description
        
        Returns:
            Generated compliance report
        """
        return self._request("POST", "/compliance/reports", json={
            "standard": standard,
            "title": title,
            "description": description,
            "period_start": datetime.now().isoformat(),
            "period_end": datetime.now().isoformat()
        })
    
    def list_compliance_reports(self) -> Dict[str, Any]:
        """List compliance reports."""
        return self._request("GET", "/compliance/reports")
    
    # Export/Import
    def export_data(self, data_type: str, format: str = "json", filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Export data.
        
        Args:
            data_type: Type of data to export
            format: Export format
            filters: Optional filters
        
        Returns:
            Exported data
        """
        return self._request("POST", "/export-import/export", json={
            "data_type": data_type,
            "format": format,
            "filters": filters or {}
        })
    
    def import_data(self, data_type: str, data: str, format: str = "json", overwrite: bool = False) -> Dict[str, Any]:
        """
        Import data.
        
        Args:
            data_type: Type of data to import
            data: Data to import
            format: Import format
            overwrite: Whether to overwrite existing data
        
        Returns:
            Import results
        """
        return self._request("POST", "/export-import/import", json={
            "data_type": data_type,
            "format": format,
            "data": data,
            "overwrite": overwrite
        })
    
    # Multi-Factor Authentication
    def setup_mfa(self) -> Dict[str, Any]:
        """Set up MFA for current user."""
        return self._request("POST", "/mfa/setup")
    
    def enable_mfa(self, secret: str, verification_code: str) -> Dict[str, Any]:
        """
        Enable MFA for current user.
        
        Args:
            secret: TOTP secret
            verification_code: Verification code
        
        Returns:
            Enable results
        """
        return self._request("POST", "/mfa/enable", json={
            "secret": secret,
            "verification_code": verification_code
        })
    
    def verify_mfa(self, code: str, method: str = "totp") -> Dict[str, Any]:
        """
        Verify MFA code.
        
        Args:
            code: MFA code
            method: MFA method
        
        Returns:
            Verification results
        """
        return self._request("POST", "/mfa/verify", json={
            "code": code,
            "method": method
        })
    
    def disable_mfa(self) -> Dict[str, Any]:
        """Disable MFA for current user."""
        return self._request("POST", "/mfa/disable")
    
    # Cache Management
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._request("GET", "/cache/statistics")
    
    def clear_cache(self, level: str = "memory") -> Dict[str, Any]:
        """
        Clear cache.
        
        Args:
            level: Cache level (memory, disk)
        
        Returns:
            Clear results
        """
        return self._request("POST", f"/cache/clear?level={level}")
    
    def invalidate_cache_pattern(self, pattern: str) -> Dict[str, Any]:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Key pattern
        
        Returns:
            Invalidation results
        """
        return self._request("DELETE", f"/cache/invalidate?pattern={pattern}")
    
    def close(self):
        """Close the session."""
        self.session.close()
