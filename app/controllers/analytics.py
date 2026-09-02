"""
Analytics controllers: Business logic for generating reports and insights from the inventory system.
"""

import logging

from sqlmodel import Session, func, select

from ..models import (
    Product,
    ProductVariant,
)

logger = logging.getLogger(__name__)


def get_inventory_value_controller(session: Session):
    """
    Calculates the aggregate value (price * quantity) of all inventory.

    Utilizes SQL-side aggregation (func.sum) to ensure high performance
    even with thousands of rows, avoiding Python-level loops.
    """

    logger.info("Executing database-side aggregation for total inventory value.")

    # Calculate (price * quantity) per row and sum them up in the DB engine
    statement = select(func.sum(Product.price * ProductVariant.quantity)).join(
        ProductVariant, Product.id == ProductVariant.product_id
    )
    result = session.exec(statement).one()
    total_value = result or 0.0

    logger.info(
        "Total inventory value successfully calculated",
        extra={"total_value": total_value},
    )

    return {"Total Inventory Value $": total_value}
