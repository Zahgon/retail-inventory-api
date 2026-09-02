"""
Django settings for the Retail Inventory API.

Django is used purely as the HTTP layer: persistence stays with SQLModel /
SQLAlchemy (see ``app.core.database``) and Alembic, so no Django database
backend, session store, template engine or contrib application is configured.

The middleware list is deliberately minimal.  Django's ``CommonMiddleware``,
``CsrfViewMiddleware``, ``SecurityMiddleware`` and ``XFrameOptionsMiddleware``
would each add response headers (``Vary``, ``X-Frame-Options``, ...) or reject
unsafe methods, none of which the API has ever emitted or done.
"""

from pathlib import Path

from .core import config

BASE_DIR = Path(__file__).resolve().parent.parent

# No sessions, cookies, CSRF tokens or password hashing are used by this
# service, so the key is inert; it only exists because Django requires it.
SECRET_KEY = "retail-inventory-api"

DEBUG = config.debug

# The service performs no Host header validation, matching its previous
# behaviour; it is deployed behind a reverse proxy that does.
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "app.apps.RetailInventoryConfig",
]

MIDDLEWARE = [
    "app.middleware.security_headers.SecurityHeadersMiddleware",
    "app.middleware.exception_handler.ExceptionHandlerMiddleware",
]

ROOT_URLCONF = "app.urls"

# Trailing slashes are handled by ``app.core.routing.not_found``, which issues a
# 307 in *both* directions (adding and removing the slash) and preserves the
# request method.  Django's own APPEND_SLASH only ever adds a slash and answers
# with a 301, which would change the public contract.
APPEND_SLASH = False

DEFAULT_CHARSET = "utf-8"

# Reading ``request.body`` raises ``RequestDataTooBig`` once the declared length
# passes this ceiling, which would turn a request the API has always accepted
# into a 500 that writes no row.  The previous framework imposed no body ceiling
# of its own, so neither does this one.
DATA_UPLOAD_MAX_MEMORY_SIZE = None

USE_TZ = True

# Django exports TIME_ZONE into the process environment and calls time.tzset()
# during setup.  Leaving it at Django's own default ("America/Chicago") would
# shift every timestamp the service writes to logs/app.log and to stdout away
# from the clock the previous framework used.  ``None`` skips that step, so the
# process keeps whatever timezone the environment supplies, as it always did.
TIME_ZONE = None

# ``django.core.handlers.base`` logs a record through ``django.request`` for
# every response with a status of 400 or more.  The API already logs those
# through app.core.errors.handlers, and the previous framework emitted nothing
# of its own, so the duplicate is silenced rather than doubled into app.log.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "django.request": {"handlers": [], "level": "CRITICAL", "propagate": False},
    },
}
