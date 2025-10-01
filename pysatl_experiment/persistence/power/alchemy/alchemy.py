from __future__ import annotations

import json
from typing import ClassVar

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.model.power.power import IPowerStorage, PowerModel, PowerQuery


class AlchemyPower(ModelBase):
    __tablename__ = "power"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    experiment_id: Mapped[int] = mapped_column(Integer, nullable=False)  # type: ignore
    criterion_code: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    criterion_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    alternative_code: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    alternative_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    monte_carlo_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    significance_level: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # type: ignore
    results_criteria: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "criterion_code",
            "criterion_parameters",
            "sample_size",
            "alternative_code",
            "alternative_parameters",
            "monte_carlo_count",
            "significance_level",
            name="uq_power_unique",
        ),
    )


class AlchemyPowerStorage(AbstractDbStore, IPowerStorage):
    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    @override
    def init(self) -> None:
        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        return AlchemyPowerStorage.session

    @override
    def get_data(self, query: PowerQuery) -> PowerModel | None:
        params_json = json.dumps(query.criterion_parameters)
        alt_params_json = json.dumps(query.alternative_parameters)
        row: AlchemyPower | None = (
            self._get_session()
            .query(AlchemyPower)
            .filter(
                AlchemyPower.criterion_code == query.criterion_code,
                AlchemyPower.criterion_parameters == params_json,
                AlchemyPower.sample_size == int(query.sample_size),
                AlchemyPower.alternative_code == query.alternative_code,
                AlchemyPower.alternative_parameters == alt_params_json,
                AlchemyPower.monte_carlo_count == int(query.monte_carlo_count),
                AlchemyPower.significance_level == float(query.significance_level),
            )
            .one_or_none()
        )
        if row is None:
            return None
        return PowerModel(
            experiment_id=int(row.experiment_id),
            criterion_code=query.criterion_code,
            criterion_parameters=query.criterion_parameters,
            sample_size=query.sample_size,
            alternative_code=query.alternative_code,
            alternative_parameters=query.alternative_parameters,
            monte_carlo_count=query.monte_carlo_count,
            significance_level=query.significance_level,
            results_criteria=json.loads(row.results_criteria),
        )

    @override
    def insert_data(self, data: PowerModel) -> None:
        params_json = json.dumps(data.criterion_parameters)
        alt_params_json = json.dumps(data.alternative_parameters)
        existing: AlchemyPower | None = (
            self._get_session()
            .query(AlchemyPower)
            .filter(
                AlchemyPower.criterion_code == data.criterion_code,
                AlchemyPower.criterion_parameters == params_json,
                AlchemyPower.sample_size == int(data.sample_size),
                AlchemyPower.alternative_code == data.alternative_code,
                AlchemyPower.alternative_parameters == alt_params_json,
                AlchemyPower.monte_carlo_count == int(data.monte_carlo_count),
                AlchemyPower.significance_level == float(data.significance_level),
            )
            .one_or_none()
        )
        if existing is None:
            entity = AlchemyPower(
                experiment_id=int(data.experiment_id),
                criterion_code=data.criterion_code,
                criterion_parameters=params_json,
                sample_size=int(data.sample_size),
                alternative_code=data.alternative_code,
                alternative_parameters=alt_params_json,
                monte_carlo_count=int(data.monte_carlo_count),
                significance_level=float(data.significance_level),
                results_criteria=json.dumps(data.results_criteria),
            )
            self._get_session().add(entity)
        else:
            existing.experiment_id = int(data.experiment_id)
            existing.results_criteria = json.dumps(data.results_criteria)
        self._get_session().commit()

    @override
    def delete_data(self, query: PowerQuery) -> None:
        params_json = json.dumps(query.criterion_parameters)
        alt_params_json = json.dumps(query.alternative_parameters)
        (
            self._get_session()
            .query(AlchemyPower)
            .filter(
                AlchemyPower.criterion_code == query.criterion_code,
                AlchemyPower.criterion_parameters == params_json,
                AlchemyPower.sample_size == int(query.sample_size),
                AlchemyPower.alternative_code == query.alternative_code,
                AlchemyPower.alternative_parameters == alt_params_json,
                AlchemyPower.monte_carlo_count == int(query.monte_carlo_count),
                AlchemyPower.significance_level == float(query.significance_level),
            )
            .delete()
        )
        self._get_session().commit()
