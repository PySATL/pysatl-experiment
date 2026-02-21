from dataclasses import dataclass

from pysatl_experiment.configuration.model.criterion.criterion import Criterion
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType


@dataclass
class ExperimentConfig:
    """
    Experiment configuration.
    """

    experiment_type: ExperimentType
    storage_connection: str
    run_mode: RunMode
    hypothesis: Hypothesis
    generator_type: StepType
    executor_type: StepType
    report_builder_type: StepType
    sample_sizes: list[int]
    monte_carlo_count: int
    criteria: list[Criterion]
    report_mode: ReportMode
    parallel_workers: int
