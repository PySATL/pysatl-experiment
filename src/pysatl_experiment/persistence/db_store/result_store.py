"""
Database storage implementation for experiment results.

The module provides ORM models and storage classes used to
persist arbitrary result objects and reconstruct them from
stored metadata.
"""

import importlib
import json
from typing import Any, ClassVar

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from pysatl_experiment.persistence.db_store import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.interfaces import IResultStore


class ResultModel(ModelBase):
    """ORM model representing a serialized experiment result."""

    __tablename__ = "result"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    module: Mapped[str] = mapped_column(String)
    className: Mapped[str] = mapped_column(String)
    data: Mapped[str] = mapped_column(String, nullable=False)


class ResultDbStore(AbstractDbStore, IResultStore):
    """Database-backed storage for serialized experiment results."""

    session: ClassVar[SessionType]
    __separator = ";"

    @override
    def insert_result(self, result_id: str, result: Any) -> None:
        """Insert benchmark to store.

        Parameters
        ----------
        result_id : str
            Result identifier.
        result : Any
            Result object to persist.
        """
        json_data = json.dumps(result.__dict__)
        data = ResultModel(
            id=result_id,
            module=result.__module__,
            className=result.__class__.__name__,
            data=json_data,
        )
        ResultDbStore.session.add(data)
        ResultDbStore.session.commit()

    @override
    def get_result(self, result_id: str) -> Any:
        """Retrieve a result from storage.

        Parameters
        ----------
        result_id : str
            Result identifier.

        Returns
        -------
        Any
            Restored result object or ``None`` if not found.
        """
        result = ResultDbStore.session.get(ResultModel, result_id)
        if not result:
            return None

        module = importlib.import_module(result.module)
        return getattr(module, result.className)(**json.loads(result.data))

    @override
    def get_results(self, offset: int, limit: int):  # -> [PowerResultModel]:  # TODO: annotation!
        """Retrieve several stored results.

        Parameters
        ----------
        offset : int
            Number of records to skip.
        limit : int
            Maximum number of records to return.

        Returns
        -------
        list[Type[ResultModel]]
            List of restored result objects.
        """
        result = (ResultDbStore.session.query(ResultModel).order_by(ResultModel.id).offset(offset).limit(limit)).all()
        result = [getattr(importlib.import_module(r.module), r.className)(**json.loads(r.data)) for r in result]
        return result
