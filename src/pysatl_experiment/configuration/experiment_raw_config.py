from typing import Any


class GenerationRawConfig:
    samples_count: int
    generator_type: str
    generator_type: str | None
    distribution_type: str | None
    distribution_params: dict[str, float] | None
    sample_sizes: list[int] | None
    parallel_workers: int | None


class ReportRawConfig:
    pass


class CriteriaRawConfig:
    criterion_code: str | None
    parameters: dict[str, Any] | None


class ExecutionRawConfig:
    executor_type: str | None
    parallel_workers: int | None

    criteria: list[CriteriaRawConfig] | None


class PowerRawConfig:
    pass


class CriticalValuesRawConfig:
    pass


class TimeComplexityRawConfig:
    pass


class RawConfig:
    experiment_name: str | None
    storage_connection: str | None
    experiment_type: str | None
    run_mode: str | None
    generation: GenerationRawConfig | None
    execution: ExecutionRawConfig | None
    report: ReportRawConfig | None
