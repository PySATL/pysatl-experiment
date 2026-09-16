"""Experiment execution configuration models."""

from dataclasses import dataclass

from pysatl_experiment.configuration.models.step_type import StepType


@dataclass
class ExecutionConfig:
    """Configuration for experiment execution.

    Parameters
    ----------
    executor_type : StepType
        Type of executor used to run experiment steps.
    parallel_workers : int
        Number of workers available for parallel execution.
    """

    executor_type: StepType
    parallel_workers: int
