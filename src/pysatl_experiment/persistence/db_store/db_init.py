"""Database initialization and session-scoping utilities."""

import logging
import threading
from contextvars import ContextVar
from typing import Any, Final

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import ArgumentError, NoSuchModuleError
from sqlalchemy.pool import StaticPool

from src.pysatl_experiment.exceptions import OperationalException


logger = logging.getLogger(__name__)

REQUEST_ID_CTX_KEY: Final[str] = "request_id"
_request_id_ctx_var: ContextVar[str | None] = ContextVar(REQUEST_ID_CTX_KEY, default=None)


def get_request_or_thread_id() -> str | None:
    """
    Return current request identifier or thread identifier.

    Returns
    -------
    str | None
        Request identifier from the current context if available.
        Otherwise, the current thread identifier.
    """
    request_id = _request_id_ctx_var.get()
    if request_id is None:
        # When not in request context - use thread id
        request_id = str(threading.current_thread().ident)

    return request_id


_SQL_DOCS_URL = "http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls"


def init_db(db_url: str) -> Engine:
    """Create and configure a SQLAlchemy engine.

    Parameters
    ----------
    db_url : str
        Database connection URL.

    Returns
    -------
    Engine
        Configured SQLAlchemy engine.

    Raises
    ------
    OperationalException
        If the database URL is invalid.
    """
    kwargs: dict[str, Any] = {}

    if db_url == "sqlite:///":
        raise OperationalException(f"Bad db-url {db_url}. For in-memory database, please use `sqlite://`.")
    if db_url == "sqlite://":
        kwargs.update(
            {
                "poolclass": StaticPool,
            }
        )
    # Take care of thread ownership
    if db_url.startswith("sqlite://"):
        kwargs.update(
            {
                "connect_args": {"check_same_thread": False},
            }
        )

    try:
        engine = create_engine(db_url, future=True, **kwargs)
    except (ArgumentError, NoSuchModuleError):
        raise OperationalException(
            f"Given value for db_url: '{db_url}' is no valid database URL! (See {_SQL_DOCS_URL})"
        )
    return engine
