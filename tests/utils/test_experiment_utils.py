"""Tests for experiment configuration file utilities."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import pysatl_experiment.utils.files_utils as files_utils
from pysatl_experiment.persistence.models.random_values import (
    IRandomValuesStorage,
    RandomValuesCountQuery,
    RandomValuesModel,
)
from pysatl_experiment.utils.experiment_utils import (
    get_sample_data_from_storage,
    is_experiment_exists,
    parameters_to_list,
    read_experiment_data,
    save_experiment_config,
    save_experiment_data,
)


PARAMETERS_CASES = [
    pytest.param({"mean": 0.0, "std": 1.0}, [0.0, 1.0], id="dict-keyword-style"),
    pytest.param([2.5, 3.5], [2.5, 3.5], id="list-positional-style"),
    pytest.param({}, [], id="empty-dict"),
    pytest.param([], [], id="empty-list"),
    pytest.param({"a": 1, "b": 2, "c": 3}, [1, 2, 3], id="dict-insertion-order"),
]

EXPERIMENT_PAYLOADS = [
    pytest.param({"name": "exp", "config": {"alphas": [0.05]}}, id="nested-dict"),
    pytest.param({"experiment": {"steps": ["generation"]}}, id="deeply-nested"),
    pytest.param({"empty": {}, "list": []}, id="empty-containers"),
]


@pytest.fixture()
def user_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolate experiment files inside a temporary user data directory."""
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(tmp_path / "user_data"))
    return tmp_path / "user_data"


@pytest.fixture()
def storage() -> MagicMock:
    """Build a random values storage double."""
    return MagicMock(spec=IRandomValuesStorage)


def make_sample(experiment_name: str, data: list[float]) -> RandomValuesModel:
    """Build a stored random values sample."""
    return RandomValuesModel(
        generator_code="gen",
        generator_parameters=[],
        sample_size=len(data),
        experiment_name=experiment_name,
        data=data,
    )


# Checks that both parameter representations are normalized to a positional list.
@pytest.mark.parametrize(("parameters", "expected"), PARAMETERS_CASES)
def test_parameters_to_list_normalizes_representations(parameters, expected) -> None:
    assert parameters_to_list(parameters) == expected


# Checks that list-style parameters are copied instead of returned as-is.
def test_parameters_to_list_copies_list_input() -> None:
    source = [1.0, 2.0]

    result = parameters_to_list(source)

    assert result == source
    assert result is not source


# Checks that unknown experiments are reported as missing.
def test_is_experiment_exists_false_before_creation(user_data_dir: Path) -> None:
    assert is_experiment_exists("some experiment") is False


# Checks that a normalized experiment name is found after the data was written.
@pytest.mark.parametrize("experiment_name", ["My Experiment", "my-experiment", "  MY EXPERIMENT  "])
def test_is_experiment_exists_true_after_save(user_data_dir: Path, experiment_name: str) -> None:
    save_experiment_data("My Experiment", {"name": "exp"})

    assert is_experiment_exists(experiment_name) is True


# Checks that saving an experiment creates the experiments directory and JSON file.
def test_save_experiment_data_creates_directory_and_file(user_data_dir: Path) -> None:
    save_experiment_data("New Experiment", {"name": "exp"})

    expected_path = user_data_dir / files_utils.EXPERIMENTS_DIR / "new_experiment.json"
    assert expected_path.is_file()
    assert json.loads(expected_path.read_text()) == {"name": "exp"}


# Checks that experiment data is serialized with an indentation of four spaces.
def test_save_experiment_data_uses_indented_json(user_data_dir: Path) -> None:
    save_experiment_data("indented", {"name": "exp"})

    text = (user_data_dir / files_utils.EXPERIMENTS_DIR / "indented.json").read_text()
    assert text == json.dumps({"name": "exp"}, indent=4)


# Checks that saved experiment data can be read back unchanged.
@pytest.mark.parametrize("payload", EXPERIMENT_PAYLOADS)
def test_read_experiment_data_roundtrip(user_data_dir: Path, payload: dict) -> None:
    save_experiment_data("roundtrip", payload)

    assert read_experiment_data("roundtrip") == payload


# Checks that the read result is a plain dict copy of the deserialized payload.
def test_read_experiment_data_returns_dict(user_data_dir: Path) -> None:
    save_experiment_data("typed", {"items": [1, 2, 3]})

    result = read_experiment_data("typed")

    assert isinstance(result, dict)
    assert result == {"items": [1, 2, 3]}


# Checks that reading a missing experiment raises a file error.
def test_read_experiment_data_missing_file_raises(user_data_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_experiment_data("missing")


# Checks that saving a config replaces the config section and keeps other keys.
def test_save_experiment_config_replaces_config_only(user_data_dir: Path) -> None:
    save_experiment_data("config exp", {"config": {"old": True}, "name": "exp", "id": 7})

    save_experiment_config("config exp", {"alphas": [0.05, 0.01]})

    assert read_experiment_data("config exp") == {
        "config": {"alphas": [0.05, 0.01]},
        "name": "exp",
        "id": 7,
    }


# Checks that saving a config adds the section when it was absent.
def test_save_experiment_config_adds_missing_section(user_data_dir: Path) -> None:
    save_experiment_data("no config", {"name": "exp"})

    save_experiment_config("no config", {"mode": "fast"})

    assert read_experiment_data("no config") == {"name": "exp", "config": {"mode": "fast"}}


# Checks that stored samples are returned in storage order.
def test_get_sample_data_from_storage_returns_samples(storage: MagicMock) -> None:
    storage.get_count_data.return_value = [
        make_sample("1", [0.1, 0.2]),
        make_sample("2", [0.3, 0.4]),
    ]

    result = get_sample_data_from_storage("gen", 2, 2, storage, "exp")

    assert result == [[0.1, 0.2], [0.3, 0.4]]


# Checks that the storage is queried with the requested scope and parameters.
@pytest.mark.parametrize("generator_parameters", [None, {"mean": 0.0}, [0.0, 1.0]])
def test_get_sample_data_from_storage_builds_query(storage: MagicMock, generator_parameters) -> None:
    storage.get_count_data.return_value = [make_sample(str(index), [0.5]) for index in range(3)]

    get_sample_data_from_storage("gen", 5, 3, storage, "exp", generator_parameters)

    storage.get_count_data.assert_called_once_with(
        RandomValuesCountQuery(
            experiment_name="exp",
            generator_code="gen",
            sample_size=5,
            count=3,
            generator_parameters=generator_parameters,
        )
    )


# Checks that a missing or insufficient storage result raises a ValueError.
@pytest.mark.parametrize(
    "available",
    [
        pytest.param(None, id="none"),
        pytest.param([], id="empty"),
        pytest.param([make_sample("1", [1.0])], id="fewer-than-requested"),
    ],
)
def test_get_sample_data_from_storage_raises_on_insufficient_data(storage: MagicMock, available) -> None:
    storage.get_count_data.return_value = available

    with pytest.raises(ValueError, match="Not enough data in storage."):
        get_sample_data_from_storage("gen", 1, 3, storage, "exp")


# Checks that exactly the requested count is accepted without error.
def test_get_sample_data_from_storage_accepts_exact_count(storage: MagicMock) -> None:
    storage.get_count_data.return_value = [
        make_sample("1", [1.0]),
        make_sample("2", [2.0]),
        make_sample("3", [3.0]),
    ]

    result = get_sample_data_from_storage("gen", 1, 3, storage, "exp")

    assert result == [[1.0], [2.0], [3.0]]
