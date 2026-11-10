
def test_create_category(admin_client):

    response = admin_client.post(
        "/api/v1/categories/",
        json={
            "name": "Electronics",
            "description": "Electronic products",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Electronics"
    assert data["description"] == "Electronic products"
    assert "id" in data


def test_get_all_categories(admin_client):

    admin_client.post(
        "/api/v1/categories/",
        json={
            "name": "Electronics",
            "description": "Electronic products",
        },
    )

    response = admin_client.get("/api/v1/categories/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Electronics"


def test_get_category_by_id(admin_client):

    create_response = admin_client.post(
        "/api/v1/categories/",
        json={
            "name": "Books",
            "description": "Books and educational materials",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    response = admin_client.get(
        f"/api/v1/categories/{category_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["name"] == "Books"


def test_create_category_with_invalid_data(admin_client):

    response = admin_client.post(
        "/api/v1/categories/",
        json={
            "name": "A",
            "description": "Invalid category name",
        },
    )

    assert response.status_code == 422


def test_delete_category(admin_client):

    create_response = admin_client.post(
        "/api/v1/categories/",
        json={
            "name": "Fashion",
            "description": "Fashion products",
        },
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    delete_response = admin_client.delete(
        f"/api/v1/categories/{category_id}"
    )

    assert delete_response.status_code in (200, 204)

    get_response = admin_client.get(
        f"/api/v1/categories/{category_id}"
    )

    assert get_response.status_code == 404


def test_get_non_existing_category(client):

    response = client.get(
        "/api/v1/categories/99999"
    )

    assert response.status_code == 404
