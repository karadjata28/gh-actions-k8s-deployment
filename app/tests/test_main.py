from http import HTTPStatus

from app.main import create_app


def test_root_endpoint_returns_runtime_metadata(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("DEMO_SECRET_TOKEN", "configured")

    client = create_app().test_client()

    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    payload = response.get_json()
    assert payload["app"] == "devops-k8s-demo"
    assert payload["environment"] == "test"
    assert payload["version"] == "1.2.3"
    assert payload["hostname"]
    assert payload["secretConfigured"] is True


def test_health_endpoint_returns_ok():
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"status": "ok"}
