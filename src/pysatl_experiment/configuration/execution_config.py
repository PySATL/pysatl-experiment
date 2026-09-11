from dataclasses import dataclass

from pysatl_experiment.configuration.models.step_type import StepType


@dataclass
class ExecutionConfig:
    executor_type: StepType
    parallel_workers: int
