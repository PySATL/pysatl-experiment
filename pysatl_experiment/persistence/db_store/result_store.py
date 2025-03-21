import importlib
import json
from typing import Any, ClassVar

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from pysatl_experiment.persistence.db_store import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.models import IResultStore


class ResultModel(ModelBase):
    """
    Result database model.
    """

    __tablename__ = "result"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    module: Mapped[str] = mapped_column(String)
    className: Mapped[str] = mapped_column(String)
    data: Mapped[str] = mapped_column(String, nullable=False)


class ResultDbStore(AbstractDbStore, IResultStore):
    session: ClassVar[SessionType]
    __separator = ";"

    @override
    def insert_result(self, result_id: str, result: Any):
        """
        Insert benchmark to store.

        :param test_code: test code
        :param benchmark:  benchmark
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
        """
        Get benchmark from store.

        :param result_id: test code

        :return benchmark on None
        """
        result = ResultDbStore.session.get(ResultModel, result_id)
        if not result:
            return None

        module = importlib.import_module(result.module)
        return getattr(module, result.className)(**json.loads(result.data))

    @override
    def get_results(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Get several powers from store.

        :param offset: offset
        :param limit: limit

        :return list of PowerResultModel
        """
        result = (
            ResultDbStore.session.query(ResultModel)
            .order_by(ResultModel.id)
            .offset(offset)
            .limit(limit)
        ).all()
        result = [
            getattr(importlib.import_module(r.module), r.className)(**json.loads(r.data))
            for r in result
        ]
        return result
