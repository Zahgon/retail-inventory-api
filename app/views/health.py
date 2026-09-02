"""
Health views: API endpoints for health checks and system status.
"""

import time

from ..core import config
from ..core.responses import json_response
from ..core.routing import route
from ..core.serialization import HEALTH_RESPONSE
from ..models import HealthResponse


def health_check(request):
    return json_response(
        HEALTH_RESPONSE.dump_python(
            HealthResponse(
                status="ok",
                version=config.version,
                uptime=time.time() - config.start_time,
            ),
            mode="json",
        )
    )


health = route(("GET", health_check), ("HEAD", health_check))
