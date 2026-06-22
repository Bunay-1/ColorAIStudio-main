"""
Unit tests for Analytics Service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from utils.analytics_service import AnalyticsService, MetricType, ReportType


@pytest.fixture
def analytics_service():
    """Fixture for AnalyticsService instance"""
    return AnalyticsService()


@pytest.fixture
def mock_database():
    """Mock database connection"""
    with patch('utils.analytics_service.Database') as mock:
        yield mock.return_value


class TestAnalyticsService:
    """Test cases for AnalyticsService"""

    def test_get_metrics_color_analysis(self, analytics_service, mock_database):
        """Test getting color analysis metrics"""
        mock_database.query.return_value = [
            {"date": "2026-06-20", "count": 100, "avg_delta_e": 1.5},
            {"date": "2026-06-21", "count": 150, "avg_delta_e": 1.8}
        ]
        
        metrics = analytics_service.get_metrics(
            metric_type=MetricType.COLOR_ANALYSIS,
            period="24h"
        )
        
        assert metrics["metric_type"] == MetricType.COLOR_ANALYSIS
        assert metrics["period"] == "24h"
        assert len(metrics["data"]) == 2
        assert metrics["data"][0]["count"] == 100

    def test_get_metrics_vision_analysis(self, analytics_service, mock_database):
        """Test getting vision analysis metrics"""
        mock_database.query.return_value = [
            {"date": "2026-06-20", "defects_detected": 25, "accuracy": 0.94}
        ]
        
        metrics = analytics_service.get_metrics(
            metric_type=MetricType.VISION_ANALYSIS,
            period="7d"
        )
        
        assert metrics["metric_type"] == MetricType.VISION_ANALYSIS
        assert metrics["period"] == "7d"
        assert metrics["data"][0]["defects_detected"] == 25

    def test_get_metrics_rag_queries(self, analytics_service, mock_database):
        """Test getting RAG query metrics"""
        mock_database.query.return_value = [
            {"date": "2026-06-20", "queries": 50, "avg_response_time": 0.5}
        ]
        
        metrics = analytics_service.get_metrics(
            metric_type=MetricType.RAG_QUERIES,
            period="30d"
        )
        
        assert metrics["metric_type"] == MetricType.RAG_QUERIES
        assert metrics["data"][0]["queries"] == 50

    def test_generate_report_color_analysis(self, analytics_service, mock_database):
        """Test generating color analysis report"""
        mock_database.query.return_value = [
            {"batch_id": "batch_001", "delta_e": 1.5, "status": "pass"},
            {"batch_id": "batch_002", "delta_e": 2.5, "status": "fail"}
        ]
        
        report = analytics_service.generate_report(
            report_type=ReportType.COLOR_ANALYSIS,
            params={"period": "7d", "format": "pdf"}
        )
        
        assert report["report_type"] == ReportType.COLOR_ANALYSIS
        assert report["format"] == "pdf"
        assert report["generated_at"] is not None
        assert len(report["data"]) == 2

    def test_generate_report_compliance(self, analytics_service, mock_database):
        """Test generating compliance report"""
        mock_database.query.return_value = [
            {"check": "audit_log", "status": "pass"},
            {"check": "encryption", "status": "pass"}
        ]
        
        report = analytics_service.generate_report(
            report_type=ReportType.COMPLIANCE,
            params={"standard": "GDPR"}
        )
        
        assert report["report_type"] == ReportType.COMPLIANCE
        assert report["standard"] == "GDPR"
        assert report["data"][0]["status"] == "pass"

    def test_calculate_trend(self, analytics_service):
        """Test trend calculation"""
        data = [
            {"date": "2026-06-18", "value": 100},
            {"date": "2026-06-19", "value": 120},
            {"date": "2026-06-20", "value": 140}
        ]
        
        trend = analytics_service.calculate_trend(data)
        
        assert trend["direction"] == "increasing"
        assert trend["change_percentage"] == 40.0
        assert trend["slope"] > 0

    def test_calculate_statistics(self, analytics_service):
        """Test statistics calculation"""
        data = [1.5, 2.0, 1.8, 2.2, 1.9]
        
        stats = analytics_service.calculate_statistics(data)
        
        assert stats["mean"] == pytest.approx(1.88, 0.01)
        assert stats["median"] == pytest.approx(1.9, 0.01)
        assert stats["min"] == 1.5
        assert stats["max"] == 2.2
        assert stats["std_dev"] > 0

    def test_aggregate_by_period(self, analytics_service):
        """Test data aggregation by period"""
        data = [
            {"date": "2026-06-20T10:00:00", "value": 10},
            {"date": "2026-06-20T14:00:00", "value": 15},
            {"date": "2026-06-21T10:00:00", "value": 20}
        ]
        
        aggregated = analytics_service.aggregate_by_period(data, period="daily")
        
        assert len(aggregated) == 2
        assert aggregated[0]["date"] == "2026-06-20"
        assert aggregated[0]["value"] == 25
        assert aggregated[1]["date"] == "2026-06-21"

    def test_export_report_to_csv(self, analytics_service):
        """Test exporting report to CSV"""
        report_data = [
            {"batch_id": "batch_001", "delta_e": 1.5},
            {"batch_id": "batch_002", "delta_e": 2.0}
        ]
        
        csv_content = analytics_service.export_to_csv(report_data)
        
        assert "batch_id,delta_e" in csv_content
        assert "batch_001,1.5" in csv_content
        assert "batch_002,2.0" in csv_content

    def test_export_report_to_json(self, analytics_service):
        """Test exporting report to JSON"""
        report_data = [
            {"batch_id": "batch_001", "delta_e": 1.5}
        ]
        
        json_content = analytics_service.export_to_json(report_data)
        
        assert "batch_001" in json_content
        assert "1.5" in json_content

    def test_get_anomaly_detection(self, analytics_service):
        """Test anomaly detection"""
        data = [1.0, 1.1, 1.2, 1.3, 5.0, 1.4, 1.5]
        
        anomalies = analytics_service.detect_anomalies(data, threshold=2.0)
        
        assert len(anomalies) == 1
        assert anomalies[0]["value"] == 5.0
        assert anomalies[0]["index"] == 4

    def test_get_dashboard_summary(self, analytics_service, mock_database):
        """Test getting dashboard summary"""
        mock_database.query.side_effect = [
            [{"count": 1000}],  # total measurements
            [{"count": 50}],   # defects detected
            [{"count": 25}]    # alerts triggered
        ]
        
        summary = analytics_service.get_dashboard_summary()
        
        assert summary["total_measurements"] == 1000
        assert summary["defects_detected"] == 50
        assert summary["alerts_triggered"] == 25
        assert summary["defect_rate"] == 5.0

    def test_compare_periods(self, analytics_service):
        """Test comparing two time periods"""
        current_period = [{"date": "2026-06-20", "value": 100}]
        previous_period = [{"date": "2026-06-19", "value": 80}]
        
        comparison = analytics_service.compare_periods(current_period, previous_period)
        
        assert comparison["current_value"] == 100
        assert comparison["previous_value"] == 80
        assert comparison["change"] == 20
        assert comparison["change_percentage"] == 25.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
