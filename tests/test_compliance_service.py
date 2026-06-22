"""
Unit tests for Compliance Service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from utils.compliance_service import ComplianceService, ComplianceStandard, ComplianceStatus


@pytest.fixture
def compliance_service():
    """Fixture for ComplianceService instance"""
    return ComplianceService()


@pytest.fixture
def mock_database():
    """Mock database connection"""
    with patch('utils.compliance_service.Database') as mock:
        yield mock.return_value


class TestComplianceService:
    """Test cases for ComplianceService"""

    def test_generate_compliance_report_gdpr(self, compliance_service, mock_database):
        """Test generating GDPR compliance report"""
        mock_database.query.return_value = [
            {"check": "data_encryption", "status": "pass"},
            {"check": "audit_logging", "status": "pass"},
            {"check": "user_consent", "status": "pass"}
        ]
        
        report = compliance_service.generate_report(
            standard=ComplianceStandard.GDPR,
            title="GDPR Compliance Report",
            description="Monthly GDPR compliance check",
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now()
        )
        
        assert report["standard"] == ComplianceStandard.GDPR
        assert report["title"] == "GDPR Compliance Report"
        assert report["status"] == ComplianceStatus.COMPLIANT
        assert len(report["checks"]) == 3

    def test_generate_compliance_report_soc2(self, compliance_service, mock_database):
        """Test generating SOC2 compliance report"""
        mock_database.query.return_value = [
            {"check": "access_control", "status": "pass"},
            {"check": "incident_response", "status": "fail"}
        ]
        
        report = compliance_service.generate_report(
            standard=ComplianceStandard.SOC2,
            title="SOC2 Compliance Report",
            description="Quarterly SOC2 compliance check",
            period_start=datetime.now() - timedelta(days=90),
            period_end=datetime.now()
        )
        
        assert report["standard"] == ComplianceStandard.SOC2
        assert report["status"] == ComplianceStatus.NON_COMPLIANT

    def test_list_compliance_reports(self, compliance_service, mock_database):
        """Test listing compliance reports"""
        mock_database.query.return_value = [
            {"id": "report_1", "standard": "GDPR", "created_at": "2026-06-20"},
            {"id": "report_2", "standard": "SOC2", "created_at": "2026-06-21"}
        ]
        
        reports = compliance_service.list_reports()
        
        assert len(reports) == 2
        assert reports[0]["standard"] == "GDPR"
        assert reports[1]["standard"] == "SOC2"

    def test_get_compliance_report_by_id(self, compliance_service, mock_database):
        """Test getting compliance report by ID"""
        mock_database.query.return_value = [
            {
                "id": "report_1",
                "standard": "GDPR",
                "title": "GDPR Report",
                "status": "compliant",
                "checks": [{"check": "encryption", "status": "pass"}]
            }
        ]
        
        report = compliance_service.get_report("report_1")
        
        assert report["id"] == "report_1"
        assert report["standard"] == "GDPR"

    def test_delete_compliance_report(self, compliance_service, mock_database):
        """Test deleting compliance report"""
        mock_database.execute.return_value = True
        
        result = compliance_service.delete_report("report_1")
        
        assert result is True

    def test_check_gdpr_compliance(self, compliance_service):
        """Test GDPR compliance checks"""
        checks = compliance_service.check_gdpr_compliance()
        
        assert len(checks) > 0
        assert all("check" in check for check in checks)
        assert all("status" in check for check in checks)

    def test_check_soc2_compliance(self, compliance_service):
        """Test SOC2 compliance checks"""
        checks = compliance_service.check_soc2_compliance()
        
        assert len(checks) > 0
        assert all("check" in check for check in checks)
        assert all("status" in check for check in checks)

    def test_check_hipaa_compliance(self, compliance_service):
        """Test HIPAA compliance checks"""
        checks = compliance_service.check_hipaa_compliance()
        
        assert len(checks) > 0
        assert all("check" in check for check in checks)
        assert all("status" in check for check in checks)

    def test_check_iso27001_compliance(self, compliance_service):
        """Test ISO27001 compliance checks"""
        checks = compliance_service.check_iso27001_compliance()
        
        assert len(checks) > 0
        assert all("check" in check for check in checks)
        assert all("status" in check for check in checks)

    def test_check_pci_dss_compliance(self, compliance_service):
        """Test PCI DSS compliance checks"""
        checks = compliance_service.check_pci_dss_compliance()
        
        assert len(checks) > 0
        assert all("check" in check for check in checks)
        assert all("status" in check for check in checks)

    def test_calculate_compliance_score(self, compliance_service):
        """Test calculating compliance score"""
        checks = [
            {"check": "encryption", "status": "pass"},
            {"check": "audit_logging", "status": "pass"},
            {"check": "access_control", "status": "fail"}
        ]
        
        score = compliance_service.calculate_compliance_score(checks)
        
        assert score == pytest.approx(66.67, 0.01)

    def test_get_compliance_summary(self, compliance_service, mock_database):
        """Test getting compliance summary"""
        mock_database.query.side_effect = [
            [{"count": 5, "compliant": 4}],  # GDPR
            [{"count": 5, "compliant": 3}],  # SOC2
            [{"count": 5, "compliant": 5}]   # HIPAA
        ]
        
        summary = compliance_service.get_summary()
        
        assert summary["GDPR"]["score"] == 80.0
        assert summary["SOC2"]["score"] == 60.0
        assert summary["HIPAA"]["score"] == 100.0

    def test_export_compliance_report_to_pdf(self, compliance_service):
        """Test exporting compliance report to PDF"""
        report = {
            "standard": "GDPR",
            "title": "GDPR Report",
            "checks": [{"check": "encryption", "status": "pass"}]
        }
        
        with patch('utils.compliance_service.generate_pdf') as mock_pdf:
            mock_pdf.return_value = b"pdf-content"
            
            pdf_content = compliance_service.export_to_pdf(report)
            
            assert pdf_content == b"pdf-content"
            mock_pdf.assert_called_once()

    def test_schedule_compliance_check(self, compliance_service):
        """Test scheduling compliance check"""
        schedule = compliance_service.schedule_check(
            standard=ComplianceStandard.GDPR,
            frequency="monthly",
            day_of_month=1
        )
        
        assert schedule["standard"] == ComplianceStandard.GDPR
        assert schedule["frequency"] == "monthly"
        assert schedule["day_of_month"] == 1

    def test_get_compliance_history(self, compliance_service, mock_database):
        """Test getting compliance history"""
        mock_database.query.return_value = [
            {"date": "2026-05-01", "score": 80.0},
            {"date": "2026-06-01", "score": 85.0}
        ]
        
        history = compliance_service.get_history(standard=ComplianceStandard.GDPR)
        
        assert len(history) == 2
        assert history[0]["score"] == 80.0
        assert history[1]["score"] == 85.0

    def test_identify_compliance_gaps(self, compliance_service):
        """Test identifying compliance gaps"""
        checks = [
            {"check": "encryption", "status": "pass"},
            {"check": "audit_logging", "status": "fail"},
            {"check": "access_control", "status": "fail"}
        ]
        
        gaps = compliance_service.identify_gaps(checks)
        
        assert len(gaps) == 2
        assert gaps[0]["check"] == "audit_logging"
        assert gaps[1]["check"] == "access_control"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
