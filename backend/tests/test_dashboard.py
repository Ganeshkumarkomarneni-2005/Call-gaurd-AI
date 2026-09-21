"""Tests for dashboard endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_dashboard_statistics_requires_auth(client: TestClient) -> None:
    """GET /dashboard/statistics without auth returns 401."""
    resp = client.get("/api/v1/dashboard/statistics")
    assert resp.status_code == 401


def test_dashboard_statistics(
    client: TestClient, auth_headers: dict, sample_call
) -> None:
    """GET /dashboard/statistics returns aggregated stats."""
    resp = client.get("/api/v1/dashboard/statistics", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Check all expected top-level keys exist
    for key in (
        "total_calls",
        "today_calls",
        "ai_callers",
        "human_callers",
        "risk_distribution",
        "intent_distribution",
        "caller_type_distribution",
    ):
        assert key in body, f"Missing key: {key}"
    assert body["total_calls"] >= 0


def test_dashboard_recent_calls(
    client: TestClient, auth_headers: dict, sample_call
) -> None:
    """GET /dashboard/recent-calls returns up to 10 calls."""
    resp = client.get("/api/v1/dashboard/recent-calls", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "calls" in body
    assert isinstance(body["calls"], list)
    assert len(body["calls"]) <= 10


def test_dashboard_risk_summary(
    client: TestClient, auth_headers: dict, sample_call
) -> None:
    """GET /dashboard/risk-summary returns risk distribution dict."""
    resp = client.get("/api/v1/dashboard/risk-summary", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "risk_distribution" in body
    assert "total_calls" in body
