"""Shared ORM metadata and SQLAlchemy session infrastructure."""

from abc import ABC
from typing import ClassVar

from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

from pysatl_experiment.persistence.sqlalchemy.connection import get_request_or_thread_id, init_db


SessionType = scoped_session[Session]


class ModelBase(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    pass


class AbstractDbStore(ABC):
    """
    Base class for SQLAlchemy-backed persistence implementations.

    The class encapsulates common database initialization logic,
    session creation, and metadata management used by all
    database storage implementations.
    """

    session: ClassVar[SessionType]

    def __init__(self, db_url="sqlite:///pysatl.sqlite"):
        """
        Initialize store configuration.

        Parameters
        ----------
        db_url : str, default="sqlite:///pysatl.sqlite"
            SQLAlchemy database connection URL.
        """
        super().__init__()
        self.db_url = db_url

    def init(self):
        """
        Initialize database infrastructure.

        Creates the database engine, configures a scoped SQLAlchemy
        session factory, and creates all registered ORM tables.
        """
        engine = init_db(self.db_url)
        AbstractDbStore.session = scoped_session(
            sessionmaker(bind=engine, autoflush=False), scopefunc=get_request_or_thread_id
        )
        ModelBase.metadata.create_all(engine)
