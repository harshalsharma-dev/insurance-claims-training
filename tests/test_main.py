def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
