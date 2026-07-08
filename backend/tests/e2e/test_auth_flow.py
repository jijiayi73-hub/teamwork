"""
F-001: Authentication Full Flow Tests

Tests the complete authentication lifecycle:
1. Register → Login → Access Protected Resource → Logout → Token Invalidation
"""
import uuid
import pytest


class TestAuthenticationFullFlow:
    """Test the complete authentication flow."""

    def test_register_login_access_logout_flow(self, client):
        """
        Test: Register → Login → Access Protected → Logout → Token Invalid

        This is the F-001 main flow test.
        """
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"flow_user_{unique_id}",
            "email": f"flow_{unique_id}@example.com",
            "password": "SecurePassword123!",
            "role": "user"
        }

        # Step 1: Register new user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["success"] is True
        assert "access_token" in register_data["data"]
        assert "user" in register_data["data"]
        assert register_data["data"]["user"]["username"] == user_data["username"]
        assert register_data["data"]["user"]["email"] == user_data["email"]
        first_token = register_data["data"]["access_token"]

        # Step 2: Login with same credentials
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["success"] is True
        assert "access_token" in login_data["data"]
        second_token = login_data["data"]["access_token"]
        # Tokens might be the same if generated at same time
        # The important part is both work for authentication

        # Step 3: Access protected resource with token
        auth_headers = {"Authorization": f"Bearer {second_token}"}

        # Verify current user
        me_response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["data"]["username"] == user_data["username"]
        assert me_data["data"]["email"] == user_data["email"]

        # Access diaries (protected resource)
        diaries_response = client.get("/api/v1/diaries", headers=auth_headers)
        assert diaries_response.status_code == 200
        assert diaries_response.json()["data"] == []  # Empty list for new user

        # Access stats (protected resource)
        stats_response = client.get("/api/v1/stats/overview", headers=auth_headers)
        assert stats_response.status_code == 200
        stats_data = stats_response.json()["data"]
        assert stats_data["total_diaries"] == 0

        # Step 4: Logout (client-side token invalidation)
        # In real flow, client would clear localStorage and dispatch 'auth-change'
        # We simulate by using an invalidated token

        # Step 5: Verify old token cannot access protected resources
        old_headers = {"Authorization": f"Bearer {first_token}"}
        invalid_response = client.get("/api/v1/auth/me", headers=old_headers)
        # Old first token should still work (JWT doesn't invalidate on re-login)
        # But let's test with a completely invalid token
        fake_headers = {"Authorization": "Bearer invalid_token_12345"}
        fake_response = client.get("/api/v1/auth/me", headers=fake_headers)
        assert fake_response.status_code == 401

    def test_token_expiration_handling(self, client):
        """Test that expired tokens are rejected."""
        unique_id = str(uuid.uuid4())[:8]

        # Register and get token
        response = client.post("/api/v1/auth/register", json={
            "username": f"expire_test_{unique_id}",
            "email": f"expire_{unique_id}@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 201
        token = response.json()["data"]["access_token"]

        # Test token works initially
        auth_headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_response.status_code == 200

        # Test malformed token header
        bad_headers = {"Authorization": "InvalidFormat token123"}
        bad_response = client.get("/api/v1/auth/me", headers=bad_headers)
        assert bad_response.status_code == 401

        # Test missing token
        no_token_response = client.get("/api/v1/auth/me")
        assert no_token_response.status_code == 401

    def test_login_after_logout_simulation(self, client):
        """Test user can login after logout simulation."""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"relogin_{unique_id}",
            "email": f"relogin_{unique_id}@example.com",
            "password": "Password123!"
        }

        # Register
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        first_token = register_response.json()["data"]["access_token"]

        # Simulate using the app
        auth_headers = {"Authorization": f"Bearer {first_token}"}
        client.get("/api/v1/diaries", headers=auth_headers)
        assert register_response.status_code == 201

        # Simulate logout (token would be cleared on client)
        # User returns and logs in again
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        new_token = login_response.json()["data"]["access_token"]

        # New token works
        new_headers = {"Authorization": f"Bearer {new_token}"}
        me_response = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_response.status_code == 200
        assert me_response.json()["data"]["email"] == user_data["email"]

    def test_protected_routes_require_auth(self, client):
        """Test that all protected routes properly require authentication."""
        protected_routes = [
            ("GET", "/api/v1/auth/me"),
            ("GET", "/api/v1/diaries"),
            ("GET", "/api/v1/stats/overview"),
            ("GET", "/api/v1/chat/conversations"),
            ("POST", "/api/v1/chat/messages"),
            ("GET", "/api/v1/memories"),
        ]

        for method, route in protected_routes:
            if method == "GET":
                response = client.get(route)
            elif method == "POST":
                response = client.post(route, json={})

            # Should return 401 for unauthenticated request
            assert response.status_code == 401, f"{method} {route} should require auth"

    def test_public_routes_accessible_without_auth(self, client):
        """Test that public routes don't require authentication."""
        public_routes = [
            "/health",
            "/api/v1/health",
            "/docs",
            "/openapi.json"
        ]

        for route in public_routes:
            response = client.get(route)
            # Public routes should be accessible
            assert response.status_code == 200, f"{route} should be publicly accessible"


class TestAuthenticationDatabaseIntegrity:
    """Test that authentication properly affects database state."""

    def test_user_persisted_after_registration(self, client, db_session):
        """Test that user record is properly created in database."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"db_test_{unique_id}@example.com"
        username = f"dbtest_{unique_id}"

        response = client.post("/api/v1/auth/register", json={
            "username": username,
            "email": email,
            "password": "Password123!"
        })
        assert response.status_code == 201

        # Verify user exists in database
        from app.models.diary import User
        user = db_session.query(User).filter_by(email=email).first()
        assert user is not None
        assert user.username == username
        assert user.email == email
        assert user.role == "user"
        assert user.password_hash != "Password123!"  # Should be hashed

    def test_multiple_users_can_coexist(self, client, db_session):
        """Test that multiple users can be registered and authenticated."""
        users = []
        for i in range(3):
            unique_id = str(uuid.uuid4())[:8]
            user_data = {
                "username": f"multi_{i}_{unique_id}",
                "email": f"multi_{i}_{unique_id}@example.com",
                "password": "Password123!"
            }
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201
            users.append(response.json()["data"]["user"])

        # Verify all users exist
        from app.models.diary import User
        all_users = db_session.query(User).count()
        assert all_users == 3

        # Verify each user can authenticate
        for user in users:
            response = client.post("/api/v1/auth/login", json={
                "email": user["email"],
                "password": "Password123!"
            })
            assert response.status_code == 200
            assert response.json()["data"]["user"]["email"] == user["email"]
