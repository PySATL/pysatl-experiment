"""Data containers for random sample generation steps."""

from dataclasses import dataclass

from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import GenerationData


@dataclass
class TimeComplexityExecutionStepContext:
    """
    Configuration for random sample generation.

    Attributes
    ----------
    data_list : list[GenerationData]
    experiment_name : str
    """

    data_list: list[GenerationData]
    experiment_name: str
    # parallel_workers: int TODO
