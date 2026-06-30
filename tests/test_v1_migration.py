import pytest
from fastapi.testclient import TestClient
from app.main import app
from utils.auth import create_access_token
from datetime import timedelta

@pytest.fixture
def auth_headers():
    access_token = create_access_token(
        data={"sub": "admin", "role": "ADMIN", "tenant_id": "default"},
        expires_delta=timedelta(minutes=15)
    )
    return {"Authorization": f"Bearer {access_token}"}

def test_get_clients_v1(auth_headers):
    with TestClient(app) as client:
        response = client.get("/v1/clients/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

def test_add_client_v1(auth_headers):
    payload = {
        "name": "Test Client V1",
        "tolerance": 1.5,
        "preferred_method": "CIE2000"
    }
    with TestClient(app) as client:
        response = client.post("/v1/clients/", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Клиентът е добавен/обновен успешно"
        assert "id" in data

def test_get_models_registry_v1(auth_headers):
    with TestClient(app) as client:
        response = client.get("/v1/models/registry", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_get_models_list_v1(auth_headers):
    with TestClient(app) as client:
        response = client.get("/v1/models/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "note" in data

def test_clear_database_v1(auth_headers):
    with TestClient(app) as client:
        response = client.post("/v1/rag/clear-database", headers=auth_headers)
        assert response.status_code == 200
        assert "Базата данни" in response.json()["message"]

def test_predict_batch_risk_v1(auth_headers):
    payload = {"temp": 80, "pressure": 1.2}
    with TestClient(app) as client:
        response = client.post("/v1/analytics/predict-batch-risk", json=payload, headers=auth_headers)
        assert response.status_code == 200

def test_kg_export_v1(auth_headers):
    with TestClient(app) as client:
        response = client.get("/v1/knowledge-graph/export", headers=auth_headers)
        assert response.status_code == 200

def test_generate_iso_report_v1(auth_headers):
    with TestClient(app) as client:
        response = client.post("/v1/reports/generate-iso", headers=auth_headers)
        assert response.status_code == 200
        assert "filename" in response.json()

def test_legacy_clients_proxy(auth_headers):
    with TestClient(app) as client:
        response = client.get("/clients", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["X-API-Deprecated"] == "true"

def test_legacy_diagnose_proxy(auth_headers):
    payload = {
        "prompt": "Test",
        "context": "Test context",
        "use_rag": False,
        "query": "Test"
    }
    with TestClient(app) as client:
        response = client.post("/diagnose", json=payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["X-API-Deprecated"] == "true"
