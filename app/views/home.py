"""
Home view: API endpoint for the root path, providing basic information about the API.
"""

from ..core import config
from ..core.responses import json_response
from ..core.routing import route


def read_root(request):
    return json_response(
        {
            "message": config.app_name,
            "version": config.version,
            "docs": "/docs",
            "endpoints": "/products",
        }
    )


home = route(("GET", read_root))
