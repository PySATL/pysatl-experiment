"""Read-only checks of external prerequisites for a prepared experiment."""

import json
from typing import Protocol

from pysatl_criterion import DistributionType
from pysatl_criterion.utils.statistic import get_available_criteria
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from pysatl_experiment.configuration import ExperimentConfig, PowerExperimentConfig


class ExperimentDependencyError(ValueError):
    """Report missing external data separately from malformed configuration."""


class CriticalValueChecker(Protocol):
    """Storage contract needed by the power dependency check."""

    def check_exists(self, code: str, parameters: dict[str, float], size: int) -> bool:
        """Return whether an empirical critical value distribution is present."""
        ...


def _check_power(config: PowerExperimentConfig, checker: CriticalValueChecker) -> None:
    classes = {
        cls.short_code(): cls
        for cls in get_available_criteria(DistributionType(config.execute.hypothesis))
        if not getattr(cls, "__abstractmethods__", None)
    }
    missing = []
    for criterion in config.execute.criteria:
        code = classes[criterion.criterion_code].code()
        for size in config.execute.sample_sizes:
            if not checker.check_exists(code, criterion.parameters, size):
                missing.append(f"{code}, sample_size={size}, parameters={criterion.parameters}")
    if missing:
        raise ExperimentDependencyError("Missing critical value distributions:\n" + "\n".join(missing))


def check_experiment_dependencies(config: ExperimentConfig, checker: CriticalValueChecker | None = None) -> None:
    """Check power prerequisites after validation; other kinds require no lookup."""
    if not isinstance(config, PowerExperimentConfig):
        return
    if checker is not None:
        _check_power(config, checker)
        return

    engine = None
    try:
        engine = create_engine(config.storage_connection)
        with engine.connect() as connection:
            has_table = inspect(connection).has_table("limit_distributions")

            class DatabaseChecker:
                def check_exists(self, code: str, parameters: dict[str, float], size: int) -> bool:
                    if not has_table:
                        return False
                    rows = connection.execute(
                        text(
                            "SELECT criterion_parameters FROM limit_distributions "
                            "WHERE criterion_code = :code AND sample_size = :size"
                        ),
                        {"code": code, "size": size},
                    )
                    return any(json.loads(row[0]) == parameters for row in rows)

            _check_power(config, DatabaseChecker())
    except SQLAlchemyError as error:
        raise ExperimentDependencyError(f"Cannot check critical value dependencies: {error}") from error
    finally:
        if engine is not None:
            engine.dispose()
