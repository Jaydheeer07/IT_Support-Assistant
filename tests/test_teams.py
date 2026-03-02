import pytest
from fastapi.testclient import TestClient

def test_messages_endpoint_exists_and_not_404():
    """The /api/messages endpoint must exist (Bot Framework sends to it)."""
    from main import app
    client = TestClient(app)
    # Without valid Bot Framework auth, expect 401 or 500 (not 404)
    response = client.post("/api/messages", json={"type": "message", "text": "hello"})
    assert response.status_code != 404, f"Got 404 — /api/messages endpoint is missing"

def test_health_still_works():
    """Ensure health check still works after wiring the bot."""
    from main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
