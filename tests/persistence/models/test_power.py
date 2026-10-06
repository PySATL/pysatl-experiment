"""Tests for the power storage models and interface."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.persistence.models.power import IPowerStorage, PowerModel, PowerQuery


def make_query(**overrides: Any) -> PowerQuery:
    """Build a power query with deterministic defaults."""
    values: dict[str, Any] = {
        "criterion_code": "KS",
        "criterion_parameters": {"mean": 0.0},
        "sample_size": 30,
        "alternative_code": "NORM",
        "alternative_parameters": [0.0, 1.0],
        "monte_carlo_count": 100,
        "significance_level": 0.05,
    }
    values.update(overrides)
    return PowerQuery(**values)


# Checks that the power model keeps every provided field.
def test_power_model_stores_all_fields() -> None:
    model = PowerModel(
        experiment_id=7,
        criterion_code="KS",
        criterion_parameters={"mean": 0.0},
        sample_size=30,
        alternative_code="NORM",
        alternative_parameters=[0.0, 1.0],
        monte_carlo_count=100,
        significance_level=0.05,
        results_criteria=[True, False, True],
    )

    assert model.experiment_id == 7
    assert model.criterion_code == "KS"
    assert model.criterion_parameters == {"mean": 0.0}
    assert model.sample_size == 30
    assert model.alternative_code == "NORM"
    assert model.alternative_parameters == [0.0, 1.0]
    assert model.monte_carlo_count == 100
    assert model.significance_level == 0.05
    assert model.results_criteria == [True, False, True]


# Checks that the power model rejects unknown constructor arguments.
def test_power_model_rejects_unknown_field() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        PowerModel(experiment_id=1, unknown_field="x")  # type: ignore[call-arg]


# Checks that the power query keeps every provided field.
def test_power_query_stores_all_fields() -> None:
    query = make_query()

    assert query.criterion_code == "KS"
    assert query.criterion_parameters == {"mean": 0.0}
    assert query.sample_size == 30
    assert query.alternative_code == "NORM"
    assert query.alternative_parameters == [0.0, 1.0]
    assert query.monte_carlo_count == 100
    assert query.significance_level == 0.05


# Checks that two queries with identical values compare equal.
def test_power_query_equality() -> None:
    assert make_query() == make_query()
    assert make_query() != make_query(sample_size=31)


# Checks that the power storage interface declares the bulk insert contract.
def test_power_storage_declares_bulk_insert_abstract() -> None:
    assert "bulk_insert_data" in IPowerStorage.__abstractmethods__


# Checks that the abstract bulk insert body is reachable through the base class.
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param([], id="empty-list"),
        pytest.param([MagicMock()], id="single-model"),
    ],
)
def test_power_storage_bulk_insert_body_returns_none(payload: Iterable[Any]) -> None:
    assert IPowerStorage.bulk_insert_data(MagicMock(), payload) is None
