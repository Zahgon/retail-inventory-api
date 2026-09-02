"""
Routing tests: unmatched paths, unsupported methods, slash redirects and the
response envelope details (204 shape, security headers) that the API exposes on
every request.
"""

from django.test import Client

PRODUCT_PAYLOAD = {
    "category": "Tees",
    "name": "Routing Tee",
    "color": "Black",
    "price": 39.90,
    "collection": "SS26",
    "coming_soon": False,
}


def test_unknown_path_returns_not_found(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert response["Content-Type"] == "application/json"


def test_unknown_nested_path_returns_not_found(client):
    response = client.get("/products/total_value/extra")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_unsupported_method_reports_the_first_registered_method(client):
    response = client.post("/health")

    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}
    assert response["Allow"] == "GET"


def test_unsupported_method_on_a_collection(client):
    response = client.delete("/")

    assert response.status_code == 405
    assert response["Allow"] == "GET"


def test_missing_trailing_slash_redirects(client):
    response = Client().get("/products")

    assert response.status_code == 307
    assert response["Location"].endswith("/products/")
    assert response["Content-Length"] == "0"
    assert not response.has_header("Content-Type")
    assert response.content == b""


def test_extra_trailing_slash_redirects(client):
    response = Client().get("/health/")

    assert response.status_code == 307
    assert response["Location"].endswith("/health")


def test_redirect_preserves_the_query_string(client):
    response = Client().get("/products", {"limit": "5"})

    assert response.status_code == 307
    assert response["Location"].endswith("/products/?limit=5")


def test_redirect_target_is_an_absolute_url(client):
    response = Client().get("/products")

    assert response["Location"].startswith("http://")


def test_delete_returns_no_content_without_a_body(client):
    created = client.post("/products/", json=PRODUCT_PAYLOAD).json()

    response = client.delete(f"/products/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert not response.has_header("Content-Length")
    assert response["Content-Type"] == "application/json"


def test_responses_carry_no_security_headers(client):
    response = client.get("/health")

    assert not response.has_header("Strict-Transport-Security")
    assert not response.has_header("X-Content-Type-Options")
    assert not response.has_header("X-Frame-Options")
    assert not response.has_header("Referrer-Policy")
    assert not response.has_header("Permissions-Policy")
    assert not response.has_header("Cross-Origin-Opener-Policy")
    assert not response.has_header("Cross-Origin-Embedder-Policy")
    assert not response.has_header("Cross-Origin-Resource-Policy")


def test_html_requests_carry_no_content_security_policy(client):
    response = Client().get("/docs", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert not response.has_header("Content-Security-Policy")


def test_json_responses_emit_content_length_before_content_type(client):
    response = client.get("/")

    assert list(response.headers) == ["Content-Length", "Content-Type"]


def test_method_not_allowed_emits_allow_before_the_entity_headers(client):
    response = client.post("/health", json={})

    assert list(response.headers) == ["Allow", "Content-Length", "Content-Type"]


def test_redirects_emit_content_length_before_location(client):
    response = Client().get("/products")

    assert list(response.headers) == ["Content-Length", "Location"]


def test_documentation_pages_emit_content_length_before_content_type(client):
    response = client.get("/docs")

    assert list(response.headers) == ["Content-Length", "Content-Type"]
