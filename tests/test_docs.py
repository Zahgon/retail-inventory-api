"""
Documentation surface tests.

The root endpoint advertises ``"docs": "/docs"`` and the README links to it, so
the OpenAPI document and the three documentation pages are part of the public
interface and are covered here.
"""

PATHS = [
    "/health",
    "/",
    "/products/total_value",
    "/products/",
    "/products/search",
    "/products/{product_id}",
    "/products/{product_id}/variants",
    "/products/{product_id}/variants/{variant_id}",
]

SCHEMAS = [
    "Category",
    "HTTPValidationError",
    "HealthResponse",
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "ProductVariant",
    "ProductVariantCreate",
    "ProductVariantUpdate",
    "Size",
    "ValidationError",
]


def test_openapi_document_is_served(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    document = response.json()
    assert document["openapi"] == "3.1.0"
    assert document["info"]["title"] == "Retail Inventory API"
    assert document["info"]["version"] == "0.0.0"


def test_openapi_document_lists_every_endpoint(client):
    document = client.get("/openapi.json").json()

    assert list(document["paths"]) == PATHS
    assert list(document["paths"]["/health"]) == ["get", "head"]
    assert list(document["paths"]["/products/"]) == ["get", "post"]
    assert list(document["paths"]["/products/{product_id}"]) == [
        "get",
        "patch",
        "delete",
    ]


def test_openapi_document_keeps_the_published_operation_ids(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert paths["/health"]["get"]["operationId"] == "health_check_health_get"
    assert (
        paths["/products/"]["post"]["operationId"]
        == "create_product_router_products__post"
    )
    assert (
        paths["/products/{product_id}"]["delete"]["operationId"]
        == "delete_product_router_products__product_id__delete"
    )


def test_openapi_document_declares_the_created_and_no_content_statuses(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "201" in paths["/products/"]["post"]["responses"]
    assert paths["/products/{product_id}"]["delete"]["responses"]["204"] == {
        "description": "Successful Response"
    }


def test_openapi_document_exposes_the_model_schemas(client):
    document = client.get("/openapi.json").json()

    assert list(document["components"]["schemas"]) == SCHEMAS
    assert document["components"]["schemas"]["Category"]["enum"] == [
        "Tees",
        "Sweaters",
        "Shirts",
        "Pants",
        "Shorts",
        "Tank Tops",
        "Other",
    ]


def test_swagger_ui_is_served(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    body = response.content.decode()
    assert "Retail Inventory API - Swagger UI" in body
    assert "/openapi.json" in body
    assert '"docExpansion": "none"' in body


def test_swagger_ui_oauth2_redirect_is_served(client):
    response = client.get("/docs/oauth2-redirect")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert "swaggerUIRedirectOauth2" in response.content.decode()


def test_redoc_is_served(client):
    response = client.get("/redoc")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    body = response.content.decode()
    assert "Retail Inventory API - ReDoc" in body
    assert '<redoc spec-url="/openapi.json">' in body
