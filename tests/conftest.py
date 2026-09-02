"""
Defines pytest fixtures for testing the app with an isolated in-memory
database, so tests never touch the real PostgreSQL instance.
"""

import os
from json import dumps
from urllib.parse import urlsplit

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

import pytest  # noqa: E402
from django.test import Client  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.core import database  # noqa: E402

# A single shared in-memory connection, so every session opened during a test
# sees the same data.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# The views open their own sessions from the module-level engine, so the test
# engine is installed in its place.
database.engine = engine


class JSONClient(Client):
    """
    Test client that sends JSON request bodies and replays temporary redirects.

    A missing or extra trailing slash is answered with a temporary redirect,
    which preserves the method and the body, so the request is simply re-sent
    to the location that came back.
    """

    def _dispatch(self, method, path, json=None):
        kwargs = {}

        if json is not None:
            kwargs = {"data": dumps(json), "content_type": "application/json"}

        send = getattr(Client, method)
        response = send(self, path, **kwargs)

        while response.status_code == 307:
            location = urlsplit(response["Location"])
            path = location.path

            if location.query:
                path = f"{path}?{location.query}"

            response = send(self, path, **kwargs)

        return response

    def get(self, path, **kwargs):
        return self._dispatch("get", path, **kwargs)

    def post(self, path, **kwargs):
        return self._dispatch("post", path, **kwargs)

    def patch(self, path, **kwargs):
        return self._dispatch("patch", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._dispatch("delete", path, **kwargs)


@pytest.fixture(name="session")
def session_fixture():
    with Session(engine) as session:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        yield session
        SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session):
    yield JSONClient()
