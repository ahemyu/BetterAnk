"""Integration tests for authentication endpoints."""
import pytest


@pytest.mark.integration
class TestRegistration:
    """Test user registration endpoint."""

    def test_register_new_user(self, client):
        """Test successful user registration."""
        response = client.post(
            "/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username fails."""
        response = client.post(
            "/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "username already exists" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email fails."""
        response = client.post(
            "/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",  # Already exists
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "password123"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/register",
            json={
                "username": "newuser"
                # Missing email and password
            }
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username."""
        response = client.post(
            "/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/login", data={})
        assert response.status_code == 422


@pytest.mark.integration
class TestGetMe:
    """Test get current user endpoint."""

    def test_get_me_authenticated(self, client, auth_headers, test_user):
        """Test getting current user information when authenticated."""
        response = client.get("/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["id"] == test_user.id
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_me_unauthenticated(self, client):
        """Test getting current user without authentication fails."""
        response = client.get("/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestDeleteMe:
    """Test delete current user endpoint."""

    def test_delete_me_authenticated(self, client, auth_headers, test_user):
        """Test deleting current user account."""
        response = client.delete("/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()

        # Verify user is deleted by trying to login
        login_response = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 401

    def test_delete_me_unauthenticated(self, client):
        """Test deleting user without authentication fails."""
        response = client.delete("/me")
        assert response.status_code == 401
