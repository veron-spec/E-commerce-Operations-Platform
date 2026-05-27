"""API tests for authentication endpoints — register, login, me."""
import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, unauth_client: AsyncClient, db):
        response = await unauth_client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "Secure@123",
            "name": "NewUser",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["name"] == "NewUser"
        assert "access_token" in data

    async def test_register_duplicate_email(self, unauth_client: AsyncClient, test_user):
        response = await unauth_client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "Secure@123",
            "name": "Duplicate",
        })
        assert response.status_code == 409
        assert "已注册" in response.json()["detail"]

    async def test_register_weak_password(self, unauth_client: AsyncClient):
        response = await unauth_client.post("/api/v1/auth/register", json={
            "email": "weak@example.com",
            "password": "123",
            "name": "Weak",
        })
        assert response.status_code == 422
        assert "至少" in response.json()["detail"]

    async def test_register_missing_fields(self, unauth_client: AsyncClient):
        response = await unauth_client.post("/api/v1/auth/register", json={
            "email": "incomplete@example.com",
        })
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, unauth_client: AsyncClient, test_user):
        response = await unauth_client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Pass@1234",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    async def test_login_wrong_password(self, unauth_client: AsyncClient, test_user):
        response = await unauth_client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, unauth_client: AsyncClient):
        response = await unauth_client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123",
        })
        assert response.status_code == 401


class TestMe:
    async def test_get_me(self, unauth_client: AsyncClient, test_user, user_token):
        response = await unauth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "TestUser"

    async def test_get_me_no_token(self, unauth_client: AsyncClient):
        response = await unauth_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, unauth_client: AsyncClient):
        response = await unauth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
