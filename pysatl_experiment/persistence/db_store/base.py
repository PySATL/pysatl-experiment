"""Base SQLAlchemy ORM definitions used by database stores."""

from sqlalchemy.orm import DeclarativeBase, Session, scoped_session


SessionType = scoped_session[Session]


class ModelBase(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    pass
