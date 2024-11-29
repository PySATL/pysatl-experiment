import importlib
import json
import sqlite3
from typing import ClassVar

import numpy as np
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, scoped_session, sessionmaker
from typing_extensions import override

from stattest.persistence.models import IResultStore
from stattest.persistence.sql_lite_store import (
    ModelBase,
    SessionType,
    get_request_or_thread_id,
    init_db,
)


class ResultModel(ModelBase):
    """
    Result database model.
    """
    __tablename__ = "result"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    module: Mapped[str] = mapped_column(String)
    className: Mapped[str] = mapped_column(String)
    data: Mapped[str] = mapped_column(String, nullable=False)


class ResultSqLiteStore(IResultStore):
    session: ClassVar[SessionType]
    __separator = ';'

    def __init__(self, name='pysatl.sqlite'):
        super().__init__()
        self.name = name

    def init(self, **kwargs):
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        engine = init_db("sqlite:///" + self.name)
        ResultSqLiteStore.session = scoped_session(
            sessionmaker(bind=engine, autoflush=False), scopefunc=get_request_or_thread_id
        )
        ModelBase.metadata.create_all(engine)

    @override
    def insert_result(self, result_id: str, result: any):
        """
        Insert benchmark to store.

        :param test_code: test code
        :param benchmark:  benchmark
        """

        json_data = json.dumps(result.__dict__)
        data = ResultModel(id=result_id, module=result.__module__,
                           className=result.__class__.__name__, data=json_data)
        ResultSqLiteStore.session.add(data)
        ResultSqLiteStore.session.commit()

    @override
    def get_result(self, result_id: str) -> any:
        """
        Get benchmark from store.

        :param result_id: test code

        :return benchmark on None
        """
        result = ResultSqLiteStore.session.query(ResultModel).get(result_id)
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
        result = (ResultSqLiteStore.session.query(ResultModel)
                  .order_by(ResultModel.id).offset(offset).limit(limit)).all()
        result = [getattr(importlib.import_module(r.module), r.className)(**json.loads(r.data))
                  for r in result]
        return result
