import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_liveness_check():
    with TestClient(app) as client:
        response = client.get("/livez")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

def test_analyze_color_basic():
    # Тест с базови параметри
    payload = {
        "lab_sample": [50.0, 10.0, 20.0],
        "lab_standard": [50.5, 10.5, 20.5],
        "method": "CIE2000",
        "tolerance": 1.0,
        "batch_id": "TEST-BATCH",
        "operator_id": "TEST-OP",
        "machine_id": "TEST-MACH"
    }
    # Пътят е /v1/color/analyze според app/main.py
    with TestClient(app) as client:
        response = client.post("/v1/color/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "delta_e" in data
        assert "status" in data
        assert data["status"] in ["Pass", "Fail"]
