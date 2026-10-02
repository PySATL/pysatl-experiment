"""Saved run progress, independent of preparation and persistence operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentRunState:
    """Execution state kept outside the immutable configuration."""

    experiment_name: str
    generation_done: bool
    execution_done: bool
