"""Tests for the SQLAlchemy experiment storage implementation."""

from __future__ import annotations

from typing import Any, cast

import pytest
from sqlalchemy import Table, UniqueConstraint

from pysatl_experiment.configuration.models.step_status import ExperimentStep, StepStatus
from pysatl_experiment.persistence.experiment_storage import AlchemyExperiment, AlchemyExperimentStorage
from pysatl_experiment.persistence.models.experiment import ExperimentModel, ExperimentQuery


SIGNATURE_FIELDS = (
    "experiment_type",
    "storage_connection",
    "run_mode",
    "report_mode",
    "hypothesis",
    "generator_type",
    "executor_type",
    "report_builder_type",
    "sample_sizes",
    "monte_carlo_count",
    "criteria",
    "alternatives",
    "significance_levels",
)

STATUS_FIELDS = ("generation_status", "execution_status", "report_building_status")

STEP_SETTERS = [
    pytest.param(ExperimentStep.GENERATION, "generation_status", id="generation"),
    pytest.param(ExperimentStep.EXECUTION, "execution_status", id="execution"),
    pytest.param(ExperimentStep.REPORT_BUILDING, "report_building_status", id="report-building"),
]

SIGNATURE_MISMATCHES = [
    pytest.param({"experiment_type": "CRITICAL_VALUE"}, id="experiment-type"),
    pytest.param({"storage_connection": "sqlite:///other.sqlite"}, id="storage-connection"),
    pytest.param({"run_mode": "APPEND"}, id="run-mode"),
    pytest.param({"report_mode": "WITHOUT_CHART"}, id="report-mode"),
    pytest.param({"hypothesis": "EXPONENT"}, id="hypothesis"),
    pytest.param({"generator_type": "NORMAL"}, id="generator-type"),
    pytest.param({"executor_type": "SEQUENTIAL"}, id="executor-type"),
    pytest.param({"report_builder_type": "CRITICAL_VALUE"}, id="report-builder-type"),
    pytest.param({"sample_sizes": [99]}, id="sample-sizes"),
    pytest.param({"monte_carlo_count": 999}, id="monte-carlo-count"),
    pytest.param({"criteria": {"AD": [1.0]}}, id="criteria"),
    pytest.param({"alternatives": {"NORM": [2.0]}}, id="alternatives"),
    pytest.param({"significance_levels": [0.5]}, id="significance-levels"),
]


@pytest.fixture()
def store() -> AlchemyExperimentStorage:
    """Create an initialized in-memory experiment storage."""
    storage = AlchemyExperimentStorage(db_url="sqlite://")
    storage.init()
    return storage


def make_model(**overrides: Any) -> ExperimentModel:
    """Build a fully defined experiment model, overriding selected fields."""
    values: dict[str, Any] = {
        "experiment_type": "POWER",
        "storage_connection": "sqlite:///data.sqlite",
        "run_mode": "OVERWRITE",
        "report_mode": "WITH_CHART",
        "hypothesis": "NORMAL",
        "generator_type": "UNIFORM",
        "executor_type": "MULTITHREADING",
        "report_builder_type": "POWER",
        "sample_sizes": [10, 20],
        "monte_carlo_count": 100,
        "criteria": {"KS": [0.1, 0.2]},
        "alternatives": {"EXP": [1.0]},
        "significance_levels": [0.05, 0.01],
        "parallel_workers": 2,
    }
    values.update(overrides)
    return ExperimentModel(**values)


def make_query(**overrides: Any) -> ExperimentQuery:
    """Build the lookup query matching :func:`make_model` by default."""
    values: dict[str, Any] = {
        "experiment_type": "POWER",
        "storage_connection": "sqlite:///data.sqlite",
        "run_mode": "OVERWRITE",
        "hypothesis": "NORMAL",
        "generator_type": "UNIFORM",
        "executor_type": "MULTITHREADING",
        "report_builder_type": "POWER",
        "sample_sizes": [10, 20],
        "monte_carlo_count": 100,
        "criteria": {"KS": [0.1, 0.2]},
        "alternatives": {"EXP": [1.0]},
        "significance_levels": [0.05, 0.01],
        "report_mode": "WITH_CHART",
        "parallel_workers": 2,
    }
    values.update(overrides)
    return ExperimentQuery(**values)


# Checks that the constructor stores the url and starts uninitialized.
def test_init_sets_url_and_uninitialized_flag() -> None:
    storage = AlchemyExperimentStorage(db_url="sqlite://")

    assert storage.db_url == "sqlite://"
    assert storage._initialized is False


# Checks that init marks the storage as initialized.
def test_init_marks_storage_as_initialized() -> None:
    storage = AlchemyExperimentStorage(db_url="sqlite://")

    storage.init()

    assert storage._initialized is True


# Checks that the ORM model name and composite unique key are as documented.
def test_orm_model_table_and_unique_constraint() -> None:
    table = cast(Table, AlchemyExperiment.__table__)
    unique_constraints = [constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)]

    assert AlchemyExperiment.__tablename__ == "experiments"
    assert len(unique_constraints) == 1
    assert unique_constraints[0].name == "uix_limit_distribution"
    assert {column.name for column in unique_constraints[0].columns} == set(SIGNATURE_FIELDS)


# Checks that the ORM entity exposes every mapped configuration column.
def test_to_orm_maps_every_column_from_the_model() -> None:
    model = make_model()

    orm = AlchemyExperimentStorage._to_orm(model)

    assert isinstance(orm, AlchemyExperiment)
    for field in (*SIGNATURE_FIELDS, "parallel_workers"):
        assert getattr(orm, field) == getattr(model, field)


# Checks that a model survives a conversion to ORM and back unchanged.
def test_to_orm_and_to_model_roundtrip() -> None:
    model = make_model(
        generation_status=StepStatus.DONE,
        execution_status=StepStatus.DONE,
        report_building_status=StepStatus.DONE,
    )

    orm = AlchemyExperimentStorage._to_orm(model)

    assert AlchemyExperimentStorage._to_model(orm) == model


# Checks that a step status is stored as its string value.
@pytest.mark.parametrize("field", ["generation_status", "execution_status", "report_building_status"])
def test_to_orm_converts_status_to_string(field: str) -> None:
    orm = AlchemyExperimentStorage._to_orm(make_model(**{field: StepStatus.RUNNING}))

    assert getattr(orm, field) == StepStatus.RUNNING.value


# Checks that an unset step status defaults to pending.
@pytest.mark.parametrize("field", ["generation_status", "execution_status", "report_building_status"])
def test_to_orm_defaults_status_to_pending(field: str) -> None:
    orm = AlchemyExperimentStorage._to_orm(make_model())

    assert getattr(orm, field) == StepStatus.PENDING.value


# Checks that a stored status string converts back to the enum member.
@pytest.mark.parametrize("field", ["generation_status", "execution_status", "report_building_status"])
def test_to_model_returns_status_enum(field: str) -> None:
    orm = AlchemyExperimentStorage._to_orm(make_model(**{field: StepStatus.FAILED}))

    assert getattr(AlchemyExperimentStorage._to_model(orm), field) is StepStatus.FAILED


# Checks that a stored experiment is read back with the same configuration.
def test_insert_data_stores_new_experiment(store: AlchemyExperimentStorage) -> None:
    model = make_model()

    store.insert_data(model)

    assert store.get_data(make_query()) == model


# Checks that reading an unknown experiment returns None.
def test_get_data_returns_none_for_unknown_experiment(store: AlchemyExperimentStorage) -> None:
    assert store.get_data(make_query()) is None


# Checks that the lookup requires every signature field to match exactly.
@pytest.mark.parametrize("overrides", SIGNATURE_MISMATCHES)
def test_get_data_requires_exact_signature_match(store: AlchemyExperimentStorage, overrides: dict[str, Any]) -> None:
    store.insert_data(make_model())

    assert store.get_data(make_query(**overrides)) is None
    assert store.get_data(make_query()) is not None


# Checks that re-inserting the same signature updates the state in place.
def test_insert_data_updates_existing_experiment_state(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())
    updated = make_model(
        generation_status=StepStatus.DONE,
        execution_status=StepStatus.DONE,
        report_building_status=StepStatus.DONE,
        parallel_workers=9,
    )

    store.insert_data(updated)

    assert store.session().query(AlchemyExperiment).count() == 1
    assert store.get_data(make_query()) == updated


# Checks that an update leaves the configuration columns untouched.
def test_insert_data_update_keeps_configuration_columns(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    store.insert_data(make_model(execution_status=StepStatus.DONE, parallel_workers=4))

    stored = store.get_data(make_query())
    assert stored is not None
    assert stored.parallel_workers == 4
    assert stored.sample_sizes == [10, 20]
    assert stored.criteria == {"KS": [0.1, 0.2]}
    assert stored.alternatives == {"EXP": [1.0]}
    assert stored.significance_levels == [0.05, 0.01]


# Checks that repeating an identical insert does not duplicate rows.
def test_insert_data_is_idempotent(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    store.insert_data(make_model())

    assert store.session().query(AlchemyExperiment).count() == 1


# Checks that a different signature produces a separate row.
def test_insert_data_creates_row_for_other_signature(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    store.insert_data(make_model(hypothesis="EXPONENT"))

    assert store.session().query(AlchemyExperiment).count() == 2
    assert store.get_data(make_query(hypothesis="EXPONENT")) is not None


# Checks that a stored experiment can be deleted by its signature.
def test_delete_data_removes_experiment(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    store.delete_data(make_query())

    assert store.get_data(make_query()) is None
    assert store.session().query(AlchemyExperiment).count() == 0


# Checks that deleting an unknown experiment is a no-op.
def test_delete_data_without_match_is_noop(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    store.delete_data(make_query(hypothesis="EXPONENT"))

    assert store.session().query(AlchemyExperiment).count() == 1


# Checks that only the experiment matching the signature is deleted.
def test_delete_data_keeps_other_experiments(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())
    store.insert_data(make_model(run_mode="APPEND"))

    store.delete_data(make_query())

    assert store.get_data(make_query()) is None
    assert store.get_data(make_query(run_mode="APPEND")) is not None


# Checks that the experiment identifier of a stored signature is returned.
def test_get_experiment_id_returns_row_identifier(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    experiment_id = store.get_experiment_id(make_query())

    assert isinstance(experiment_id, int)
    assert store.session().query(AlchemyExperiment).one().id == experiment_id


# Checks that an unknown signature raises a ValueError.
def test_get_experiment_id_raises_for_unknown_signature(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    with pytest.raises(ValueError, match="Experiment not found"):
        store.get_experiment_id(make_query(hypothesis="EXPONENT"))


# Checks that the worker count is not part of the signature lookup.
def test_get_experiment_id_ignores_parallel_workers(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model(parallel_workers=2))

    assert store.get_experiment_id(make_query(parallel_workers=7)) == store.get_experiment_id(make_query())


# Checks that a step status is set for the experiment and persisted.
@pytest.mark.parametrize(("step", "field"), STEP_SETTERS)
def test_set_step_status(store: AlchemyExperimentStorage, step: ExperimentStep, field: str) -> None:
    store.insert_data(make_model())
    experiment_id = store.get_experiment_id(make_query())

    store.set_step_status(experiment_id, step, StepStatus.DONE)

    stored = store.get_data(make_query())
    assert getattr(stored, field) is StepStatus.DONE
    other_fields = set(STATUS_FIELDS) - {field}
    assert all(getattr(stored, other) is StepStatus.PENDING for other in other_fields)


# Checks that every lifecycle status value round-trips through the storage.
@pytest.mark.parametrize("status", [StepStatus.RUNNING, StepStatus.DONE, StepStatus.FAILED])
def test_set_step_status_round_trips_all_statuses(store: AlchemyExperimentStorage, status: StepStatus) -> None:
    store.insert_data(make_model())
    experiment_id = store.get_experiment_id(make_query())

    store.set_step_status(experiment_id, ExperimentStep.EXECUTION, status)

    stored = store.get_data(make_query())
    assert stored is not None
    assert stored.execution_status is status


# Checks that setting a step status for an unknown identifier raises.
@pytest.mark.parametrize("step", [ExperimentStep.GENERATION, ExperimentStep.EXECUTION, ExperimentStep.REPORT_BUILDING])
def test_set_step_status_raises_for_unknown_experiment(store: AlchemyExperimentStorage, step: ExperimentStep) -> None:
    with pytest.raises(ValueError, match="Experiment not found"):
        store.set_step_status(404, step, StepStatus.DONE)


# Checks that step statuses of the same experiment are updated independently.
def test_set_step_statuses_are_updated_independently(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())
    experiment_id = store.get_experiment_id(make_query())

    store.set_step_status(experiment_id, ExperimentStep.GENERATION, StepStatus.DONE)
    store.set_step_status(experiment_id, ExperimentStep.REPORT_BUILDING, StepStatus.RUNNING)

    stored = store.get_data(make_query())
    assert stored is not None
    assert stored.generation_status is StepStatus.DONE
    assert stored.report_building_status is StepStatus.RUNNING
    assert stored.execution_status is StepStatus.PENDING


# Checks that task counters are persisted and read back.
def test_set_task_stats(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())
    experiment_id = store.get_experiment_id(make_query())

    store.set_task_stats(experiment_id, 2, 10)

    stored = store.get_data(make_query())
    assert stored is not None
    assert stored.tasks_failed == 2
    assert stored.tasks_total == 10


# Checks that task counters default to None for a freshly inserted experiment.
def test_task_stats_default_to_none(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    stored = store.get_data(make_query())
    assert stored is not None
    assert stored.tasks_failed is None
    assert stored.tasks_total is None


# Checks that setting task counters for an unknown identifier raises.
def test_set_task_stats_raises_for_unknown_experiment(store: AlchemyExperimentStorage) -> None:
    with pytest.raises(ValueError, match="Experiment not found"):
        store.set_task_stats(404, 1, 1)


# Checks that re-inserting a signature updates the stored task counters.
def test_insert_data_updates_task_counters(store: AlchemyExperimentStorage) -> None:
    store.insert_data(make_model())

    store.insert_data(make_model(tasks_failed=1, tasks_total=5))

    stored = store.get_data(make_query())
    assert stored is not None
    assert stored.tasks_failed == 1
    assert stored.tasks_total == 5
