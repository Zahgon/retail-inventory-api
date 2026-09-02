"""
Variant views: API endpoints for managing product variants.
"""

import logging

from ..controllers import (
    create_product_variant_controller,
    delete_product_variant_controller,
    get_product_controller,
    get_product_variants_controller,
    update_product_variant_controller,
)
from ..core import session_scope
from ..core.errors import (
    ProductNotFoundException,
    ProductVariantNotFoundException,
)
from ..core.responses import json_response, no_content_response
from ..core.routing import route
from ..core.serialization import (
    UUID_PARAM,
    VARIANT_CREATE_BODY,
    VARIANT_LIST_RESPONSE,
    VARIANT_RESPONSE,
    VARIANT_UPDATE_BODY,
)
from ..core.validation import raise_for_errors, validate_body, validate_path

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. READ VIEWS
# ----------------------------------------------------


def get_product_variants_view(request, product_id):
    """Get all variants for a product"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        variants = get_product_variants_controller(product_id, session)
        return json_response(VARIANT_LIST_RESPONSE.dump_python(variants, mode="json"))


# ----------------------------------------------------
# 2. WRITE VIEWS (POST/PATCH/DELETE)
# ----------------------------------------------------


def create_product_variant_view(request, product_id):
    """Add variants for an existing product"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    variant = validate_body(errors, request, VARIANT_CREATE_BODY)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        created = create_product_variant_controller(product_id, variant, session)
        return json_response(VARIANT_RESPONSE.dump_python(created, mode="json"), 201)


def update_product_variant_view(request, product_id, variant_id):
    """Partial update of a product's variants"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    variant_id = validate_path(errors, "variant_id", variant_id, UUID_PARAM)
    update_data = validate_body(errors, request, VARIANT_UPDATE_BODY)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        variant = update_product_variant_controller(variant_id, update_data, session)
        if not variant:
            raise ProductVariantNotFoundException(variant_id)
        return json_response(VARIANT_RESPONSE.dump_python(variant, mode="json"))


def delete_product_variant_view(request, product_id, variant_id):
    """Remove a product's variants"""
    errors = []
    product_id = validate_path(errors, "product_id", product_id, UUID_PARAM)
    variant_id = validate_path(errors, "variant_id", variant_id, UUID_PARAM)
    raise_for_errors(errors)

    with session_scope() as session:
        product = get_product_controller(product_id, session)
        if not product:
            raise ProductNotFoundException(product_id)
        variant = delete_product_variant_controller(variant_id, session)
        if not variant:
            raise ProductVariantNotFoundException(variant_id)
        return no_content_response()


product_variants = route(
    ("GET", get_product_variants_view), ("POST", create_product_variant_view)
)
variant_detail = route(
    ("PATCH", update_product_variant_view), ("DELETE", delete_product_variant_view)
)
