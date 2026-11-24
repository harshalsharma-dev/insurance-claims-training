from models.db_models import Policy


def test_create_claim_success(authenticated_client, db_session, monkeypatch):
    # Prevent an actual notification from being sent.
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    # Create a policy in the test database.
    policy = Policy(
        policy_number="TEST1001",
        policy_type="Motor",
    )

    db_session.add(policy)
    db_session.flush()

    payload = {
        "policy_number": "TEST1001",
        "claim_amount": "50000",
        "priority": "High",
        "description": "Vehicle accident damage",
    }

    response = authenticated_client.post("/claims", json=payload)

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["claim_id"] == 1
    assert response_data["claim_type"] == "Motor"
    assert float(response_data["claim_amount"]) == 50000.0
    assert response_data["status"] == "Submitted"
    assert response_data["priority"] == "High"
    assert response_data["description"] == "Vehicle accident damage"


def test_create_claim_with_unknown_policy(authenticated_client, monkeypatch):
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    payload = {
        "policy_number": "UNKNOWN1",
        "claim_amount": "50000",
        "priority": "Medium",
        "description": "Test claim",
    }

    response = authenticated_client.post("/claims", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Policy not found"


def test_get_all_claims(authenticated_client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    policy = Policy(
        policy_number="TEST2001",
        policy_type="Motor",
    )
    db_session.add(policy)
    db_session.flush()

    response = authenticated_client.post(
        "/claims",
        json={
            "policy_number": "TEST2001",
            "claim_amount": "25000",
            "priority": "Medium",
            "description": "Test vehicle damage",
        },
    )

    assert response.status_code == 201
    claim_id = response.json()["claim_id"]

    response = authenticated_client.get("/claims")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["claim_id"] == claim_id


def test_get_claim_by_id(authenticated_client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    policy = Policy(
        policy_number="TEST2002",
        policy_type="Health",
    )
    db_session.add(policy)
    db_session.flush()

    create_response = authenticated_client.post(
        "/claims",
        json={
            "policy_number": "TEST2002",
            "claim_amount": "15000",
            "priority": "Low",
            "description": "Medical expense",
        },
    )

    claim_id = create_response.json()["claim_id"]

    response = authenticated_client.get(f"/claims/{claim_id}")

    assert response.status_code == 200
    assert response.json()["claim_id"] == claim_id
    assert response.json()["claim_type"] == "Health"


def test_get_nonexistent_claim(authenticated_client):
    response = authenticated_client.get("/claims/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Claim with ID 999 not found"


def test_update_claim(authenticated_client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    policy = Policy(
        policy_number="TEST3001",
        policy_type="Motor",
    )
    db_session.add(policy)
    db_session.flush()

    create_response = authenticated_client.post(
        "/claims",
        json={
            "policy_number": "TEST3001",
            "claim_amount": "20000",
            "priority": "Low",
            "description": "Original description",
        },
    )

    claim_id = create_response.json()["claim_id"]

    update_response = authenticated_client.put(
        f"/claims/{claim_id}",
        json={
            "policy_number": "TEST3001",
            "status": "Submitted",
            "priority": "High",
            "claim_amount": "35000",
            "description": "Updated description",
        },
    )

    assert update_response.status_code == 200
    assert float(update_response.json()["claim_amount"]) == 35000.0
    assert update_response.json()["priority"] == "High"
    assert update_response.json()["description"] == "Updated description"


def test_patch_claim(authenticated_client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    policy = Policy(
        policy_number="TEST3002",
        policy_type="Health",
    )
    db_session.add(policy)
    db_session.flush()

    create_response = authenticated_client.post(
        "/claims",
        json={
            "policy_number": "TEST3002",
            "claim_amount": "10000",
            "priority": "Medium",
            "description": "Original description",
        },
    )

    claim_id = create_response.json()["claim_id"]

    response = authenticated_client.patch(
        f"/claims/{claim_id}",
        json={"claim_amount": "15000"},
    )

    assert response.status_code == 200
    assert float(response.json()["claim_amount"]) == 15000.0
    assert response.json()["priority"] == "Medium"


def test_delete_claim(authenticated_client, db_session, monkeypatch):
    monkeypatch.setattr(
        "routers.claims.send_claim_notification",
        lambda *args, **kwargs: None,
    )

    policy = Policy(
        policy_number="TEST4001",
        policy_type="Property",
    )
    db_session.add(policy)
    db_session.flush()

    create_response = authenticated_client.post(
        "/claims",
        json={
            "policy_number": "TEST4001",
            "claim_amount": "30000",
            "priority": "Medium",
            "description": "Property damage",
        },
    )

    claim_id = create_response.json()["claim_id"]

    # Delete the claim.
    delete_response = authenticated_client.delete(f"/claims/{claim_id}")

    assert delete_response.status_code == 204

    # Verify the claim no longer exists.
    get_response = authenticated_client.get(f"/claims/{claim_id}")

    assert get_response.status_code == 404
