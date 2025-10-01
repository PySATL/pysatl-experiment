from __future__ import annotations

import json
from typing import ClassVar

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)


class AlchemyRandomValues(ModelBase):
    __tablename__ = "random_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    generator_name: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    generator_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    sample_num: Mapped[int] = mapped_column(Integer, nullable=False)  # type: ignore
    data: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "generator_name",
            "generator_parameters",
            "sample_size",
            "sample_num",
            name="uq_random_values_unique",
        ),
    )


class AlchemyRandomValuesStorage(AbstractDbStore, IRandomValuesStorage):
    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    @override
    def init(self) -> None:
        # Initialize engine and scoped session via AbstractDbStore
        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        # Access class attribute defined by AbstractDbStore after init()
        return AlchemyRandomValuesStorage.session

    @override
    def get_data(self, query: RandomValuesQuery) -> RandomValuesModel | None:
        params_json = json.dumps(query.generator_parameters)
        row: AlchemyRandomValues | None = (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
                AlchemyRandomValues.sample_num == int(query.sample_num),
            )
            .one_or_none()
        )
        if row is None:
            return None
        return RandomValuesModel(
            generator_name=query.generator_name,
            generator_parameters=query.generator_parameters,
            sample_size=query.sample_size,
            sample_num=query.sample_num,
            data=json.loads(row.data),
        )

    @override
    def insert_data(self, data: RandomValuesModel) -> None:
        params_json = json.dumps(data.generator_parameters)
        entity = AlchemyRandomValues(
            generator_name=data.generator_name,
            generator_parameters=params_json,
            sample_size=int(data.sample_size),
            sample_num=int(data.sample_num),
            data=json.dumps(data.data),
        )
        existing: AlchemyRandomValues | None = (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == entity.generator_name,
                AlchemyRandomValues.generator_parameters == entity.generator_parameters,
                AlchemyRandomValues.sample_size == entity.sample_size,
                AlchemyRandomValues.sample_num == entity.sample_num,
            )
            .one_or_none()
        )
        if existing is None:
            self._get_session().add(entity)
        else:
            existing.data = entity.data
        self._get_session().commit()

    @override
    def delete_data(self, query: RandomValuesQuery) -> None:
        params_json = json.dumps(query.generator_parameters)
        (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
                AlchemyRandomValues.sample_num == int(query.sample_num),
            )
            .delete()
        )
        self._get_session().commit()

    @override
    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        params_json = json.dumps(query.generator_parameters)
        return (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
            )
            .count()
        )

    @override
    def insert_all_data(self, query: RandomValuesAllModel) -> None:
        params_json = json.dumps(query.generator_parameters)
        # delete existing
        (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
            )
            .delete()
        )
        # insert new
        for i, sample in enumerate(query.data, start=1):
            self._get_session().add(
                AlchemyRandomValues(
                    generator_name=query.generator_name,
                    generator_parameters=params_json,
                    sample_size=int(query.sample_size),
                    sample_num=i,
                    data=json.dumps(sample),
                )
            )
        self._get_session().commit()

    @override
    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel] | None:
        params_json = json.dumps(query.generator_parameters)
        rows: list[AlchemyRandomValues] = (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
            )
            .order_by(AlchemyRandomValues.sample_num)
            .all()
        )
        return [
            RandomValuesModel(
                generator_name=query.generator_name,
                generator_parameters=query.generator_parameters,
                sample_size=query.sample_size,
                sample_num=row.sample_num,
                data=json.loads(row.data),
            )
            for row in rows
        ]

    @override
    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        params_json = json.dumps(query.generator_parameters)
        (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
            )
            .delete()
        )
        self._get_session().commit()

    @override
    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel] | None:
        params_json = json.dumps(query.generator_parameters)
        rows: list[AlchemyRandomValues] = (
            self._get_session()
            .query(AlchemyRandomValues)
            .filter(
                AlchemyRandomValues.generator_name == query.generator_name,
                AlchemyRandomValues.generator_parameters == params_json,
                AlchemyRandomValues.sample_size == int(query.sample_size),
            )
            .order_by(AlchemyRandomValues.sample_num)
            .limit(int(query.count))
            .all()
        )
        return [
            RandomValuesModel(
                generator_name=query.generator_name,
                generator_parameters=query.generator_parameters,
                sample_size=query.sample_size,
                sample_num=row.sample_num,
                data=json.loads(row.data),
            )
            for row in rows
        ]
