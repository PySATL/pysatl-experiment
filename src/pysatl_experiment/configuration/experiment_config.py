"""Complete experiment configurations with independently typed steps."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pysatl_experiment.types import RunMode

from .experiment_config_interfaces import CriticalValueConfig, PowerConfig, TimeComplexityConfig
from .steps_config import (
    ExecutionConfig,
    GenerationConfig,
    PowerExecutionConfig,
    ReportConfig,
    RequiredConfig,
    SampleGenerationConfig,
)


G = TypeVar("G", bound=GenerationConfig)
R = TypeVar("R", bound=ReportConfig)
E = TypeVar("E", bound=ExecutionConfig)


@dataclass(frozen=True, kw_only=True)
class ExperimentConfig(RequiredConfig, Generic[G, R, E]):
    """Complete configuration; new experiment kinds can supply their own steps."""

    experiment_name: str
    storage_connection: str
    experiment_type: str
    run_mode: RunMode
    generate: G
    report: R
    execute: E

    def __post_init__(self) -> None:
        """Require prepared objects for all three steps."""
        super().__post_init__()
        for name, config_type in (
            ("generate", GenerationConfig),
            ("report", ReportConfig),
            ("execute", ExecutionConfig),
        ):
            if not isinstance(getattr(self, name), config_type):
                raise TypeError(f"{name} must be an instance of {config_type.__name__}")


@dataclass(frozen=True, kw_only=True)
class CriticalValueExperimentConfig(
    ExperimentConfig[SampleGenerationConfig, ReportConfig, ExecutionConfig], CriticalValueConfig
):
    """Complete critical value experiment configuration."""

    experiment_type: str = field(default="critical_value", init=False)


@dataclass(frozen=True, kw_only=True)
class PowerExperimentConfig(ExperimentConfig[GenerationConfig, ReportConfig, PowerExecutionConfig], PowerConfig):
    """Complete power experiment configuration."""

    experiment_type: str = field(default="power", init=False)


@dataclass(frozen=True, kw_only=True)
class TimeComplexityExperimentConfig(
    ExperimentConfig[SampleGenerationConfig, ReportConfig, ExecutionConfig], TimeComplexityConfig
):
    """Complete time complexity experiment configuration."""

    experiment_type: str = field(default="time_complexity", init=False)
