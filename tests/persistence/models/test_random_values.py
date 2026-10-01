"""Tests for the random values storage models and interface."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.persistence.models.random_values import (
    IRandomValuesStorage,
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)


# Checks that the random values model keeps every provided field.
def test_random_values_model_stores_all_fields() -> None:
    model = RandomValuesModel(
        generator_code="NORM",
        generator_parameters=[0.0, 1.0],
        sample_size=3,
        experiment_name="1",
        data=[0.1, 0.2, 0.3],
    )

    assert model.generator_code == "NORM"
    assert model.generator_parameters == [0.0, 1.0]
    assert model.sample_size == 3
    assert model.experiment_name == "1"
    assert model.data == [0.1, 0.2, 0.3]


# Checks that the random values model rejects unknown constructor arguments.
def test_random_values_model_rejects_unknown_field() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        RandomValuesModel(generator_code="NORM", unknown_field="x")  # type: ignore[call-arg]


# Checks that the single-sample query keeps every provided field.
def test_random_values_query_stores_all_fields() -> None:
    query = RandomValuesQuery(generator_code="NORM", sample_size=3, experiment_name="1")

    assert query.generator_code == "NORM"
    assert query.sample_size == 3
    assert query.experiment_name == "1"


# Checks that the single-sample query parameters default to None.
def test_random_values_query_generator_parameters_default_to_none() -> None:
    query = RandomValuesQuery(generator_code="NORM", sample_size=3, experiment_name="1")

    assert query.generator_parameters is None


# Checks that the single-sample query accepts explicit generator parameters.
@pytest.mark.parametrize(
    "generator_parameters",
    [
        pytest.param({"mean": 0.0}, id="mapping"),
        pytest.param([0.0, 1.0], id="list"),
    ],
)
def test_random_values_query_accepts_generator_parameters(generator_parameters: Any) -> None:
    query = RandomValuesQuery(
        generator_code="NORM",
        sample_size=3,
        experiment_name="1",
        generator_parameters=generator_parameters,
    )

    assert query.generator_parameters == generator_parameters


# Checks that the all-samples query defaults its optional fields.
def test_random_values_all_query_defaults_optional_fields() -> None:
    query = RandomValuesAllQuery(generator_code="NORM", sample_size=3)

    assert query.generator_code == "NORM"
    assert query.sample_size == 3
    assert query.experiment_name == ""
    assert query.generator_parameters is None


# Checks that the count query keeps every provided field.
def test_random_values_count_query_stores_all_fields() -> None:
    query = RandomValuesCountQuery(generator_code="NORM", sample_size=3, count=5)

    assert query.generator_code == "NORM"
    assert query.sample_size == 3
    assert query.count == 5
    assert query.experiment_name == ""
    assert query.generator_parameters is None


# Checks that the bulk container stores every provided field.
def test_random_values_all_model_stores_all_fields() -> None:
    model = RandomValuesAllModel(
        sample_size=3,
        generator_parameters={"mean": 0.0},
        data=[[1.0, 2.0, 3.0]],
        generator_code="NORM",
        experiment_name="exp",
    )

    assert model.generator_code == "NORM"
    assert model.experiment_name == "exp"
    assert model.sample_size == 3
    assert model.generator_parameters == {"mean": 0.0}
    assert model.data == [[1.0, 2.0, 3.0]]


# Checks that the generator name is used when no explicit code is given.
def test_random_values_all_model_falls_back_to_generator_name() -> None:
    model = RandomValuesAllModel(sample_size=3, generator_parameters=[0.0], data=[[]], generator_name="norm")

    assert model.generator_code == "norm"


# Checks that the explicit generator code wins over the generator name.
def test_random_values_all_model_prefers_generator_code() -> None:
    model = RandomValuesAllModel(
        sample_size=3,
        generator_parameters=[0.0],
        data=[[]],
        generator_code="CODE",
        generator_name="NAME",
    )

    assert model.generator_code == "CODE"


# Checks that the bulk container defaults its experiment name to an empty string.
def test_random_values_all_model_defaults_experiment_name() -> None:
    model = RandomValuesAllModel(sample_size=3, generator_parameters=[0.0], data=[[]], generator_code="NORM")

    assert model.experiment_name == ""


# Checks that the random values storage interface declares its five own abstract methods.
def test_random_values_storage_declares_expected_abstract_methods() -> None:
    assert {"get_rvs_count", "bulk_insert_data", "get_all_data", "delete_all_data", "get_count_data"} <= set(
        IRandomValuesStorage.__abstractmethods__
    )


# Checks that the abstract random values bodies are reachable through the base class.
@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        pytest.param(
            "get_rvs_count",
            (RandomValuesAllQuery(generator_code="NORM", sample_size=3),),
            id="get-rvs-count",
        ),
        pytest.param("bulk_insert_data", ([MagicMock()],), id="bulk-insert-data"),
        pytest.param(
            "get_all_data",
            (RandomValuesAllQuery(generator_code="NORM", sample_size=3),),
            id="get-all-data",
        ),
        pytest.param(
            "delete_all_data",
            (RandomValuesAllQuery(generator_code="NORM", sample_size=3),),
            id="delete-all-data",
        ),
        pytest.param(
            "get_count_data",
            (RandomValuesCountQuery(generator_code="NORM", sample_size=3, count=1),),
            id="get-count-data",
        ),
    ],
)
def test_abstract_random_values_bodies_return_none(method_name: str, args: tuple[Any, ...]) -> None:
    assert getattr(IRandomValuesStorage, method_name)(MagicMock(), *args) is None
