"""
Request binding tests.

Path parameters, query parameters and request bodies are validated before a
view runs, and every failure is reported through the same validation envelope.
The final two tests pin pre-existing server-error behaviour that the API has
always had, so a future change to it is noticed rather than silently accepted.
"""

from json import dumps

from django.test import Client

PRODUCT_PAYLOAD = {
    "category": "Tees",
    "name": "Binding Tee",
    "color": "Black",
    "price": 39.90,
    "collection": "SS26",
    "coming_soon": False,
}


def first_error(response):
    return response.json()["error"]["details"]["errors"][0]


def test_invalid_product_id_reports_a_path_error(client):
    response = client.get("/products/not-a-uuid")

    assert response.status_code == 422
    error = first_error(response)
    assert error["loc"] == ["path", "product_id"]
    assert error["type"] == "uuid_parsing"
    assert error["input"] == "not-a-uuid"


def test_limit_above_the_maximum_is_rejected(client):
    response = client.get("/products/?limit=101")

    assert response.status_code == 422
    error = first_error(response)
    assert error["loc"] == ["query", "limit"]
    assert error["type"] == "less_than_equal"
    assert error["input"] == "101"


def test_limit_must_be_an_integer(client):
    response = client.get("/products/?limit=abc")

    assert response.status_code == 422
    error = first_error(response)
    assert error["loc"] == ["query", "limit"]
    assert error["type"] == "int_parsing"


def test_offset_falls_back_to_its_default(client):
    client.post("/products/", json=PRODUCT_PAYLOAD)

    response = client.get("/products/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_requires_a_query_parameter(client):
    response = client.get("/products/search")

    assert response.status_code == 422
    error = first_error(response)
    assert error["loc"] == ["query", "q"]
    assert error["type"] == "missing"
    assert error["input"] is None


def test_malformed_json_body_is_rejected(client):
    response = Client().post(
        "/products/", data="{invalid", content_type="application/json"
    )

    assert response.status_code == 422
    error = first_error(response)
    assert error["type"] == "json_invalid"
    assert error["loc"] == ["body", 1]
    assert error["msg"] == "JSON decode error"


def test_non_json_content_type_is_rejected(client):
    response = Client().post("/products/", data="hello", content_type="text/plain")

    assert response.status_code == 422
    error = first_error(response)
    assert error["loc"] == ["body"]
    assert error["type"] == "model_attributes_type"


def test_missing_body_is_rejected(client):
    response = Client().post("/products/", data="", content_type="application/json")

    assert response.status_code == 422
    error = first_error(response)
    assert error["loc"] == ["body"]
    assert error["type"] == "missing"
    assert error["input"] is None


def test_body_without_a_content_type_is_rejected(client):
    response = Client().generic(
        "POST", "/products/", dumps(PRODUCT_PAYLOAD), content_type=""
    )

    assert response.status_code == 422
    error = first_error(response)
    assert error["type"] == "model_attributes_type"
    assert error["loc"] == ["body"]
    assert error["input"] == dumps(PRODUCT_PAYLOAD)


def test_omitted_optional_fields_fail_with_a_server_error(client):
    response = client.post(
        "/products/", json={"category": "Tees", "name": "Sparse", "price": 39.90}
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "UNEXPECTED_ERROR"
    assert response.json()["error"]["message"] == "An unexpected error occurred"


def test_blank_product_name_fails_with_a_server_error(client):
    response = client.post("/products/", json={**PRODUCT_PAYLOAD, "name": "   "})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "UNEXPECTED_ERROR"
