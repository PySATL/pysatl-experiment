"""
Database storage implementation for critical values and distributions.

This module contains SQLAlchemy ORM models and a database-backed
storage implementation used for persisting critical values and
empirical distributions of statistical criteria.
"""

from typing import ClassVar, cast

from sqlalchemy import Float, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from src.pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from src.pysatl_experiment.persistence.db_store.model import AbstractDbStore
from src.pysatl_experiment.persistence.models import ICriticalValueStore


class Distribution(ModelBase):
    """
    ORM model representing a stored empirical distribution.

    Attributes
    ----------
    code : str
        Unique code of the statistical criterion.
    size : int
        Sample size associated with the distribution.
    data : str
        Serialized distribution values separated by a delimiter.
    """

    __tablename__ = "distribution"
    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # type: ignore
    size: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    data: Mapped[str] = mapped_column(String(), nullable=False)  # type: ignore


class CriticalValue(ModelBase):
    """
    ORM model representing a stored critical value.

    Attributes
    ----------
    code : str
        Unique code of the statistical criterion.
    size : int
        Sample size associated with the critical value.
    sl : float
        Significance level.
    lower_value : float | None
        Lower critical value.
    upper_value : float | None
        Upper critical value for two-sided criteria.
    """

    __tablename__ = "critical_value"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # type: ignore
    size: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    sl: Mapped[float] = mapped_column(Float, primary_key=True)  # type: ignore
    lower_value: Mapped[float] = mapped_column(Float, nullable=True)
    upper_value: Mapped[float] = mapped_column(Float, nullable=True)


class CriticalValueDbStore(AbstractDbStore, ICriticalValueStore):
    """
    Database-backed storage for critical values and distributions.

    The store provides persistence and retrieval operations for
    critical values and empirical distributions associated with
    statistical criteria.

    Notes
    -----
    Distribution values are serialized into a single string using
    an internal separator before being written to the database.
    """

    session: ClassVar[SessionType]
    __separator = ";"

    @override
    def insert_critical_value(self, code: str, size: int, sl: float, value: float | tuple[float, float]):
        """
        Store a critical value in the database.

        Parameters
        ----------
        code : str
            Criterion identifier.
        size : int
            Sample size.
        sl : float
            Significance level.
        value : float | tuple[float, float]
            Critical value. For two-sided criteria a tuple containing
            lower and upper bounds may be provided.
        """
        if isinstance(value, tuple):
            lower_value, upper_value = value
        else:
            lower_value, upper_value = value, None

        try:
            CriticalValueDbStore.session.add(
                CriticalValue(
                    code=code,
                    size=int(size),
                    sl=sl,
                    lower_value=lower_value,
                    upper_value=upper_value,
                )
            )
            CriticalValueDbStore.session.commit()
        except IntegrityError:
            CriticalValueDbStore.session.rollback()

    @override
    def insert_distribution(self, code: str, size: int, data: list[float]):
        """
        Store an empirical distribution in the database.

        Parameters
        ----------
        code : str
            Criterion identifier.
        size : int
            Sample size.
        data : list[float]
            Distribution values to persist.
        """
        data_to_insert = CriticalValueDbStore.__separator.join(map(str, data))
        try:
            CriticalValueDbStore.session.add(Distribution(code=code, size=int(size), data=data_to_insert))
            CriticalValueDbStore.session.commit()
        except IntegrityError:
            CriticalValueDbStore.session.rollback()

    @override
    def get_critical_value(self, code: str, size: int, sl: float) -> float | tuple[float, float] | None:
        """Retrieve a critical value from storage.

        Parameters
        ----------
        code : str
            Criterion identifier.
        size : int
            Sample size.
        sl : float
            Significance level.

        Returns
        -------
        float | tuple[float, float] | None
            Stored critical value, a pair of critical values for
            two-sided criteria, or ``None`` if no record exists.
        """
        critical_value = CriticalValueDbStore.session.get(CriticalValue, (code, size, sl))
        if critical_value is not None:
            if critical_value.upper_value is not None:
                return (cast(float, critical_value.lower_value), cast(float, critical_value.upper_value))
            else:
                return cast(float, critical_value.lower_value)
        else:
            return None

    @override
    def get_distribution(self, code: str, size: int) -> list[float] | None:
        """Retrieve an empirical distribution from storage.

        Parameters
        ----------
        code : str
            Criterion identifier.
        size : int
            Sample size.

        Returns
        -------
        list[float] | None
            Distribution values if found, otherwise ``None``.
        """
        distribution = CriticalValueDbStore.session.get(Distribution, (code, size))
        if distribution is not None:
            return [float(x) for x in distribution.data.split(CriticalValueDbStore.__separator)]
        else:
            return None


# TODO: Mapped ORMs?
