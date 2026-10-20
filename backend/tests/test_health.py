def test_health_check_endpoint(application_client):
    client = application_client
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "CareerMind AI"
