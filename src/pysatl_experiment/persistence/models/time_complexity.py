"""Data models and queries for time complexity."""

from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery

from pysatl_experiment.persistence.validation import require_nonempty_name, require_positive_integer


@dataclass
class TimeComplexityModel(DataModel):
    """
    Time complexity measurement model.

    Parameters
    ----------
    experiment_name : str
        Experiment name.
    criterion_code : str
        Criterion identifier.
    criterion_parameters : dict[str, float]
        Criterion parameters.
    sample_size : int
        Sample size.
    samples_count : int
        Number of simulations.
    results_times : list[float]
        Execution time measurements.
    generator_code : str
        Source sample-series identifier, including configured parameter ranges.
    """

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float]
    sample_size: int
    samples_count: int
    results_times: list[float]
    generator_code: str

    def __post_init__(self) -> None:
        """Require the source series to be part of every result's identity."""
        require_nonempty_name(self.generator_code, "generator_code")


@dataclass
class TimeComplexityQuery(DataQuery):
    """
    Query for time complexity data.

    Parameters
    ----------
    experiment_name : str
        Experiment name.
    criterion_code : str
    criterion_parameters : CriterionParameters
    sample_size : int
    samples_count : int
    generator_code : str
        Source sample-series identifier.
    """

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float]
    sample_size: int
    samples_count: int
    generator_code: str

    def __post_init__(self) -> None:
        """Require an exact source series when querying a result."""
        require_nonempty_name(self.generator_code, "generator_code")


@dataclass(frozen=True, kw_only=True)
class TimeComplexityFilter:
    """Select one experiment's results; None leaves optional fields unrestricted."""

    experiment_name: str
    criterion_code: str | None = None
    criterion_parameters: dict[str, float] | None = None
    sample_size: int | None = None
    samples_count: int | None = None
    generator_code: str | None = None

    def __post_init__(self) -> None:
        """Require an explicit experiment and valid optional dimensions."""
        require_nonempty_name(self.experiment_name, "experiment_name")
        if self.criterion_code is not None:
            require_nonempty_name(self.criterion_code, "criterion_code")
        if self.generator_code is not None:
            require_nonempty_name(self.generator_code, "generator_code")
        for field in ("sample_size", "samples_count"):
            value = getattr(self, field)
            if value is not None:
                require_positive_integer(value, field)
