"""
Response models.

The previous framework declared a ``response_model`` on every route and used it
to project the handler's return value onto the public schema before rendering
it.  The adapters below are that projection, kept in one place so the views read
the same way the routes did.

Key order in the rendered document is *declaration* order.  The previous
implementation derived it from an unordered set, which made it differ from one
worker process to the next; it was therefore never part of the public contract
and could not be reproduced.  See "The crux" in truth.md.
"""

from typing import Annotated, Dict, List
from uuid import UUID

from pydantic import Field, TypeAdapter

from ..models import (
    HealthResponse,
    Product,
    ProductCreate,
    ProductUpdate,
    ProductVariant,
    ProductVariantCreate,
    ProductVariantUpdate,
)

HEALTH_RESPONSE = TypeAdapter(HealthResponse)
INVENTORY_VALUE_RESPONSE = TypeAdapter(Dict[str, float])
PRODUCT_RESPONSE = TypeAdapter(Product)
PRODUCT_LIST_RESPONSE = TypeAdapter(List[Product])
VARIANT_RESPONSE = TypeAdapter(ProductVariant)
VARIANT_LIST_RESPONSE = TypeAdapter(List[ProductVariant])

PRODUCT_CREATE_BODY = TypeAdapter(ProductCreate)
PRODUCT_UPDATE_BODY = TypeAdapter(ProductUpdate)
VARIANT_CREATE_BODY = TypeAdapter(ProductVariantCreate)
VARIANT_UPDATE_BODY = TypeAdapter(ProductVariantUpdate)

UUID_PARAM = TypeAdapter(UUID)
OFFSET_PARAM = TypeAdapter(int)
LIMIT_PARAM = TypeAdapter(Annotated[int, Field(le=100)])
SEARCH_PARAM = TypeAdapter(str)
