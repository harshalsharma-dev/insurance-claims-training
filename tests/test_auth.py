from models.db_models import User
from utils.security import hash_password


def test_get_current_user(authenticated_client):
    response = authenticated_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "claimant@test.com"
    assert response.json()["role"] == "claimant"


def test_admin_can_access_admin_endpoint(admin_client):
    response = admin_client.get("/auth/admin")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_claimant_cannot_access_admin_endpoint(authenticated_client):
    response = authenticated_client.get("/auth/admin")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action"
    )


def test_signup_success(client, monkeypatch):
    monkeypatch.setattr(
        # "routers.auth.send_welcome_notification",
        "routers.auth.send_welcome_notification.delay",
        lambda *args, **kwargs: None,
    )

    payload = {
        "name": "New Claimant",
        "email": "newclaimant@test.com",
        "phone_number": "9876543212",
        "password": "TestPassword123",
    }

    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 201
    assert response.json()["email"] == "newclaimant@test.com"
    assert response.json()["role"] == "claimant"


def test_signup_duplicate_email(authenticated_client, monkeypatch):
    monkeypatch.setattr(
        "routers.auth.send_welcome_notification",
        lambda *args, **kwargs: None,
    )

    payload = {
        "name": "Duplicate Claimant",
        "email": "claimant@test.com",
        "phone_number": "9876543213",
        "password": "TestPassword123",
    }

    response = authenticated_client.post("/auth/signup", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_login_success(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.auth.check_login_rate_limit",
        lambda client_ip: (True, 60),
    )

    user = User(
        name="Login User",
        email="login@test.com",
        phone_number="9876543214",
        role="claimant",
        password_hash=hash_password("LoginPassword123"),
    )

    db_session.add(user)
    db_session.flush()

    response = client.post(
        "/auth/login",
        data={
            "username": "login@test.com",
            "password": "LoginPassword123",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["token_type"] == "bearer"
    assert response_data["access_token"]
    assert response_data["refresh_token"]


def test_login_wrong_password(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.auth.check_login_rate_limit",
        lambda client_ip: (True, 60),
    )

    user = User(
        name="Login User",
        email="wrongpass@test.com",
        phone_number="9876543215",
        role="claimant",
        password_hash=hash_password("CorrectPassword123"),
    )

    db_session.add(user)
    db_session.flush()

    response = client.post(
        "/auth/login",
        data={
            "username": "wrongpass@test.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
