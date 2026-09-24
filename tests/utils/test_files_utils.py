"""Tests for filesystem path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

import pysatl_experiment.utils.files_utils as files_utils


DIR_HELPERS = [
    pytest.param("ensure_experiment_dir", "EXPERIMENTS_DIR", id="experiments"),
    pytest.param("ensure_result_dir", "RESULTS_DIR", id="results"),
]

EXPERIMENT_CONF_CASES = [
    pytest.param("simple", "simple.json", id="plain-name"),
    pytest.param("My Experiment", "my_experiment.json", id="spaces-to-underscores"),
    pytest.param("My-Experiment", "my_experiment.json", id="dashes-to-underscores"),
    pytest.param("  Report 2024  ", "report_2024.json", id="stripped-and-lowercased"),
    pytest.param("ALREADY_LOWER", "already_lower.json", id="already-normalized"),
]


@pytest.fixture()
def user_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point the configured user data directory at a temporary location."""
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(tmp_path / "user_data"))
    return tmp_path / "user_data"


# Checks that ensure_user_data_dir resolves the configured directory to an absolute path.
def test_ensure_user_data_dir_returns_resolved_path(user_data_dir: Path) -> None:
    assert files_utils.ensure_user_data_dir() == user_data_dir.resolve()


# Checks that a relative user data directory is resolved against the current working directory.
def test_ensure_user_data_dir_resolves_relative_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", "user_data")
    monkeypatch.chdir(tmp_path)

    assert files_utils.ensure_user_data_dir() == (tmp_path / "user_data").resolve()


# Checks that the user data directory constant is used verbatim when already absolute.
@pytest.mark.parametrize("sub_dir", ["nested/user_data", "user_data"])
def test_ensure_user_data_dir_uses_absolute_constant(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sub_dir: str
) -> None:
    expected = tmp_path / sub_dir
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(expected))

    assert files_utils.ensure_user_data_dir() == expected.resolve()


# Checks that both directory helpers create their directory and return its path.
@pytest.mark.parametrize(("helper_name", "const_name"), DIR_HELPERS)
def test_dir_helper_creates_and_returns_directory(
    user_data_dir: Path, helper_name: str, const_name: str
) -> None:
    target = getattr(files_utils, helper_name)()

    assert target == user_data_dir / getattr(files_utils, const_name)
    assert target.is_dir()


# Checks that repeated calls to a directory helper are idempotent.
@pytest.mark.parametrize(("helper_name", "const_name"), DIR_HELPERS)
def test_dir_helper_is_idempotent(user_data_dir: Path, helper_name: str, const_name: str) -> None:
    helper = getattr(files_utils, helper_name)

    first = helper()
    second = helper()

    assert first == second
    assert second.is_dir()


# Checks that directory helpers create missing parent directories.
@pytest.mark.parametrize(("helper_name", "const_name"), DIR_HELPERS)
def test_dir_helper_creates_missing_parents(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, helper_name: str, const_name: str
) -> None:
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(tmp_path / "deep" / "nested" / "data"))

    target = getattr(files_utils, helper_name)()

    assert target.is_dir()
    assert target == tmp_path / "deep" / "nested" / "data" / getattr(files_utils, const_name)


# Checks that the nested constants are honoured when building helper paths.
@pytest.mark.parametrize(("helper_name", "const_name"), DIR_HELPERS)
def test_dir_helper_honours_constant_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, helper_name: str, const_name: str
) -> None:
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(files_utils, const_name, "custom_dir")

    target = getattr(files_utils, helper_name)()

    assert target == tmp_path / "custom_dir"
    assert target.is_dir()


# Checks that experiment config paths are normalized and point into the experiments directory.
@pytest.mark.parametrize(("experiment_name", "expected_file_name"), EXPERIMENT_CONF_CASES)
def test_ensure_experiment_conf_builds_normalized_json_path(
    user_data_dir: Path, experiment_name: str, expected_file_name: str
) -> None:
    path = files_utils.ensure_experiment_conf(experiment_name)

    assert path == user_data_dir / files_utils.EXPERIMENTS_DIR / expected_file_name
    assert path.suffix == ".json"
    assert path.parent.is_dir()


# Checks that building a config path does not create the JSON file itself.
def test_ensure_experiment_conf_does_not_create_file(user_data_dir: Path) -> None:
    path = files_utils.ensure_experiment_conf("placeholder")

    assert not path.exists()
    assert list(path.parent.glob("*.json")) == []
