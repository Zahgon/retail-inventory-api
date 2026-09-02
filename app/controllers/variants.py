"""
Variant controllers: Business logic for managing product variants in the inventory system.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from ..models import (
    ProductVariant,
    ProductVariantCreate,
    ProductVariantUpdate,
)

logger = logging.getLogger(__name__)


def get_product_variants_controller(
    product_id: UUID, session: Session
) -> list[ProductVariant]:
    """
    Fetches the variants of the selected product.
    """
    logger.info(
        "Attempting to fetch product variants", extra={"product_id": product_id}
    )
    statement = select(ProductVariant).where(ProductVariant.product_id == product_id)
    variants = session.exec(statement).all()
    logger.info(
        "Product variants fetched successfully",
        extra={"product_id": product_id, "count": len(variants)},
    )
    return variants


def create_product_variant_controller(
    product_id: UUID, variant: ProductVariantCreate, session: Session
) -> ProductVariant:
    """
    Persists a new variant for the given product.

    Links the variant to its parent product via product_id
    and delegates ID generation to PostgreSQL.
    """

    logger.info(
        "Creating product variant",
        extra={
            "product_id": product_id,
            "size": variant.size,
            "quantity": variant.quantity,
            "in_stock": variant.in_stock,
        },
    )

    # 1. Converts the Pydantic schema into a SQLModel Table instance
    db_variant = ProductVariant.model_validate(
        variant, update={"product_id": product_id}
    )
    # 2. Add to session and commit to persist
    session.add(db_variant)
    session.commit()
    session.refresh(db_variant)  # Syncs db_variant with the DB-generated ID

    logger.info(
        "Product variant created successfully",
        extra={"variant_id": db_variant.id, "product_id": product_id},
    )

    return db_variant


def update_product_variant_controller(
    variant_id: UUID, update_data: ProductVariantUpdate, session: Session
) -> ProductVariant:
    """
    Updates a product variant by its ID.
    Applies only the fields provided in the request body.
    Returns the updated variant, or None if not found.
    """

    logger.info(
        "Updating product variant",
        extra={
            "variant_id": variant_id,
            "size": update_data.size,
            "quantity": update_data.quantity,
            "in_stock": update_data.in_stock,
        },
    )

    db_variant = session.get(ProductVariant, variant_id)
    # Return None if there is no variant
    if not db_variant:
        logger.warning("Product variant not found", extra={"variant_id": variant_id})
        return None

    # Update only the fields provided in update_data
    variant_data = update_data.model_dump(exclude_unset=True)

    # Update the database product with the new data
    for key, value in variant_data.items():
        setattr(db_variant, key, value)

    # Add to session and commit to persist
    session.add(db_variant)
    session.commit()
    session.refresh(db_variant)

    logger.info(
        "Product variant updated successfully",
        extra={
            "variant_id": variant_id,
            "size": db_variant.size,
            "quantity": db_variant.quantity,
            "in_stock": db_variant.in_stock,
        },
    )

    return db_variant


def delete_product_variant_controller(
    variant_id: UUID, session: Session
) -> Optional[ProductVariant]:
    """
    Deletes the variants of a product from the database.
    """
    logger.info(
        "Attempting to delete product variant", extra={"variant_id": variant_id}
    )
    db_variant = session.get(ProductVariant, variant_id)

    if not db_variant:
        return None

    session.delete(db_variant)
    session.commit()

    logger.info(
        "Product variant deleted successfully", extra={"variant_id": variant_id}
    )

    return db_variant
