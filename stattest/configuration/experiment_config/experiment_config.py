from dataclasses import dataclass

from stattest.configuration.model.criterion.criterion import Criterion
from stattest.configuration.model.experiment_type.experiment_type import ExperimentType
from stattest.configuration.model.hypothesis.hypothesis import Hypothesis
from stattest.configuration.model.run_mode.run_mode import RunMode
from stattest.configuration.model.step_type.step_type import StepType


@dataclass
class ExperimentConfig:
    """
    Experiment configuration.
    """

    experiment_type: ExperimentType
    storage_connection: str
    run_mode: RunMode
    hypothesis: Hypothesis
    data_generator_type: StepType
    executor_type: StepType
    report_builder_type: StepType
    sample_sizes: list[int]
    monte_carlo_count: int
    criteria: list[Criterion]
