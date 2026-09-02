"""
OpenAPI document generation.

The API advertises its own documentation surface: the home route returns
``"docs": "/docs"`` and the README links to it. The document is therefore part
of the public interface and is rebuilt here from the same Pydantic models the
views validate against, so it stays in sync with the code instead of being a
frozen copy.

Two details are reproduced deliberately because they are observable:

* ``components.schemas`` is normalised - keys are re-ordered into the canonical
  JSON Schema key order, ``None`` values are dropped, and the numeric
  constraint keywords are emitted as floats.
* ``paths`` is *not* normalised - operation, parameter and response objects
  keep the insertion order used when they are built.

Operation identifiers and generated response titles are published values that
clients key off, so they are kept exactly as they were even though the view
functions behind them were renamed.
"""

from typing import Any, Dict, List, Optional

from pydantic import TypeAdapter
from pydantic.json_schema import GenerateJsonSchema

from .core import config
from .models import (
    HealthResponse,
    Product,
    ProductCreate,
    ProductUpdate,
    ProductVariant,
    ProductVariantCreate,
    ProductVariantUpdate,
)

REF_TEMPLATE = "#/components/schemas/{model}"

# --- Schema normalisation ---------------------------------------------------

# Canonical JSON Schema key order. Keys outside this list keep their relative
# position and are appended after the known ones.
SCHEMA_KEY_ORDER = (
    "$schema",
    "$vocabulary",
    "$id",
    "$anchor",
    "$dynamicAnchor",
    "$ref",
    "$dynamicRef",
    "$defs",
    "$comment",
    "allOf",
    "anyOf",
    "oneOf",
    "not",
    "if",
    "then",
    "else",
    "dependentSchemas",
    "prefixItems",
    "items",
    "contains",
    "properties",
    "patternProperties",
    "additionalProperties",
    "propertyNames",
    "unevaluatedItems",
    "unevaluatedProperties",
    "type",
    "enum",
    "const",
    "multipleOf",
    "maximum",
    "exclusiveMaximum",
    "minimum",
    "exclusiveMinimum",
    "maxLength",
    "minLength",
    "pattern",
    "maxItems",
    "minItems",
    "uniqueItems",
    "maxContains",
    "minContains",
    "maxProperties",
    "minProperties",
    "required",
    "dependentRequired",
    "format",
    "contentEncoding",
    "contentMediaType",
    "contentSchema",
    "title",
    "description",
    "default",
    "deprecated",
    "readOnly",
    "writeOnly",
    "examples",
    "discriminator",
    "xml",
    "externalDocs",
    "example",
)

_KEY_RANK = {key: index for index, key in enumerate(SCHEMA_KEY_ORDER)}

# Numeric keywords are typed as floats, so integer bounds widen to floats.
FLOAT_KEYWORDS = frozenset(
    {"multipleOf", "maximum", "exclusiveMaximum", "minimum", "exclusiveMinimum"}
)

# Keywords whose value is a single nested schema.
_NESTED_SCHEMA = frozenset(
    {
        "not",
        "if",
        "then",
        "else",
        "items",
        "contains",
        "propertyNames",
        "unevaluatedItems",
        "unevaluatedProperties",
        "contentSchema",
        "additionalProperties",
    }
)

# Keywords whose value is a list of schemas.
_SCHEMA_LIST = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})

# Keywords whose value maps names to schemas.
_SCHEMA_MAP = frozenset(
    {"properties", "patternProperties", "dependentSchemas", "$defs"}
)


def normalise_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Re-order a JSON Schema fragment, drop null values and widen numeric bounds.

    Applied to every entry under ``components.schemas`` and recursively to each
    nested schema, mirroring how the document is serialised from its model
    representation.
    """
    normalised: Dict[str, Any] = {}

    for key, value in sorted(
        schema.items(), key=lambda item: _KEY_RANK.get(item[0], len(_KEY_RANK))
    ):
        # Null values never reach the document.
        if value is None:
            continue

        if key in FLOAT_KEYWORDS:
            normalised[key] = float(value)
        elif key in _SCHEMA_MAP:
            normalised[key] = {
                name: normalise_schema(nested) for name, nested in value.items()
            }
        elif key in _SCHEMA_LIST:
            normalised[key] = [normalise_schema(nested) for nested in value]
        elif key in _NESTED_SCHEMA and isinstance(value, dict):
            normalised[key] = normalise_schema(value)
        else:
            normalised[key] = value

    return normalised


# --- Component schemas ------------------------------------------------------

# Models exposed by the API, in the order they are first referenced.
DOCUMENTED_MODELS = (
    HealthResponse,
    Product,
    ProductCreate,
    ProductUpdate,
    ProductVariant,
    ProductVariantCreate,
    ProductVariantUpdate,
)

# The validation error envelope is part of the documented contract for every
# operation that takes parameters or a body.
VALIDATION_ERROR_SCHEMAS: Dict[str, Any] = {
    "HTTPValidationError": {
        "properties": {
            "detail": {
                "items": {"$ref": "#/components/schemas/ValidationError"},
                "type": "array",
                "title": "Detail",
            }
        },
        "type": "object",
        "title": "HTTPValidationError",
    },
    "ValidationError": {
        "properties": {
            "loc": {
                "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                "type": "array",
                "title": "Location",
            },
            "msg": {"type": "string", "title": "Message"},
            "type": {"type": "string", "title": "Error Type"},
            "input": {"title": "Input"},
            "ctx": {"type": "object", "title": "Context"},
        },
        "type": "object",
        "required": ["loc", "msg", "type"],
        "title": "ValidationError",
    },
}


def build_component_schemas() -> Dict[str, Any]:
    """Generate the ``components.schemas`` map from the Pydantic models."""
    generator = GenerateJsonSchema(ref_template=REF_TEMPLATE)
    inputs = [
        (model, "validation", TypeAdapter(model).core_schema)
        for model in DOCUMENTED_MODELS
    ]
    _, definitions = generator.generate_definitions(inputs=inputs)

    schemas: Dict[str, Any] = dict(definitions)
    schemas.update(VALIDATION_ERROR_SCHEMAS)

    return {name: normalise_schema(schemas[name]) for name in sorted(schemas)}


# --- Path items -------------------------------------------------------------


def _ref(model_name: str) -> Dict[str, str]:
    """Reference a component schema by model name."""
    return {"$ref": REF_TEMPLATE.format(model=model_name)}


def _parameter(name: str, location: str, required: bool, schema: Dict[str, Any]):
    """Build a single parameter object."""
    return {"name": name, "in": location, "required": required, "schema": schema}


def _request_body(model_name: str) -> Dict[str, Any]:
    """Build a required ``application/json`` request body."""
    return {
        "required": True,
        "content": {"application/json": {"schema": _ref(model_name)}},
    }


def _json_response(description: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Build a response object carrying a JSON payload."""
    return {
        "description": description,
        "content": {"application/json": {"schema": schema}},
    }


VALIDATION_RESPONSE = _json_response("Validation Error", _ref("HTTPValidationError"))

EMPTY_RESPONSE = {"description": "Successful Response"}


def _operation(
    tags: List[str],
    summary: str,
    operation_id: str,
    responses: Dict[str, Any],
    parameters: Optional[List[Dict[str, Any]]] = None,
    request_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble an operation object with its keys in documentation order."""
    operation: Dict[str, Any] = {
        "tags": tags,
        "summary": summary,
        "operationId": operation_id,
    }

    if parameters is not None:
        operation["parameters"] = parameters
    if request_body is not None:
        operation["requestBody"] = request_body

    operation["responses"] = responses

    return operation


PRODUCT_ID_PARAMETER = _parameter(
    "product_id",
    "path",
    True,
    {"type": "string", "format": "uuid", "title": "Product Id"},
)

VARIANT_ID_PARAMETER = _parameter(
    "variant_id",
    "path",
    True,
    {"type": "string", "format": "uuid", "title": "Variant Id"},
)


def _array_of(model_name: str, title: str) -> Dict[str, Any]:
    """Build the response schema for a list endpoint."""
    return {"type": "array", "items": _ref(model_name), "title": title}


def build_paths() -> Dict[str, Any]:
    """
    Build the ``paths`` object.

    Paths appear in the order their routes are registered, which is why the
    analytics route sits ahead of the product detail route.
    """
    return {
        "/health": {
            "get": _operation(
                ["System"],
                "Health Check",
                "health_check_health_get",
                {"200": _json_response("Successful Response", _ref("HealthResponse"))},
            ),
            "head": _operation(
                ["System"],
                "Health Check",
                "health_check_health_head",
                {"200": _json_response("Successful Response", {})},
            ),
        },
        "/": {
            "get": _operation(
                ["System"],
                "Read Root",
                "read_root__get",
                {"200": _json_response("Successful Response", {})},
            )
        },
        "/products/total_value": {
            "get": _operation(
                ["Analytics"],
                "Calculate the total monetary value of the current inventory",
                "get_inventory_value_router_products_total_value_get",
                {
                    "200": _json_response(
                        "Successful Response",
                        {
                            "additionalProperties": {"type": "number"},
                            "type": "object",
                            "title": (
                                "Response Get Inventory Value Router Products "
                                "Total Value Get"
                            ),
                        },
                    )
                },
            )
        },
        "/products/": {
            "get": _operation(
                ["Products"],
                "List all products with pagination",
                "get_all_products_router_products__get",
                {
                    "200": _json_response(
                        "Successful Response",
                        _array_of(
                            "Product",
                            "Response Get All Products Router Products  Get",
                        ),
                    ),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[
                    _parameter(
                        "offset",
                        "query",
                        False,
                        {"type": "integer", "default": 0, "title": "Offset"},
                    ),
                    _parameter(
                        "limit",
                        "query",
                        False,
                        {
                            "type": "integer",
                            "maximum": 100,
                            "default": 100,
                            "title": "Limit",
                        },
                    ),
                ],
            ),
            "post": _operation(
                ["Products"],
                "Add a new product to the inventory",
                "create_product_router_products__post",
                {
                    "201": _json_response("Successful Response", _ref("Product")),
                    "422": VALIDATION_RESPONSE,
                },
                request_body=_request_body("ProductCreate"),
            ),
        },
        "/products/search": {
            "get": _operation(
                ["Products"],
                "Search products by name or SKU",
                "get_searchable_products_router_products_search_get",
                {
                    "200": _json_response(
                        "Successful Response",
                        _array_of(
                            "Product",
                            "Response Get Searchable Products Router Products Search Get",
                        ),
                    ),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[
                    _parameter("q", "query", True, {"type": "string", "title": "Q"})
                ],
            )
        },
        "/products/{product_id}": {
            "get": _operation(
                ["Products"],
                "Get product by ID",
                "get_product_router_products__product_id__get",
                {
                    "200": _json_response("Successful Response", _ref("Product")),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[PRODUCT_ID_PARAMETER],
            ),
            "patch": _operation(
                ["Products"],
                "Partial update of a product",
                "update_product_router_products__product_id__patch",
                {
                    "200": _json_response("Successful Response", _ref("Product")),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[PRODUCT_ID_PARAMETER],
                request_body=_request_body("ProductUpdate"),
            ),
            "delete": _operation(
                ["Products"],
                "Remove a product",
                "delete_product_router_products__product_id__delete",
                {"204": EMPTY_RESPONSE, "422": VALIDATION_RESPONSE},
                parameters=[PRODUCT_ID_PARAMETER],
            ),
        },
        "/products/{product_id}/variants": {
            "get": _operation(
                ["Variants"],
                "Get all variants for a product",
                "get_product_variants_router_products__product_id__variants_get",
                {
                    "200": _json_response(
                        "Successful Response",
                        _array_of(
                            "ProductVariant",
                            "Response Get Product Variants Router Products "
                            " Product Id  Variants Get",
                        ),
                    ),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[PRODUCT_ID_PARAMETER],
            ),
            "post": _operation(
                ["Variants"],
                "Add variants for an existing product",
                "create_product_variant_router_products__product_id__variants_post",
                {
                    "201": _json_response(
                        "Successful Response", _ref("ProductVariant")
                    ),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[PRODUCT_ID_PARAMETER],
                request_body=_request_body("ProductVariantCreate"),
            ),
        },
        "/products/{product_id}/variants/{variant_id}": {
            "patch": _operation(
                ["Variants"],
                "Partial update of a product's variants",
                "update_product_variant_router_products__product_id__variants"
                "__variant_id__patch",
                {
                    "200": _json_response(
                        "Successful Response", _ref("ProductVariant")
                    ),
                    "422": VALIDATION_RESPONSE,
                },
                parameters=[PRODUCT_ID_PARAMETER, VARIANT_ID_PARAMETER],
                request_body=_request_body("ProductVariantUpdate"),
            ),
            "delete": _operation(
                ["Variants"],
                "Remove a product's variants",
                "delete_product_variant_router_products__product_id__variants"
                "__variant_id__delete",
                {"204": EMPTY_RESPONSE, "422": VALIDATION_RESPONSE},
                parameters=[PRODUCT_ID_PARAMETER, VARIANT_ID_PARAMETER],
            ),
        },
    }


# --- Document ---------------------------------------------------------------

DESCRIPTION = (
    "A robust Django service for managing warehouse stock using PostgreSQL and "
    "SQLModel."
)


def build_openapi() -> Dict[str, Any]:
    """Build the complete OpenAPI document served at ``/openapi.json``."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": config.app_name,
            "description": DESCRIPTION,
            "version": config.version,
        },
        "paths": build_paths(),
        "components": {"schemas": build_component_schemas()},
    }


OPENAPI_SCHEMA = build_openapi()
