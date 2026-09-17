"""Raw configuration models for experiments."""

from typing import Any


class GenerationRawConfig:
    """Raw configuration for sample generation.

    Parameters
    ----------
    samples_count : int
        Number of samples to generate.
    generator_type : str or None
        Type of random variable generator.
    distribution_type : str or None
        Type of probability distribution.
    distribution_params : dict[str, float] or None
        Parameters of the probability distribution.
    sample_sizes : list[int] or None
        Sample sizes used in the experiment.
    parallel_workers : int or None
        Number of workers available for parallel generation.
    """

    samples_count: int
    generator_type: str
    generator_type: str | None
    distribution_type: str | None
    distribution_params: dict[str, float] | None
    sample_sizes: list[int] | None
    parallel_workers: int | None


class ReportRawConfig:
    """Raw configuration for experiment reports."""

    pass


class CriteriaRawConfig:
    """Raw configuration for a statistical criterion.

    Parameters
    ----------
    criterion_code : str or None
        Code identifying the statistical criterion.
    parameters : dict[str, Any] or None
        Parameters passed to the statistical criterion.
    """

    criterion_code: str | None
    parameters: dict[str, Any] | None


class ExecutionRawConfig:
    """Raw configuration for experiment execution.

    Parameters
    ----------
    executor_type : str or None
        Type of executor used to run experiment steps.
    parallel_workers : int or None
        Number of workers available for parallel execution.
    criteria : list[CriteriaRawConfig] or None
        Statistical criteria used during experiment execution.
    """

    executor_type: str | None
    parallel_workers: int | None

    criteria: list[CriteriaRawConfig] | None


class PowerRawConfig:
    """Raw configuration for a statistical power experiment."""

    pass


class CriticalValuesRawConfig:
    """Raw configuration for a critical values experiment."""

    pass


class TimeComplexityRawConfig:
    """Raw configuration for a time complexity experiment."""

    pass


class RawConfig:
    """Raw configuration for an experiment.

    Parameters
    ----------
    experiment_name : str or None
        Name of the experiment.
    storage_connection : str or None
        Connection string for experiment data storage.
    experiment_type : str or None
        Type of experiment to execute.
    run_mode : str or None
        Mode in which the experiment is executed.
    generation : GenerationRawConfig or None
        Configuration for sample generation.
    execution : ExecutionRawConfig or None
        Configuration for experiment execution.
    report : ReportRawConfig or None
        Configuration for report generation.
    """

    experiment_name: str | None
    storage_connection: str | None
    experiment_type: str | None
    run_mode: str | None
    generation: GenerationRawConfig | None
    execution: ExecutionRawConfig | None
    report: ReportRawConfig | None
