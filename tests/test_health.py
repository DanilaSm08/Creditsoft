import pytest


@pytest.mark.django_db
@pytest.mark.requirement("INF-01")
def test_health(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_health_read_only(client):
    assert client.post("/health/").status_code == 405
