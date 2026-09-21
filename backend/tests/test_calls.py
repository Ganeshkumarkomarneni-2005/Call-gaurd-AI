"""Tests for call management endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /calls/incoming
# ---------------------------------------------------------------------------


def test_post_incoming_call(client: TestClient) -> None:
    """POST /calls/incoming creates a new call record and returns 201."""
    resp = client.post(
        "/api/v1/calls/incoming",
        json={
            "caller_number": "+15550009999",
            "virtual_number": "+15551112222",
            "telephony_call_id": "call-abc-123",
            "telephony_provider": "twilio",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "id" in body
    assert body["status"] == "ringing"
    assert body["caller_number"] == "+15550009999"


def test_post_incoming_call_missing_fields(client: TestClient) -> None:
    """POST /calls/incoming with missing required fields returns 422."""
    resp = client.post("/api/v1/calls/incoming", json={"caller_number": "+15550009999"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /calls
# ---------------------------------------------------------------------------


def test_list_calls_requires_auth(client: TestClient) -> None:
    """GET /calls without auth returns 401."""
    resp = client.get("/api/v1/calls")
    assert resp.status_code == 401


def test_list_calls(client: TestClient, auth_headers: dict, sample_call) -> None:
    """GET /calls returns a paginated list of calls."""
    resp = client.get("/api/v1/calls", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "calls" in body
    assert "total" in body
    assert isinstance(body["calls"], list)


# ---------------------------------------------------------------------------
# GET /calls/{call_id}
# ---------------------------------------------------------------------------


def test_get_call_detail(
    client: TestClient, auth_headers: dict, sample_call
) -> None:
    """GET /calls/{id} returns the full call detail view."""
    resp = client.get(f"/api/v1/calls/{sample_call.id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "call" in body
    assert str(body["call"]["id"]) == str(sample_call.id)


def test_get_call_not_found(client: TestClient, auth_headers: dict) -> None:
    """GET /calls/{unknown_id} returns 404."""
    resp = client.get(
        "/api/v1/calls/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# POST /calls/{call_id}/end
# ---------------------------------------------------------------------------


def test_end_call(client: TestClient, auth_headers: dict, sample_call) -> None:
    """POST /calls/{id}/end returns the updated call with status 'ended'."""
    resp = client.post(f"/api/v1/calls/{sample_call.id}/end", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ended"


def test_end_call_not_found(client: TestClient, auth_headers: dict) -> None:
    """POST /calls/{unknown_id}/end returns 404."""
    resp = client.post(
        "/api/v1/calls/00000000-0000-0000-0000-000000000000/end",
        headers=auth_headers,
    )
    assert resp.status_code == 404, resp.text
