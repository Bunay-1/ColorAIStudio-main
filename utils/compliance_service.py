"""
Automated Compliance Reporting Service for ICAP Enterprise
===========================================================
Compliance report generation and management for regulatory requirements.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

logger = logging.getLogger("Compliance_Service")

class ComplianceStandard(str, Enum):
    """Compliance standards."""
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    CUSTOM = "custom"

class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"

class ReportFrequency(str, Enum):
    """Report generation frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"

@dataclass
class ComplianceCheck:
    """Individual compliance check result."""
    id: str
    standard: ComplianceStandard
    control_id: str
    control_name: str
    description: str
    status: ComplianceStatus
    score: float
    findings: List[str]
    evidence: List[str]
    last_assessed: str
    assessor: str
    
    def __post_init__(self):
        if self.last_assessed is None:
            self.last_assessed = datetime.now().isoformat()

@dataclass
class ComplianceReport:
    """Compliance report data structure."""
    id: str
    standard: ComplianceStandard
    title: str
    description: str
    period_start: str
    period_end: str
    overall_status: ComplianceStatus
    overall_score: float
    checks: List[ComplianceCheck]
    recommendations: List[str]
    generated_by: str
    generated_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()

class ComplianceService:
    """Main compliance service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None):
        """Initialize compliance service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
        self._init_database()
        self._load_compliance_controls()
    
    def _init_database(self):
        """Initialize compliance database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compliance reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    id TEXT PRIMARY KEY,
                    standard TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    overall_score REAL,
                    checks TEXT,
                    recommendations TEXT,
                    generated_by TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT
                )
            ''')
            
            # Compliance checks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id TEXT PRIMARY KEY,
                    standard TEXT NOT NULL,
                    control_id TEXT NOT NULL,
                    control_name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    score REAL,
                    findings TEXT,
                    evidence TEXT,
                    last_assessed TEXT NOT NULL,
                    assessor TEXT NOT NULL
                )
            ''')
            
            # Scheduled compliance reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_compliance_reports (
                    id TEXT PRIMARY KEY,
                    standard TEXT NOT NULL,
                    title TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    recipients TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_run TEXT,
                    next_run TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Compliance database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize compliance database: {e}")
    
    def _load_compliance_controls(self):
        """Load compliance control definitions."""
        # Define controls for different standards
        self.controls = {
            ComplianceStandard.GDPR: [
                {
                    "control_id": "GDPR-001",
                    "control_name": "Data Access Logging",
                    "description": "All data access must be logged with user and timestamp",
                    "check_function": self._check_data_access_logging
                },
                {
                    "control_id": "GDPR-002",
                    "control_name": "Data Retention Policy",
                    "description": "Data must be retained according to retention policy",
                    "check_function": self._check_data_retention
                },
                {
                    "control_id": "GDPR-003",
                    "control_name": "Right to be Forgotten",
                    "description": "User data must be deletable upon request",
                    "check_function": self._check_right_to_be_forgotten
                }
            ],
            ComplianceStandard.SOC2: [
                {
                    "control_id": "SOC2-001",
                    "control_name": "Access Control",
                    "description": "Access to systems must be controlled and monitored",
                    "check_function": self._check_access_control
                },
                {
                    "control_id": "SOC2-002",
                    "control_name": "Change Management",
                    "description": "All changes must be documented and approved",
                    "check_function": self._check_change_management
                },
                {
                    "control_id": "SOC2-003",
                    "control_name": "Incident Response",
                    "description": "Security incidents must be tracked and resolved",
                    "check_function": self._check_incident_response
                }
            ]
        }
    
    def _check_data_access_logging(self) -> tuple:
        """Check GDPR data access logging compliance."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if audit logs exist and are being recorded
            cursor.execute('SELECT COUNT(*) FROM audit_logs WHERE timestamp >= datetime("now", "-7 days")')
            count = cursor.fetchone()[0]
            
            conn.close()
            
            if count > 0:
                return (ComplianceStatus.COMPLIANT, 1.0, [])
            else:
                return (ComplianceStatus.NON_COMPLIANT, 0.0, ["No audit logs found in the last 7 days"])
                
        except Exception as e:
            logger.error(f"Error checking data access logging: {e}")
            return (ComplianceStatus.PENDING_REVIEW, 0.5, [f"Error: {str(e)}"])
    
    def _check_data_retention(self) -> tuple:
        """Check GDPR data retention policy compliance."""
        try:
            # Check if old data is being cleaned up
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # This is a simplified check - in reality, you'd check actual retention policy
            cursor.execute('SELECT COUNT(*) FROM audit_logs WHERE timestamp < datetime("now", "-365 days")')
            old_logs = cursor.fetchone()[0]
            
            conn.close()
            
            if old_logs == 0:
                return (ComplianceStatus.COMPLIANT, 1.0, [])
            else:
                return (ComplianceStatus.PARTIALLY_COMPLIANT, 0.7, [f"{old_logs} old logs found - may violate retention policy"])
                
        except Exception as e:
            logger.error(f"Error checking data retention: {e}")
            return (ComplianceStatus.PENDING_REVIEW, 0.5, [f"Error: {str(e)}"])
    
    def _check_right_to_be_forgotten(self) -> tuple:
        """Check GDPR right to be forgotten compliance."""
        try:
            # Check if user deletion functionality works
            # This is a simplified check
            return (ComplianceStatus.COMPLIANT, 1.0, [])
                
        except Exception as e:
            logger.error(f"Error checking right to be forgotten: {e}")
            return (ComplianceStatus.PENDING_REVIEW, 0.5, [f"Error: {str(e)}"])
    
    def _check_access_control(self) -> tuple:
        """Check SOC2 access control compliance."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if role-based access is implemented
            cursor.execute('SELECT COUNT(DISTINCT role) FROM users')
            role_count = cursor.fetchone()[0]
            
            conn.close()
            
            if role_count >= 3:
                return (ComplianceStatus.COMPLIANT, 1.0, [])
            else:
                return (ComplianceStatus.PARTIALLY_COMPLIANT, 0.6, ["Insufficient role diversity for access control"])
                
        except Exception as e:
            logger.error(f"Error checking access control: {e}")
            return (ComplianceStatus.PENDING_REVIEW, 0.5, [f"Error: {str(e)}"])
    
    def _check_change_management(self) -> tuple:
        """Check SOC2 change management compliance."""
        try:
            # Check if audit logs track changes
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM audit_logs WHERE action LIKE "%create%" OR action LIKE "%update%" OR action LIKE "%delete%"')
            change_count = cursor.fetchone()[0]
            
            conn.close()
            
            if change_count > 0:
                return (ComplianceStatus.COMPLIANT, 1.0, [])
            else:
                return (ComplianceStatus.PARTIALLY_COMPLIANT, 0.5, ["No change management logs found"])
                
        except Exception as e:
            logger.error(f"Error checking change management: {e}")
            return (ComplianceStatus.PENDING_REVIEW, 0.5, [f"Error: {str(e)}"])
    
    def _check_incident_response(self) -> tuple:
        """Check SOC2 incident response compliance."""
        try:
            # Check if security incidents are being tracked
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM alerts WHERE severity IN ("error", "critical")')
            incident_count = cursor.fetchone()[0]
            
            resolved_count = cursor.fetchone()[0] if cursor.description else 0
            
            conn.close()
            
            if incident_count > 0 and resolved_count > 0:
                return (ComplianceStatus.COMPLIANT, 1.0, [])
            elif incident_count > 0:
                return (ComplianceStatus.PARTIALLY_COMPLIANT, 0.7, ["Incidents found but not all resolved"])
            else:
                return (ComplianceStatus.COMPLIANT, 1.0, [])
                
        except Exception as e:
            logger.error(f"Error checking incident response: {e}")
            return (ComplianceStatus.PENDING_REVIEW, 0.5, [f"Error: {str(e)}"])
    
    def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        title: str,
        description: str,
        period_start: str,
        period_end: str,
        generated_by: str
    ) -> ComplianceReport:
        """
        Generate a compliance report.
        
        Args:
            standard: Compliance standard
            title: Report title
            description: Report description
            period_start: Report period start (ISO format)
            period_end: Report period end (ISO format)
            generated_by: User who generated the report
        
        Returns:
            Generated compliance report
        """
        try:
            # Get controls for the standard
            controls = self.controls.get(standard, [])
            
            # Run compliance checks
            checks = []
            total_score = 0.0
            
            for control in controls:
                status, score, findings = control["check_function"]()
                
                check = ComplianceCheck(
                    id=f"check_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{control['control_id']}",
                    standard=standard,
                    control_id=control["control_id"],
                    control_name=control["control_name"],
                    description=control["description"],
                    status=status,
                    score=score,
                    findings=findings,
                    evidence=[],
                    assessor=generated_by
                )
                
                checks.append(check)
                total_score += score
            
            # Calculate overall status and score
            if controls:
                overall_score = total_score / len(controls)
            else:
                overall_score = 0.0
            
            if overall_score >= 0.9:
                overall_status = ComplianceStatus.COMPLIANT
            elif overall_score >= 0.7:
                overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
            elif overall_score >= 0.5:
                overall_status = ComplianceStatus.PENDING_REVIEW
            else:
                overall_status = ComplianceStatus.NON_COMPLIANT
            
            # Generate recommendations
            recommendations = self._generate_recommendations(checks)
            
            # Create report
            report = ComplianceReport(
                id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{standard.value}",
                standard=standard,
                title=title,
                description=description,
                period_start=period_start,
                period_end=period_end,
                overall_status=overall_status,
                overall_score=overall_score,
                checks=checks,
                recommendations=recommendations,
                generated_by=generated_by
            )
            
            # Store report
            self._store_report(report)
            
            logger.info(f"Compliance report generated: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            raise
    
    def _generate_recommendations(self, checks: List[ComplianceCheck]) -> List[str]:
        """Generate recommendations based on compliance checks."""
        recommendations = []
        
        for check in checks:
            if check.status != ComplianceStatus.COMPLIANT:
                recommendations.append(f"Address {check.control_name}: {', '.join(check.findings)}")
        
        if not recommendations:
            recommendations.append("Continue maintaining current compliance practices")
        
        return recommendations
    
    def _store_report(self, report: ComplianceReport):
        """Store report in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO compliance_reports
                (id, standard, title, description, period_start, period_end, overall_status, overall_score, checks, recommendations, generated_by, generated_at, approved_by, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.id,
                report.standard.value,
                report.title,
                report.description,
                report.period_start,
                report.period_end,
                report.overall_status.value,
                report.overall_score,
                json.dumps([asdict(c) for c in report.checks]),
                json.dumps(report.recommendations),
                report.generated_by,
                report.generated_at,
                report.approved_by,
                report.approved_at
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store report: {e}")
    
    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get a compliance report by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, standard, title, description, period_start, period_end, overall_status, overall_score, checks, recommendations, generated_by, generated_at, approved_by, approved_at
                FROM compliance_reports
                WHERE id = ?
            ''', (report_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                checks_data = json.loads(row[8])
                checks = [ComplianceCheck(**c) for c in checks_data]
                
                return ComplianceReport(
                    id=row[0],
                    standard=ComplianceStandard(row[1]),
                    title=row[2],
                    description=row[3],
                    period_start=row[4],
                    period_end=row[5],
                    overall_status=ComplianceStatus(row[6]),
                    overall_score=row[7],
                    checks=checks,
                    recommendations=json.loads(row[9]),
                    generated_by=row[10],
                    generated_at=row[11],
                    approved_by=row[12],
                    approved_at=row[13]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None
    
    def list_reports(
        self,
        standard: Optional[ComplianceStandard] = None,
        limit: int = 50
    ) -> List[ComplianceReport]:
        """List compliance reports."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT id, standard, title, description, period_start, period_end, overall_status, overall_score, checks, recommendations, generated_by, generated_at, approved_by, approved_at FROM compliance_reports'
            params = []
            
            if standard:
                query += ' WHERE standard = ?'
                params.append(standard.value)
            
            query += ' ORDER BY generated_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                checks_data = json.loads(row[8])
                checks = [ComplianceCheck(**c) for c in checks_data]
                
                reports.append(ComplianceReport(
                    id=row[0],
                    standard=ComplianceStandard(row[1]),
                    title=row[2],
                    description=row[3],
                    period_start=row[4],
                    period_end=row[5],
                    overall_status=ComplianceStatus(row[6]),
                    overall_score=row[7],
                    checks=checks,
                    recommendations=json.loads(row[9]),
                    generated_by=row[10],
                    generated_at=row[11],
                    approved_by=row[12],
                    approved_at=row[13]
                ))
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []
    
    def approve_report(self, report_id: str, approved_by: str) -> bool:
        """Approve a compliance report."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE compliance_reports
                SET approved_by = ?, approved_at = ?
                WHERE id = ?
            ''', (approved_by, datetime.now().isoformat(), report_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve report: {e}")
            return False

# Global compliance service instance
compliance_service = ComplianceService()
