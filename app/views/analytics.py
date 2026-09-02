"""
Analytics views: API endpoints for inventory analytics and reporting.
"""

import logging

from ..controllers import get_inventory_value_controller
from ..core import session_scope
from ..core.responses import json_response
from ..core.routing import route
from ..core.serialization import INVENTORY_VALUE_RESPONSE
from .products import product_detail

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# ANALYTICS VIEWS
# ----------------------------------------------------


def get_inventory_value_view(request):
    """Calculate the total monetary value of the current inventory"""
    with session_scope() as session:
        return json_response(
            INVENTORY_VALUE_RESPONSE.dump_python(
                get_inventory_value_controller(session), mode="json"
            )
        )


inventory_value = route(
    ("GET", get_inventory_value_view),
    fallthrough=(product_detail, {"product_id": "total_value"}),
)
