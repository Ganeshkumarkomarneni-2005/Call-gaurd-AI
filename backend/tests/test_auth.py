"""Tests for authentication endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


def test_register_new_user(client: TestClient) -> None:
    """POST /auth/register creates a user and returns a bearer token."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Secure1234",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient, test_user) -> None:
    """POST /auth/register with a duplicate e-mail returns 409."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "Secure1234",
            "full_name": "Dup User",
        },
    )
    assert resp.status_code == 409, resp.text


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_correct_credentials(client: TestClient, test_user) -> None:
    """POST /auth/login with valid credentials returns a token."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "Str0ng!Pass#2026"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user) -> None:
    """POST /auth/login with wrong password returns 401."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "WrongPass!"},
    )
    assert resp.status_code == 401, resp.text


def test_login_nonexistent_user(client: TestClient) -> None:
    """POST /auth/login with unknown e-mail returns 401."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "Password123"},
    )
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------


def test_get_current_user(client: TestClient, auth_headers: dict) -> None:
    """GET /auth/me returns the authenticated user profile."""
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "testuser@example.com"
    assert "id" in body
    assert "hashed_password" not in body


def test_get_current_user_no_token(client: TestClient) -> None:
    """GET /auth/me without a token returns 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401, resp.text


def test_get_current_user_bad_token(client: TestClient) -> None:
    """GET /auth/me with an invalid token returns 401."""
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer totally.invalid.token"}
    )
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# Forgot Password & Reset Password
# ---------------------------------------------------------------------------


def test_forgot_password_registered_user(client: TestClient, test_user) -> None:
    """POST /auth/forgot-password sends reset link for registered user."""
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "message" in body
    assert "reset_link" in body
    assert "/reset-password?token=" in body["reset_link"]


def test_forgot_password_unregistered_user(client: TestClient) -> None:
    """POST /auth/forgot-password returns safe generic response for unknown user."""
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "message" in body


def test_reset_password_flow(client: TestClient, test_user) -> None:
    """Test full reset password flow: request reset link, set new password, login."""
    # 1. Request reset link
    forgot_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert forgot_resp.status_code == 200
    reset_link = forgot_resp.json()["reset_link"]
    token = reset_link.split("token=")[1]

    # 2. Reset password using token
    new_password = "BrandNewSecret#2026"
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": new_password},
    )
    assert reset_resp.status_code == 200
    assert "successfully updated" in reset_resp.json()["message"]

    # 3. Verify login with old password fails
    old_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "Str0ng!Pass#2026"},
    )
    assert old_login_resp.status_code == 401

    # 4. Verify login with new password succeeds
    new_login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": new_password},
    )
    assert new_login_resp.status_code == 200
    assert "access_token" in new_login_resp.json()


def test_reset_password_invalid_token(client: TestClient) -> None:
    """POST /auth/reset-password with invalid token returns 400."""
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid.fake.token", "new_password": "NewValidPassword123"},
    )
    assert resp.status_code == 400, resp.text

