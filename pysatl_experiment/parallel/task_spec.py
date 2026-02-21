from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskSpec:
    """
    Universal, pickle-serializable task specification.
    Contains ONLY primitive types.
    """

    experiment_type: str
    statistic_class_name: str
    statistic_module: str
    sample_size: int
    monte_carlo_count: int
    db_path: str

    # For Critical Value & Time Complexity
    hypothesis_generator: str = ""
    hypothesis_parameters: list[float] = field(default_factory=list)

    # For Power
    alternative_generator: str = ""
    alternative_parameters: list[float] = field(default_factory=list)
    significance_level: Optional[float] = None
