"""Tests for the build-and-run CLI command and generation-only execution."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click import BadParameter
from click.testing import CliRunner

from pysatl_experiment.cli.commands.build_and_run import _build_experiment, _run_experiment_data, build_and_run
from pysatl_experiment.cli.validation.commands.build_and_run import validate_build_and_run
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.experiment_execution.experiment_factory.generation_only_factory import (
    GenerationOnlyExperimentFactory,
)
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage


COMMAND_PATH = "pysatl_experiment.cli.commands.build_and_run"


def test_run_experiment_data_executes_only_generation_step(tmp_path: Path) -> None:
    raw = {
        "name": "normal_training_samples",
        "config": {
            "experiment_type": "generation_only",
            "distribution": "normal",
            "sample_sizes": [10],
            "samples_count": 2,
            "parameters": {
                "mean": {"type": "random_uniform", "low": -5.0, "high": 5.0},
                "var": {"type": "fixed", "value": 1.0},
            },
            "seed": 42,
            "run_mode": "reuse",
            "storage_connection": f"sqlite:///{tmp_path / 'samples.sqlite'}",
        },
    }
    data = validate_build_and_run(raw)

    _run_experiment_data(data)

    steps = GenerationOnlyExperimentFactory(data).create_experiment_steps()
    assert steps.generation_step is None
    storage = GeneratedSamplesStorage(data.config.storage_connection)
    storage.init()
    assert storage.get_existing_sample_numbers(
        steps.experiment_id,
        sample_size=10,
    ) == {1, 2}


# Checks that a missing experiment aborts the command before any other work happens.
@patch(f"{COMMAND_PATH}.read_experiment_data")
@patch(f"{COMMAND_PATH}.is_experiment_exists", return_value=False)
def test_build_and_run_fails_for_unknown_experiment(
    is_experiment_exists: MagicMock, read_experiment_data: MagicMock
) -> None:
    result = CliRunner().invoke(build_and_run, ["missing-exp"])

    assert result.exit_code == 2
    assert "Experiment with name missing-exp does not exist." in result.output
    is_experiment_exists.assert_called_once_with("missing-exp")
    read_experiment_data.assert_not_called()


# Checks that the command reads, validates and runs the stored experiment configuration.
@patch(f"{COMMAND_PATH}._run_experiment_data")
@patch(f"{COMMAND_PATH}.validate_build_and_run")
@patch(f"{COMMAND_PATH}.setup_logging")
@patch(f"{COMMAND_PATH}.read_experiment_data")
@patch(f"{COMMAND_PATH}.is_experiment_exists", return_value=True)
def test_build_and_run_executes_validated_experiment(
    is_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    setup_logging: MagicMock,
    validate: MagicMock,
    run_experiment_data: MagicMock,
) -> None:
    configuration = {"name": "my-exp", "config": {"experiment_type": "generation_only"}}
    read_experiment_data.return_value = configuration
    experiment_data = MagicMock()
    validate.return_value = experiment_data

    result = CliRunner().invoke(build_and_run, ["my-exp"])

    assert result.exit_code == 0
    assert result.exception is None
    is_experiment_exists.assert_called_once_with("my-exp")
    read_experiment_data.assert_called_once_with("my-exp")
    setup_logging.assert_called_once_with(configuration, logging.WARNING, None)
    validate.assert_called_once_with(configuration)
    run_experiment_data.assert_called_once_with(experiment_data)


# Checks that every supported experiment type is dispatched to its own factory.
@pytest.mark.parametrize(
    ("experiment_type", "factory_name"),
    [
        (ExperimentType.POWER, "PowerExperimentFactory"),
        (ExperimentType.CRITICAL_VALUE, "CriticalValueExperimentFactory"),
        (ExperimentType.TIME_COMPLEXITY, "TimeComplexityExperimentFactory"),
        (ExperimentType.GENERATION_ONLY, "GenerationOnlyExperimentFactory"),
    ],
)
def test_build_experiment_uses_type_specific_factory(experiment_type: ExperimentType, factory_name: str) -> None:
    experiment_data = MagicMock()
    experiment_data.config.experiment_type = experiment_type

    with patch(f"{COMMAND_PATH}.{factory_name}") as factory:
        factory.return_value.create_experiment_steps.return_value = "steps"

        assert _build_experiment(experiment_data) == "steps"

    factory.assert_called_once_with(experiment_data)
    factory.return_value.create_experiment_steps.assert_called_once_with()


# Checks that an unregistered experiment type is reported as a bad parameter.
def test_build_experiment_rejects_unknown_experiment_type() -> None:
    experiment_data = MagicMock()
    experiment_data.config.experiment_type = "unsupported"

    with pytest.raises(BadParameter, match="Unsupported experiment type: unsupported."):
        _build_experiment(experiment_data)
