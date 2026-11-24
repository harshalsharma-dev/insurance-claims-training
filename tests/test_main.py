from conftest import client


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


def test_deliberately_failing():
    # assert 1 == 2
    assert 1 == 1
