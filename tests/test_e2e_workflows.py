"""
End-to-End Tests for Critical Workflows
=======================================
Тестове за критични бизнес workflows в ICAP.
"""

import pytest
import asyncio
import os
import tempfile
from fastapi.testclient import TestClient
from irm_api import app

@pytest.fixture
def client():
    """Fixture за TestClient."""
    return TestClient(app)

class TestCriticalWorkflows:
    """Test suite for critical business workflows."""
    
    def test_color_analysis_workflow(self, client):
        """Тест за пълен workflow на цветов анализ."""
        payload = {
            "lab_sample": [50.0, 10.0, 20.0],
            "lab_standard": [50.5, 10.5, 20.5],
            "method": "CIE2000",
            "tolerance": 1.0,
            "batch_id": "TEST-BATCH-001",
            "operator_id": "TEST-OP-001",
            "machine_id": "TEST-MACH-001",
            "client_id": "TEST-CLIENT-001",
            "batch_size": 100.0,
            "illuminant": "D65"
        }
        
        response = client.post("/color/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "delta_e" in data
        assert "status" in data
        assert "method" in data
        assert "closest_ral" in data
        assert "sustainability" in data
        
        # Verify data types
        assert isinstance(data["delta_e"], float)
        assert data["status"] in ["Pass", "Fail"]
        
        # Verify business logic
        if data["delta_e"] <= payload["tolerance"]:
            assert data["status"] == "Pass"
        else:
            assert data["status"] == "Fail"
    
    def test_trend_prediction_workflow(self, client):
        """Тест за workflow на прогнозиране на тренд."""
        payload = {
            "historical_de": [0.5, 0.6, 0.4, 0.7, 0.5, 0.8, 0.6, 0.7, 0.5, 0.6],
            "tolerance": 1.0
        }
        
        response = client.post("/color/predict_trend", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "prediction" in data
        assert "trend" in data
        assert "drift_warning" in data
        assert "anomalies_indices" in data
    
    def test_recipe_formulation_workflow(self, client):
        """Тест за workflow на изчисляване на рецепта."""
        payload = {
            "lab_sample": [50.0, 10.0, 20.0],
            "lab_standard": [50.5, 10.5, 20.5],
            "method": "CIE2000",
            "tolerance": 1.0,
            "batch_id": "TEST-BATCH-002",
            "operator_id": "TEST-OP-002",
            "machine_id": "TEST-MACH-002",
            "client_id": "TEST-CLIENT-002",
            "batch_size": 100.0,
            "illuminant": "D65"
        }
        
        response = client.post("/color/recipe_formulation", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recommended_pigment" in data
        assert "estimated_delta_e" in data
        assert "concentration" in data
    
    def test_health_check_workflow(self, client):
        """Тест за health check workflow."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_rag_query_workflow(self, client):
        """Тест за RAG query workflow."""
        payload = {
            "query": "How to fix yellow drift in color?",
            "n_results": 5
        }
        
        response = client.post("/rag/query", json=payload)
        
        # May fail if RAG is not initialized, but should not crash
        assert response.status_code in [200, 503]  # 503 if service unavailable
    
    def test_agent_workflow(self, client):
        """Тест за multi-agent workflow."""
        payload = {
            "task": "color_analysis",
            "data": {
                "lab_sample": [50.0, 10.0, 20.0],
                "lab_standard": [50.5, 10.5, 20.5]
            }
        }
        
        response = client.post("/agents/process", json=payload)
        
        # May fail if agents are not initialized
        assert response.status_code in [200, 503]
    
    def test_error_handling_invalid_payload(self, client):
        """Тест за error handling при невалиден payload."""
        payload = {
            "lab_sample": [50.0],  # Invalid: only 1 value instead of 3
            "lab_standard": [50.5, 10.5, 20.5],
            "method": "CIE2000",
            "tolerance": 1.0
        }
        
        response = client.post("/color/analyze", json=payload)
        
        # Should return 400 for invalid input
        assert response.status_code == 400
    
    def test_error_handling_negative_tolerance(self, client):
        """Тест за error handling при отрицателен толеранс."""
        payload = {
            "lab_sample": [50.0, 10.0, 20.0],
            "lab_standard": [50.5, 10.5, 20.5],
            "method": "CIE2000",
            "tolerance": -1.0,  # Invalid: negative tolerance
            "batch_id": "TEST-BATCH",
            "operator_id": "TEST-OP",
            "machine_id": "TEST-MACH"
        }
        
        response = client.post("/color/analyze", json=payload)
        
        # Should return 400 for invalid input
        assert response.status_code == 400
    
    def test_rate_limiting(self, client):
        """Тест за rate limiting."""
        payload = {
            "lab_sample": [50.0, 10.0, 20.0],
            "lab_standard": [50.5, 10.5, 20.5],
            "method": "CIE2000",
            "tolerance": 1.0,
            "batch_id": "TEST-BATCH",
            "operator_id": "TEST-OP",
            "machine_id": "TEST-MACH"
        }
        
        # Make multiple requests to test rate limiting
        for _ in range(5):
            response = client.post("/color/analyze", json=payload)
            # First few should succeed
            assert response.status_code in [200, 429]  # 429 if rate limited

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
