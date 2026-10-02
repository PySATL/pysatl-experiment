"""Persist empirical limit distributions by experiment name."""

import json
from collections.abc import Iterable
from dataclasses import asdict

from sqlalchemy import Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from pysatl_experiment.persistence.contracts.limit_distribution import ILimitDistributionStorage
from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionModel, LimitDistributionQuery
from pysatl_experiment.persistence.sqlalchemy.base import AbstractDbStore, ModelBase


class AlchemyLimitDistribution(ModelBase):
    """One computed limit distribution belonging to an experiment."""

    __tablename__ = "experiment_limit_distributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_name: Mapped[str] = mapped_column(String, nullable=False)
    criterion_code: Mapped[str] = mapped_column(String, nullable=False)
    criterion_parameters: Mapped[str] = mapped_column(String, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    monte_carlo_count: Mapped[int] = mapped_column(Integer, nullable=False)
    results_statistics: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "experiment_name",
            "criterion_code",
            "criterion_parameters",
            "sample_size",
            "monte_carlo_count",
            name="uq_experiment_limit_distribution",
        ),
    )


class AlchemyLimitDistributionStorage(AbstractDbStore, ILimitDistributionStorage):
    """Keep lookup, replacement and deletion scoped to a named experiment."""

    @staticmethod
    def _statement(query: LimitDistributionQuery | LimitDistributionModel):
        return select(AlchemyLimitDistribution).where(
            AlchemyLimitDistribution.experiment_name == query.experiment_name,
            AlchemyLimitDistribution.criterion_code == query.criterion_code,
            AlchemyLimitDistribution.criterion_parameters == json.dumps(query.criterion_parameters, sort_keys=True),
            AlchemyLimitDistribution.sample_size == query.sample_size,
            AlchemyLimitDistribution.monte_carlo_count == query.monte_carlo_count,
        )

    def get_data(self, query: LimitDistributionQuery) -> LimitDistributionModel | None:
        """Read one result for the named experiment."""
        with self.session() as session:
            row = session.scalars(self._statement(query)).one_or_none()
            if row is None:
                return None
            return LimitDistributionModel(**asdict(query), results_statistics=json.loads(row.results_statistics))

    def insert_data(self, data: LimitDistributionModel) -> None:
        """Insert or replace one result."""
        self.bulk_insert_data([data])

    def bulk_insert_data(self, data_list: Iterable[LimitDistributionModel]) -> None:
        """Insert or replace results in one transaction."""
        with self.session() as session:
            for data in data_list:
                row = session.scalars(self._statement(data)).one_or_none()
                if row is None:
                    values = asdict(data)
                    values["criterion_parameters"] = json.dumps(data.criterion_parameters, sort_keys=True)
                    values["results_statistics"] = json.dumps(data.results_statistics)
                    session.add(AlchemyLimitDistribution(**values))
                else:
                    row.results_statistics = json.dumps(data.results_statistics)
                session.flush()
            session.commit()

    def delete_data(self, query: LimitDistributionQuery) -> None:
        """Delete only the result identified by the experiment-scoped query."""
        with self.session() as session:
            row = session.scalars(self._statement(query)).one_or_none()
            if row is not None:
                session.delete(row)
                session.commit()
