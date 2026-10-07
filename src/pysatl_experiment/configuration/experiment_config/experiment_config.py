"""Base experiment configuration model."""

from dataclasses import dataclass, field

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.criterion import Criterion
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.configuration.models.step_type import StepType


@dataclass
class ExperimentConfig:
    """
    Base experiment configuration.

    Attributes
    ----------
    experiment_type : ExperimentType
        Experiment execution mode.
    storage_connection : str
        Database or storage connection string.
    run_mode : RunMode
        Experiment execution behavior.
    hypothesis : DistributionType
        Tested statistical hypothesis.
    hypothesis_params : dict[str, float]
        Parameters of the hypothesized distribution. Defaults to an empty
        dict (distributions without required parameters, e.g. normal with
        defaults). Distributions with mandatory parameters still need
        explicit values — see the TODO in `_adapt_pydantic_to_dataclass`.
    generator_type : StepType
        Random sample generator implementation type.
    executor_type : StepType
        Experiment executor implementation type.
    report_builder_type : StepType
        Report builder implementation type.
    sample_sizes : list[int]
        Sample sizes used during experiments.
    monte_carlo_count : int
        Number of Monte Carlo iterations.
    criteria : list[Criterion]
        Configured goodness-of-fit criteria.
    report_mode : ReportMode
        Report generation mode.
    parallel_workers : int
        Number of parallel worker processes.
    """

    experiment_type: ExperimentType
    storage_connection: str
    run_mode: RunMode
    hypothesis: DistributionType
    generator_type: StepType
    executor_type: StepType
    report_builder_type: StepType
    sample_sizes: list[int]
    monte_carlo_count: int
    criteria: list[Criterion]
    report_mode: ReportMode
    parallel_workers: int
    # Default added so the CLI adapter (`_adapt_pydantic_to_dataclass`, which
    # dumps the Pydantic schema 1-to-1 via dacite) works for experiments
    # created through `create`/`configure`: the Pydantic layer has no
    # `hypothesis_params` field yet. `kw_only` keeps positional construction
    # order intact (all existing call sites use keywords).
    hypothesis_params: dict[str, float] = field(default_factory=dict, kw_only=True)
