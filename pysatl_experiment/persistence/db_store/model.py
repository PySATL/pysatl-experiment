"""Base implementation for SQLAlchemy-backed storage classes."""

from abc import ABC
from typing import ClassVar

from sqlalchemy.orm import scoped_session, sessionmaker
from typing_extensions import override

from pysatl_experiment.persistence import IStore
from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.db_init import get_request_or_thread_id, init_db


class AbstractDbStore(IStore, ABC):
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

    @override
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
