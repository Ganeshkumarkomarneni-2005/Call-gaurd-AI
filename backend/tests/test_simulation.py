"""Tests for the simulation service and multi-scenario AI analysis pipeline."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_simulate_ai_recruiter_call(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Test simulating an AI recruitment call."""
    resp = client.post(
        "/api/v1/calls/simulate",
        json={"scenario": "ai_recruiter"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "id" in data
    assert data["caller_name"] == "AI Recruitment Assistant (ABC Technologies)"
    assert data["status"] == "ended"

    # Verify detail view
    call_id = data["id"]
    detail_resp = client.get(
        f"/api/v1/calls/{call_id}",
        headers=auth_headers,
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["transcript"] is not None
    assert len(detail["transcript"]["segments"]) > 0
    assert detail["analysis"] is not None
    assert detail["analysis"]["caller_type"] == "ai"
    assert detail["analysis"]["intent"] == "RECRUITMENT"
    assert detail["recruitment_details"] is not None
    assert detail["recruitment_details"]["company"] == "ABC Technologies"


def test_simulate_fraud_call(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Test simulating a high-risk fraud call."""
    resp = client.post(
        "/api/v1/calls/simulate",
        json={"scenario": "otp_fraud"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    call_id = data["id"]

    detail_resp = client.get(
        f"/api/v1/calls/{call_id}",
        headers=auth_headers,
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["analysis"]["risk_level"] in ("high", "critical")
    assert detail["analysis"]["decision"] == "end"


def test_simulation_reflected_in_dashboard(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Test that simulated calls appear in dashboard statistics and recent calls."""
    # 1. Simulate a call
    resp = client.post(
        "/api/v1/calls/simulate",
        json={"scenario": "human_recruiter"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text

    # 2. Check statistics
    stats_resp = client.get(
        "/api/v1/dashboard/statistics",
        headers=auth_headers,
    )
    assert stats_resp.status_code == 200, stats_resp.text
    stats = stats_resp.json()
    assert stats["total_calls"] >= 1

    # 3. Check recent calls
    recent_resp = client.get(
        "/api/v1/dashboard/recent-calls",
        headers=auth_headers,
    )
    assert recent_resp.status_code == 200, recent_resp.text
    recent = recent_resp.json()
    assert len(recent["calls"]) >= 1
