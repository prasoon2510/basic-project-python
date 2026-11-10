
def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Welcome to E-Commerce Management API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "Running"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Healthy"
    assert data["application"] == "E-Commerce Management API"


def test_database_health_endpoint(client):
    response = client.get("/health/database")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Healthy"
    assert data["database"] == "MySQL"
    assert data["connection"] == "Connected"
