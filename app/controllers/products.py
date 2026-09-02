"""
Product controllers: Business logic for managing products in the inventory system.
"""

import logging
import re
from typing import Optional
from uuid import UUID

from sqlmodel import Session, func, select

from ..models import (
    Product,
    ProductCreate,
    ProductUpdate,
)
from ..utils import generate_sku

logger = logging.getLogger(__name__)


def get_all_products_controller(
    session: Session,
    offset: int = 0,
    limit: int = 100,
):
    """
    Retrieves a list of products using offset/limit pagination.

    Args:
        offset: The number of items to skip.
        limit: The maximum number of items to return (capped at 100).
    """
    statement = select(Product).offset(offset).limit(limit)
    products = session.exec(statement).all()
    logger.info("Products retrieved successfully", extra={"count": len(products)})
    return products


def sku_searchable(q: str) -> bool:
    """
    Validates if the search query is a valid SKU format.
    """
    pattern = r"^[A-Za-z]{2}-\d{4}$"
    return bool(re.match(pattern, q.strip()))


def get_searchable_products_controller(q: str, session: Session):
    """
    Retrieves products based on a search query.
    """
    if sku_searchable(q):
        # Exact match on sku column
        logger.info("Performing SKU search", extra={"query": q})
        product = session.exec(select(Product).where(Product.sku == q.upper())).first()
        return [product] if product else []
    else:
        # TODO: semantic search - RAG (vector Database)
        logger.info("Performing name search", extra={"query": q})
        statement = select(Product).where(Product.name.ilike(f"%{q}%"))
        return session.exec(statement).all()


def get_product_controller(product_id: UUID, session: Session) -> Optional[Product]:
    """
    Fetches a single product record.
    """
    logger.info("Attempting to fetch product", extra={"product_id": product_id})
    product = session.get(Product, product_id)
    if product:
        logger.info("Product fetched successfully", extra={"product_id": product_id})
    return product


def create_product_controller(product: ProductCreate, session: Session) -> Product:
    """
    Persists a new product record.

    Validates input using ProductCreate and maps it to the Product table model.
    The database automatically handles ID generation and stock-status logic.
    """

    logger.info(
        "Creating new product",
        extra={
            "category": product.category,
            "product_name": product.name,
            "color": product.color,
            "price": product.price,
            "collection": product.collection,
            "coming_soon": product.coming_soon,
        },
    )
    # Count existing products in this category to generate the next sequential SKU
    category_count = session.exec(
        select(func.count()).where(Product.category == product.category)
    ).one()
    sku = generate_sku(product.category, category_count + 1)

    # 1. Converts the Pydantic schema into a SQLModel Table instance, injecting the SKU
    db_product = Product.model_validate(product, update={"sku": sku})
    # 2. Add to session and commit to persist
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    logger.info(
        "Product created successfully",
        extra={"product_id": db_product.id, "sku": db_product.sku},
    )

    return db_product


def update_product_controller(
    product_id: UUID, update_data: ProductUpdate, session: Session
) -> Product:
    """
    Updates specific fields of an existing product.

    Uses 'exclude_unset=True' to ensure only fields provided in the
    request body are modified, preserving other existing values.
    """

    logger.info(
        "Updating product",
        extra={
            "product_id": product_id,
            "category": update_data.category,
            "product_name": update_data.name,
            "color": update_data.color,
            "price": update_data.price,
            "collection": update_data.collection,
            "coming_soon": update_data.coming_soon,
        },
    )

    db_product = session.get(Product, product_id)
    # Return None if there is no product
    if not db_product:
        logger.warning("Product not found", extra={"product_id": product_id})
        return None

    # Update only the fields provided in update_data
    product_data = update_data.model_dump(exclude_unset=True)

    # Update the database product with the new data
    for key, value in product_data.items():
        setattr(db_product, key, value)

    # Add to session and commit to persist
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    logger.info(
        "Product updated successfully",
        extra={
            "product_id": product_id,
            "category": db_product.category,
            "product_name": db_product.name,
            "color": db_product.color,
            "price": db_product.price,
            "collection": db_product.collection,
            "coming_soon": db_product.coming_soon,
        },
    )

    return db_product


def delete_product_controller(product_id: UUID, session: Session) -> Optional[Product]:
    """
    Deletes a product from the database.
    """
    logger.info("Attempting to delete product", extra={"product_id": product_id})
    db_product = session.get(Product, product_id)

    if not db_product:
        return None

    session.delete(db_product)
    session.commit()

    logger.info("Product deleted successfully", extra={"product_id": product_id})

    return db_product
