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
