"""Tests for the build_and_run CLI command helpers."""

from pathlib import Path
from types import SimpleNamespace

from pysatl_experiment.cli.commands.build_and_run import _apply_failure_policy_overrides
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.models.steps_status import StepsStatus
from pysatl_experiment.configuration.models.task_failure_policy import TaskFailurePolicy


def make_data(**config_attrs: object) -> ExperimentData[SimpleNamespace]:
    """Build experiment data with a lightweight config double."""
    return ExperimentData(
        experiment_name="exp",
        config=SimpleNamespace(**config_attrs),
        steps_status=StepsStatus(),
        results_path=Path("results"),
    )


# Checks that CLI flags take precedence over the configured policy values.
def test_cli_flags_override_configured_policy() -> None:
    data = make_data(task_failure_policy=TaskFailurePolicy.FAIL_FAST, failure_threshold=0.01)

    _apply_failure_policy_overrides(data, "isolate", 0.5)

    assert data.config.task_failure_policy is TaskFailurePolicy.ISOLATE
    assert data.config.failure_threshold == 0.5


# Checks that absent CLI flags keep the configured policy values.
def test_absent_cli_flags_keep_configured_policy() -> None:
    data = make_data(task_failure_policy=TaskFailurePolicy.ISOLATE, failure_threshold=0.25)

    _apply_failure_policy_overrides(data, None, None)

    assert data.config.task_failure_policy is TaskFailurePolicy.ISOLATE
    assert data.config.failure_threshold == 0.25


# Checks that overrides are ignored for configurations without a failure policy.
def test_overrides_are_ignored_without_policy_support() -> None:
    data = make_data()

    _apply_failure_policy_overrides(data, "isolate", 0.5)

    assert not hasattr(data.config, "task_failure_policy")
    assert not hasattr(data.config, "failure_threshold")
