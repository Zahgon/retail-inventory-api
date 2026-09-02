"""
Product views: API endpoints for creating, reading, updating and deleting products.
"""

import logging

from ..controllers import (
    create_product_controller,
    delete_product_controller,
    get_all_products_controller,
    get_product_controller,
    get_searchable_products_controller,
    update_product_controller,
)
from ..core import session_scope
from ..core.errors import ProductNotFoundException
from ..core.responses import json_response, no_content_response
from ..core.routing import route
from ..core.serialization import (
    LIMIT_PARAM,
    OFFSET_PARAM,
    PRODUCT_CREATE_BODY,
    PRODUCT_LIST_RESPONSE,
    PRODUCT_RESPONSE,
    PRODUCT_UPDATE_BODY,
    SEARCH_PARAM,
    UUID_PARAM,
)
from ..core.validation import (
    raise_for_errors,
    validate_body,
    validate_path,
    validate_query,
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# 1. READ VIEWS
# ----------------------------------------------------


def get_all_products_view(request):
    """List all products with pagination"""
    errors = []
    offset = validate_query(errors, request, "offset", OFFSET_PARAM, default=0)
    limit = validate_query(errors, request, "limit", LIMIT_PARAM, default=100)
    raise_for_errors(errors)

    with session_scope() as session:
        products = get_all_products_controller(session, offset, limit)
        return json_response(PRODUCT_LIST_RESPONSE.dump_python(products, mode="json"))


def get_searchable_products_view(request):
    """Search products by name or SKU"""
    errors = []
    q = validate_query(errors, request, "q", SEARCH_PARAM)
    raise_for_errors(errors)

    with session_scope() as session:
        products = get_searchable_products_controller(q, session)
        return json_response(PRODUCT_LIST_RESPONSE.dump_python(products, mode="json"))


def get_product_view(request, product_id):
    """Get product by ID"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        return json_response(PRODUCT_RESPONSE.dump_python(product, mode="json"))


# ----------------------------------------------------
# 2. WRITE VIEWS (POST/PATCH/DELETE)
# ----------------------------------------------------


def create_product_view(request):
    """Add a new product to the inventory"""
    errors = []
    product = validate_body(errors, request, PRODUCT_CREATE_BODY)
    raise_for_errors(errors)

    with session_scope() as session:
        created = create_product_controller(product, session)
        return json_response(PRODUCT_RESPONSE.dump_python(created, mode="json"), 201)


def update_product_view(request, product_id):
    """Partial update of a product"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    update_data = validate_body(errors, request, PRODUCT_UPDATE_BODY)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        updated = update_product_controller(product_id, update_data, session)
        return json_response(PRODUCT_RESPONSE.dump_python(updated, mode="json"))


def delete_product_view(request, product_id):
    """Remove a product"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        delete_product_controller(product_id, session)
        return no_content_response()


products = route(("GET", get_all_products_view), ("POST", create_product_view))
product_detail = route(
    ("GET", get_product_view),
    ("PATCH", update_product_view),
    ("DELETE", delete_product_view),
)
product_search = route(
    ("GET", get_searchable_products_view),
    fallthrough=(product_detail, {"product_id": "search"}),
)
