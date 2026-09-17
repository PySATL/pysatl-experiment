"""Tests for alternative hypothesis validation."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from pysatl_criterion.generator.generators import CauchyRVSGenerator, NormalGenerator

from pysatl_experiment.cli.commands.configure import configure
from pysatl_experiment.configuration.models.experiment_type import ExperimentType


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists")
def test_alternatives_fails_if_experiment_type_not_set(
        read_experiment_config: MagicMock,
        runner: CliRunner
) -> None:
    experiment_name = "my-exp"
    read_experiment_config.return_value = {"some_key": "some_value"}

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-alt", "Normal 1 1",
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    read_experiment_config.assert_not_called()


@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_alternatives_fails_for_unsupported_experiment_type(
        is_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner
) -> None:
    """Tests that the command fails if alternatives are provided for a non-POWER experiment."""
    experiment_name = "my-exp"
    read_experiment_data.return_value = {
        "name": experiment_name,
        "config": {"experiment_type": ExperimentType.CRITICAL_VALUE.value},
    }

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-alt", "Normal 1 1",
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code != 0
    assert "alternative" in result.output.lower()
    # TODO: registry is empty in tests, so AlternativesConfig fails before checking non-POWER experiment_type —
    #  populate via conftest

    is_experiment_exists.assert_called_once()
    read_experiment_data.assert_called_once()
    save_experiment_config.assert_not_called()

    # TODO: long time of executing this test


@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_alternatives_fails_with_wrong_parameter_count(
        is_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner,
) -> None:
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}
    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-alt", "Normal 1.0",
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code != 0

    is_experiment_exists.assert_called_once()
    read_experiment_data.assert_called_once()
    save_experiment_config.assert_not_called()


@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_alternatives_fails_with_non_numeric_parameters(
        is_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner,
) -> None:
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}
    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-alt", "Normal 1.0 abc",
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code != 0

    is_experiment_exists.assert_called_once()
    read_experiment_data.assert_called_once()
    save_experiment_config.assert_not_called()


@patch(
    "pysatl_experiment.cli.validation.schemas.alternative._get_available_generator_classes",
    return_value=[NormalGenerator, CauchyRVSGenerator, NormalGenerator],
)
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_alternatives_fails_with_ambiguous_generator_name(
        is_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        fake_generator_subclasses: MagicMock,
        runner: CliRunner,
) -> None:
    """Tests failure when a generator prefix matches multiple available generators."""
    experiment_name = "my-exp"
    initial_config = {"experiment_type": "power"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}
    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-alt", "Normal 1 2",
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            "-expt", "power",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code != 0

    output = result.output

    assert "For alternative #1 ('Normal 1 2')" in output
    assert "Generator prefix 'Normal' is ambiguous" in output
    assert "NORMALGENERATOR" in output
    assert "Please be more specific" in output

    is_experiment_exists.assert_called_once()
    read_experiment_data.assert_called_once()
    save_experiment_config.assert_not_called()
    fake_generator_subclasses.assert_called()


@patch(
    "pysatl_experiment.cli.validation.schemas.alternative._get_available_generator_classes",
    return_value=[NormalGenerator, CauchyRVSGenerator],
)
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_alternatives_success_with_valid_inputs(
        is_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        fake_generator_subclasses: MagicMock,
        runner: CliRunner,
) -> None:
    experiment_name = "my-exp"
    initial_config: dict[str, Any] = {"experiment_type": "power"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}
    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-alt", "NormalG 1.0 0.5",
            "-alt", "cauchy 0 2",
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            "-expt", "power",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code == 0
    assert result.exception is None

    assert "alternatives" in initial_config
    assert len(initial_config["alternatives"]) == 2
    assert initial_config["alternatives"][0]["generator_name"] == "NORMALGENERATOR"
    assert initial_config["alternatives"][0]["parameters"] == [1.0, 0.5]
    assert initial_config["alternatives"][1]["generator_name"] == "CAUCHYRVSGENERATOR"
    assert initial_config["alternatives"][1]["parameters"] == [0.0, 2.0]

    is_experiment_exists.assert_called_once()
    read_experiment_data.assert_called_once()
    save_experiment_config.assert_called_once()
    fake_generator_subclasses.assert_called()
