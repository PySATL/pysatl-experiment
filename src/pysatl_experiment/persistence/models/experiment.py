"""Data models and queries for experiment."""

from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery


@dataclass
class ExperimentModel(DataModel):
    """
    Experiment configuration and execution state.

    Parameters
    ----------
    experiment_type : str
        Type of experiment.
    storage_connection : str
        Storage backend connection string.
    run_mode : str
        Execution mode of experiment.
    report_mode : str
        Report generation mode.
    hypothesis : str
        Hypothesis identifier.
    generator_type : str
        Random generator type.
    executor_type : str
        Execution engine type.
    report_builder_type : str
        Report builder type.
    sample_sizes : list[int]
        List of sample sizes used in experiment.
    monte_carlo_count : int
        Number of Monte-Carlo simulations.
    criteria : dict[str, list[float]]
        Statistical criteria parameters.
    alternatives : dict[str, list[float]]
        Alternative hypothesis parameters.
    significance_levels : list[float]
        Significance levels (alpha values).
    parallel_workers : int
        Number of parallel workers.
    is_generation_done : bool
        Whether generation step is completed.
    is_execution_done : bool
        Whether execution step is completed.
    is_report_building_done : bool
        Whether report building step is completed.
    """

    experiment_name: str
    experiment_type: str
    storage_connection: str
    run_mode: str
    report_mode: str
    hypothesis: str
    generator_type: str
    executor_type: str
    report_builder_type: str
    sample_sizes: list[int]
    monte_carlo_count: int
    criteria: dict[str, list[float]]
    alternatives: dict[str, list[float]]
    significance_levels: list[float]
    parallel_workers: int
    is_generation_done: bool
    is_execution_done: bool
    is_report_building_done: bool


@dataclass
class ExperimentQuery(DataQuery):
    """Identify an experiment independently of its configuration."""

    experiment_name: str
