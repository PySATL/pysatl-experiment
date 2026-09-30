"""Domain models for generated training samples."""

from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationRunModel:
    """Configuration and state of one generation-only run."""

    name: str
    distribution: str
    sample_sizes: list[int]
    samples_count: int
    parameter_config: dict[str, dict[str, Any]]
    seed: int
    config_fingerprint: str
    is_complete: bool = False
    id: int | None = None


@dataclass
class GeneratedSampleModel:
    """One generated sample and the exact parameters used for it."""

    generation_run_id: int
    sample_size: int
    sample_num: int
    parameters: dict[str, float]
    sample_seed: int
    data: list[float]
    id: int | None = None
