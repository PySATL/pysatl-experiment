"""Tests for the time complexity storage models and interface."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.persistence.models.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


def make_query(**overrides: Any) -> TimeComplexityQuery:
    """Build a time complexity query with deterministic defaults."""
    values: dict[str, Any] = {
        "experiment_name": "exp",
        "criterion_code": "KS",
        "criterion_parameters": {"mean": 0.0},
        "sample_size": 30,
        "samples_count": 10,
    }
    values.update(overrides)
    return TimeComplexityQuery(**values)


# Checks that the time complexity model keeps every provided field.
def test_time_complexity_model_stores_all_fields() -> None:
    model = TimeComplexityModel(
        experiment_name="exp",
        criterion_code="KS",
        criterion_parameters={"mean": 0.0},
        sample_size=30,
        samples_count=10,
        results_times=[0.1, 0.2, 0.3],
    )

    assert model.experiment_name == "exp"
    assert model.criterion_code == "KS"
    assert model.criterion_parameters == {"mean": 0.0}
    assert model.sample_size == 30
    assert model.samples_count == 10
    assert model.results_times == [0.1, 0.2, 0.3]


# Checks that the time complexity model rejects unknown constructor arguments.
def test_time_complexity_model_rejects_unknown_field() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        TimeComplexityModel(experiment_name="exp", unknown_field="x")  # type: ignore[call-arg]


# Checks that the time complexity query keeps every provided field.
def test_time_complexity_query_stores_all_fields() -> None:
    query = make_query()

    assert query.experiment_name == "exp"
    assert query.criterion_code == "KS"
    assert query.criterion_parameters == {"mean": 0.0}
    assert query.sample_size == 30
    assert query.samples_count == 10


# Checks that two queries with identical values compare equal.
def test_time_complexity_query_equality() -> None:
    assert make_query() == make_query()
    assert make_query() != make_query(experiment_name="other")


# Checks that the time complexity storage interface declares the bulk insert contract.
def test_time_complexity_storage_declares_bulk_insert_abstract() -> None:
    assert "bulk_insert_data" in ITimeComplexityStorage.__abstractmethods__


# Checks that the abstract bulk insert body is reachable through the base class.
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param([], id="empty-list"),
        pytest.param([MagicMock()], id="single-model"),
    ],
)
def test_time_complexity_storage_bulk_insert_body_returns_none(payload: Iterable[Any]) -> None:
    assert ITimeComplexityStorage.bulk_insert_data(MagicMock(), payload) is None
