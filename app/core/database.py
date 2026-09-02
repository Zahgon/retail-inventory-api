"""
Database Infrastructure: Connection and Session Management.

This module configures the SQLAlchemy engine via SQLModel and defines
the dependency injection pattern used by the API endpoints to interact
with the PostgreSQL database.
"""

import logging
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from .config import config

logger = logging.getLogger(__name__)

# The Engine is the 'source' of connectivity.
# echo=True logs all generated SQL statements to the terminal—great for debugging!
engine = create_engine(
    f"postgresql://{config.db_username}:{config.db_password}@{config.db_host}:{config.db_port}/{config.db_name}",
    echo=config.debug,
    connect_args={"sslmode": "prefer"},
)


def create_db_and_tables():
    """
    Scans all SQLModel classes with 'table=True' and creates them in PostgreSQL.

    This is called during the application startup phase to ensure
    the database schema stays in sync with your Python models.
    """
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created or verified successfully.")


def get_session():
    """
    Provides a transactional scope for database operations.

    Yields a Session object and ensures it is properly closed after the
    request is finished, even if an error occurs.
    """
    # Use of Generator here so the view can handle the 'teardown'.
    # This prevents the database from running out of connections.
    with Session(engine) as session:
        yield session


# session_scope is the context manager every view opens around its work.
# It replaces the dependency-injection alias the previous framework provided:
# "Whenever a view needs a Session, call get_session() and close it afterwards."
session_scope = contextmanager(get_session)
