"""
Search tests: the endpoint switches between an exact SKU lookup and a partial
name match depending on the shape of the query string.
"""

PRODUCT_PAYLOAD = {
    "category": "Tees",
    "name": "Striped Tee",
    "color": "Black",
    "price": 39.90,
    "collection": "SS26",
    "coming_soon": False,
}


def test_search_by_partial_name(client):
    client.post("/products/", json=PRODUCT_PAYLOAD)

    response = client.get("/products/search?q=strip")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Striped Tee"


def test_search_by_sku(client):
    client.post("/products/", json=PRODUCT_PAYLOAD)

    response = client.get("/products/search?q=ts-0001")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sku"] == "TS-0001"


def test_search_by_unknown_sku_returns_nothing(client):
    client.post("/products/", json=PRODUCT_PAYLOAD)

    response = client.get("/products/search?q=ZZ-9999")

    assert response.status_code == 200
    assert response.json() == []


def test_search_without_a_match_returns_nothing(client):
    client.post("/products/", json=PRODUCT_PAYLOAD)

    response = client.get("/products/search?q=hoodie")

    assert response.status_code == 200
    assert response.json() == []
