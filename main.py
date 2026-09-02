"""
Application launcher.

Creates the ASGI app, registers the URL configuration, and manages the
database lifespan.
"""

import logging
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

from app.core import config, create_db_and_tables, setup_logging  # noqa: E402, F401
from app.core.errors import DatabaseException  # noqa: E402
from app.middleware.exception_handler import SERVER_ERROR_KEY  # noqa: E402

logger = logging.getLogger(__name__)


async def lifespan(scope, receive, send):
    """
    Handles the application startup and shutdown events.

    Ensures the database engine is ready and tables are created before
    the API starts accepting traffic.
    """
    while True:
        message = await receive()

        if message["type"] == "lifespan.startup":
            logger.info(
                "Lifespan Startup: Verifying database connectivity and creating tables."
            )
            # A failure must be announced as `lifespan.startup.failed` before it
            # propagates: that message is what aborts the boot.  An exception that
            # escapes unannounced makes the server conclude the application has no
            # lifespan support and serve traffic against an unverified database.
            try:
                try:
                    create_db_and_tables()
                except Exception as e:
                    raise DatabaseException(details={"error": str(e)})
            except BaseException:
                await send(
                    {
                        "type": "lifespan.startup.failed",
                        "message": traceback.format_exc(),
                    }
                )
                raise
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            logger.info("Lifespan Shutdown: Cleaning up resources.")
            await send({"type": "lifespan.shutdown.complete"})
            return


def create_app():
    """
    Builds the ASGI callable served by the application server.

    The URL configuration, middleware stack and exception handlers are declared
    in the settings module; lifespan events are handled here so that startup
    runs once when the server boots rather than on import.
    """
    application = get_asgi_application()

    async def entrypoint(scope, receive, send):
        if scope["type"] == "lifespan":
            await lifespan(scope, receive, send)
            return

        await application(scope, receive, send)

        # The previous framework's server-error layer always re-raised after the
        # 500 had been written, which is what makes the server log the exception
        # and close the connection.  Swallowing it keeps the connection alive and
        # loses the server-side record, both observable by a client.
        server_error = scope.pop(SERVER_ERROR_KEY, None)
        if server_error is not None:
            raise server_error

    return entrypoint


app = create_app()
