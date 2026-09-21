"""Tests for the /health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """GET /health returns 200 with all expected fields."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "CallGuard AI"
    assert "timestamp" in body
    assert "version" in body


def test_root_endpoint(client: TestClient) -> None:
    """GET / returns API info with docs and health keys."""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert "service" in body
    assert "docs" in body
    assert "health" in body
