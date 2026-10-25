def test_health_check_endpoint(application_client):
    client = application_client
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "CareerMind AI"


def test_demo_notice_exposes_no_configuration_secrets(application_client, monkeypatch):
    from app.core.config import settings
    for enabled in [True, False]:
        monkeypatch.setattr(settings, "DEMO_MODE", enabled)
        response = application_client.get("/api/v1/deployment-info")
        assert response.status_code == 200
        assert response.json() == {"disposable_demo": enabled}
