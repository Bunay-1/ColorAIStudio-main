import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_graphql_system_status():
    query = """
    query {
      systemStatus {
        status
        version
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["systemStatus"]["status"] == "healthy"
    assert "8.11" in data["data"]["systemStatus"]["version"]

def test_graphql_measurements_query():
    query = """
    query {
      measurements(limit: 5) {
        id
        batch_id
        status
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "measurements" in data["data"]
    assert isinstance(data["data"]["measurements"], list)

def test_graphql_create_measurement_mutation():
    mutation = """
    mutation {
      createMeasurement(
        batch_id: "test_graphql_batch",
        operator_id: "graphql_op",
        machine_id: "m1",
        client_id: "GENERAL",
        lab_sample: [50.0, 10.0, 5.0],
        lab_standard: [50.5, 10.2, 5.1],
        method: "CIE2000"
      ) {
        batch_id
        delta_e
        status
      }
    }
    """
    response = client.post("/graphql", json={"query": mutation})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["createMeasurement"]["batch_id"] == "test_graphql_batch"
    assert "delta_e" in data["data"]["createMeasurement"]
    assert "status" in data["data"]["createMeasurement"]
