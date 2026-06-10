"""API integration via FastAPI TestClient (mock LLM, real test DB)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _client() -> TestClient:
    from backend.app.main import app

    return TestClient(app)


def test_chat_streams_valid_sse() -> None:
    with _client() as client:
        with client.stream(
            "POST", "/chat", json={"session_id": "api-test", "message": "Tell me about PS11752778"}
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            body = "".join(resp.iter_text())
    assert "event: tool_start" in body
    assert "event: done" in body


def test_malformed_body_422() -> None:
    with _client() as client:
        assert client.post("/chat", json={"nope": 1}).status_code == 422


def test_part_endpoint_and_404() -> None:
    with _client() as client:
        ok = client.get("/parts/PS11752778")
        assert ok.status_code == 200 and ok.json()["mpn"] == "WPW10321304"
        assert client.get("/parts/PS00000001").status_code == 404


def test_health_and_cors() -> None:
    with _client() as client:
        health = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert health.json()["parts_count"] > 0
        assert health.headers.get("access-control-allow-origin") == "http://localhost:3000"
