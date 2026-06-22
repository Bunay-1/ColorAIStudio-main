"""
Advanced Analytics and Reporting Service for ICAP Enterprise
============================================================
Comprehensive analytics and reporting capabilities for business intelligence.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

logger = logging.getLogger("Analytics_Service")

class ReportType(str, Enum):
    """Report types."""
    COLOR_ANALYSIS = "color_analysis"
    VISION_ANALYSIS = "vision_analysis"
    USER_ACTIVITY = "user_activity"
    TENANT_USAGE = "tenant_usage"
    SYSTEM_PERFORMANCE = "system_performance"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    """Report output formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"

class TimePeriod(str, Enum):
    """Time periods for analytics."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

@dataclass
class AnalyticsMetric:
    """Analytics metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Report:
    """Report data structure."""
    id: str
    type: ReportType
    title: str
    description: str
    period: TimePeriod
    start_date: str
    end_date: str
    metrics: List[AnalyticsMetric]
    created_by: str
    created_at: str
    format: ReportFormat = ReportFormat.JSON
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class AnalyticsService:
    """Main analytics service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None):
        """Initialize analytics service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize analytics database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_reports (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    period TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    metrics TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    format TEXT NOT NULL
                )
            ''')
            
            # Scheduled reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_reports (
                    id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    recipients TEXT,
                    parameters TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_run TEXT,
                    next_run TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Analytics database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
    
    def get_color_analysis_analytics(
        self,
        start_date: str,
        end_date: str,
        tenant_id: Optional[str] = None
    ) -> List[AnalyticsMetric]:
        """
        Get color analysis analytics.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            tenant_id: Filter by tenant ID (optional)
        
        Returns:
            List of analytics metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query color analysis data
            query = '''
                SELECT 
                    COUNT(*) as total_analyses,
                    AVG(delta_e) as avg_delta_e,
                    MAX(delta_e) as max_delta_e,
                    MIN(delta_e) as min_delta_e,
                    SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as pass_count,
                    SUM(CASE WHEN status = 'Fail' THEN 1 ELSE 0 END) as fail_count
                FROM measurements
                WHERE timestamp BETWEEN ? AND ?
            '''
            
            params = [start_date, end_date]
            
            if tenant_id:
                query += ' AND tenant_id = ?'
                params.append(tenant_id)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            metrics = []
            if row:
                total_analyses, avg_delta_e, max_delta_e, min_delta_e, pass_count, fail_count = row
                
                metrics.extend([
                    AnalyticsMetric(
                        name="Total Analyses",
                        value=total_analyses or 0,
                        unit="count",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Average Delta E",
                        value=avg_delta_e or 0,
                        unit="ΔE",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Max Delta E",
                        value=max_delta_e or 0,
                        unit="ΔE",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Min Delta E",
                        value=min_delta_e or 0,
                        unit="ΔE",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Pass Rate",
                        value=(pass_count / total_analyses * 100) if total_analyses > 0 else 0,
                        unit="%",
                        timestamp=datetime.now().isoformat()
                    )
                ])
            
            conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get color analysis analytics: {e}")
            return []
    
    def get_user_activity_analytics(
        self,
        start_date: str,
        end_date: str,
        user_id: Optional[str] = None
    ) -> List[AnalyticsMetric]:
        """
        Get user activity analytics.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            user_id: Filter by user ID (optional)
        
        Returns:
            List of analytics metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query user activity from audit logs
            query = '''
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT action) as unique_actions
                FROM audit_logs
                WHERE timestamp BETWEEN ? AND ?
            '''
            
            params = [start_date, end_date]
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            metrics = []
            if row:
                total_actions, unique_users, unique_actions = row
                
                metrics.extend([
                    AnalyticsMetric(
                        name="Total Actions",
                        value=total_actions or 0,
                        unit="count",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Unique Users",
                        value=unique_users or 0,
                        unit="count",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Unique Actions",
                        value=unique_actions or 0,
                        unit="count",
                        timestamp=datetime.now().isoformat()
                    )
                ])
            
            conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get user activity analytics: {e}")
            return []
    
    def get_tenant_usage_analytics(
        self,
        start_date: str,
        end_date: str,
        tenant_id: Optional[str] = None
    ) -> List[AnalyticsMetric]:
        """
        Get tenant usage analytics.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            tenant_id: Filter by tenant ID (optional)
        
        Returns:
            List of analytics metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query tenant usage
            query = '''
                SELECT 
                    COUNT(DISTINCT tenant_id) as total_tenants,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_tenants
                FROM tenants
            '''
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            metrics = []
            if row:
                total_tenants, active_tenants = row
                
                metrics.extend([
                    AnalyticsMetric(
                        name="Total Tenants",
                        value=total_tenants or 0,
                        unit="count",
                        timestamp=datetime.now().isoformat()
                    ),
                    AnalyticsMetric(
                        name="Active Tenants",
                        value=active_tenants or 0,
                        unit="count",
                        timestamp=datetime.now().isoformat()
                    )
                ])
            
            conn.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get tenant usage analytics: {e}")
            return []
    
    def get_system_performance_analytics(
        self,
        start_date: str,
        end_date: str
    ) -> List[AnalyticsMetric]:
        """
        Get system performance analytics.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            List of analytics metrics
        """
        try:
            # In a real implementation, this would query system metrics
            # For now, return placeholder metrics
            metrics = [
                AnalyticsMetric(
                    name="Average Response Time",
                    value=120.5,
                    unit="ms",
                    timestamp=datetime.now().isoformat()
                ),
                AnalyticsMetric(
                    name="Error Rate",
                    value=0.02,
                    unit="%",
                    timestamp=datetime.now().isoformat()
                ),
                AnalyticsMetric(
                    name="Throughput",
                    value=450.5,
                    unit="req/min",
                    timestamp=datetime.now().isoformat()
                ),
                AnalyticsMetric(
                    name="Uptime",
                    value=99.95,
                    unit="%",
                    timestamp=datetime.now().isoformat()
                )
            ]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system performance analytics: {e}")
            return []
    
    def generate_report(
        self,
        report_type: ReportType,
        title: str,
        description: str,
        period: TimePeriod,
        start_date: str,
        end_date: str,
        created_by: str,
        format: ReportFormat = ReportFormat.JSON,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Report:
        """
        Generate a report.
        
        Args:
            report_type: Type of report
            title: Report title
            description: Report description
            period: Time period
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            created_by: User who created the report
            format: Output format
            tenant_id: Filter by tenant ID (optional)
            user_id: Filter by user ID (optional)
        
        Returns:
            Generated report
        """
        try:
            # Get metrics based on report type
            if report_type == ReportType.COLOR_ANALYSIS:
                metrics = self.get_color_analysis_analytics(start_date, end_date, tenant_id)
            elif report_type == ReportType.USER_ACTIVITY:
                metrics = self.get_user_activity_analytics(start_date, end_date, user_id)
            elif report_type == ReportType.TENANT_USAGE:
                metrics = self.get_tenant_usage_analytics(start_date, end_date, tenant_id)
            elif report_type == ReportType.SYSTEM_PERFORMANCE:
                metrics = self.get_system_performance_analytics(start_date, end_date)
            else:
                metrics = []
            
            # Create report
            report = Report(
                id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=report_type,
                title=title,
                description=description,
                period=period,
                start_date=start_date,
                end_date=end_date,
                metrics=metrics,
                created_by=created_by,
                created_at=datetime.now().isoformat(),
                format=format
            )
            
            # Store report in database
            self._store_report(report)
            
            logger.info(f"Report generated: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
    
    def _store_report(self, report: Report):
        """Store report in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analytics_reports
                (id, type, title, description, period, start_date, end_date, metrics, created_by, created_at, format)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.id,
                report.type.value,
                report.title,
                report.description,
                report.period.value,
                report.start_date,
                report.end_date,
                json.dumps([asdict(m) for m in report.metrics]),
                report.created_by,
                report.created_at,
                report.format.value
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store report: {e}")
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """
        Get a report by ID.
        
        Args:
            report_id: Report ID
        
        Returns:
            Report or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, type, title, description, period, start_date, end_date, metrics, created_by, created_at, format
                FROM analytics_reports
                WHERE id = ?
            ''', (report_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                metrics_data = json.loads(row[7])
                metrics = [AnalyticsMetric(**m) for m in metrics_data]
                
                return Report(
                    id=row[0],
                    type=ReportType(row[1]),
                    title=row[2],
                    description=row[3],
                    period=TimePeriod(row[4]),
                    start_date=row[5],
                    end_date=row[6],
                    metrics=metrics,
                    created_by=row[8],
                    created_at=row[9],
                    format=ReportFormat(row[10])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None
    
    def list_reports(
        self,
        report_type: Optional[ReportType] = None,
        limit: int = 50
    ) -> List[Report]:
        """
        List reports.
        
        Args:
            report_type: Filter by report type (optional)
            limit: Maximum number of reports to return
        
        Returns:
            List of reports
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT id, type, title, description, period, start_date, end_date, metrics, created_by, created_at, format FROM analytics_reports'
            params = []
            
            if report_type:
                query += ' WHERE type = ?'
                params.append(report_type.value)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                metrics_data = json.loads(row[7])
                metrics = [AnalyticsMetric(**m) for m in metrics_data]
                
                reports.append(Report(
                    id=row[0],
                    type=ReportType(row[1]),
                    title=row[2],
                    description=row[3],
                    period=TimePeriod(row[4]),
                    start_date=row[5],
                    end_date=row[6],
                    metrics=metrics,
                    created_by=row[8],
                    created_at=row[9],
                    format=ReportFormat(row[10])
                ))
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM analytics_reports WHERE id = ?', (report_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete report: {e}")
            return False

# Global analytics service instance
analytics_service = AnalyticsService()
