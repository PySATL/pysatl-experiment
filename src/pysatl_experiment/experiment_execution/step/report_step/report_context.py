"""Output settings and prepared data shared by all experiment reports."""

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from pysatl_experiment.persistence.validation import require_nonempty_name
from pysatl_experiment.types import ReportMode


ResultT = TypeVar("ResultT")


@dataclass(frozen=True, slots=True)
class ReportStepContext:
    """Describe report output independently of its result source."""

    report_name: str
    report_mode: ReportMode
    results_path: Path
    template_path: Path

    def __post_init__(self) -> None:
        """Require a nonempty output name."""
        require_nonempty_name(self.report_name, "report_name")


@dataclass(frozen=True, slots=True)
class ReportBuilderContext(ReportStepContext, Generic[ResultT]):
    """Carry fully loaded results without retaining a storage connection."""

    data: tuple[ResultT, ...]

    def __post_init__(self) -> None:
        """Freeze the result collection without copying measurement arrays."""
        ReportStepContext.__post_init__(self)
        object.__setattr__(self, "data", tuple(self.data))
