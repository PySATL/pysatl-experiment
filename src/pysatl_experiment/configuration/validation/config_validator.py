"""Validate raw documents and build prepared experiment configurations."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError
from pysatl_criterion.utils.generator import get_available_generator
from pysatl_criterion.utils.statistic import get_available_criteria

from pysatl_experiment.configuration import (
    CriterionConfig,
    CriticalValueExperimentConfig,
    DistributionConfig,
    ExecutionConfig,
    ExperimentConfig,
    GenerationConfig,
    PowerExecutionConfig,
    PowerExperimentConfig,
    RawExperimentConfig,
    ReportConfig,
    SampleGenerationConfig,
    TimeComplexityExperimentConfig,
)

from .config_errors import ConfigIssue, ConfigValidationError
from .config_schemas import CriticalValueSchema, PowerSchema, TimeComplexitySchema


def _build_steps(schema: Any) -> dict[str, Any]:
    generation = schema.generate.model_dump()
    generation["distributions"] = [
        DistributionConfig(
            distribution_type=item.distribution_type.value,
            distribution_params=item.distribution_params,
        )
        for item in schema.generate.distributions
    ]
    execution = schema.execute.model_dump()
    execution["hypothesis"] = schema.execute.hypothesis.value
    execution["criteria"] = [CriterionConfig(**item.model_dump()) for item in schema.execute.criteria]
    return {
        "experiment_name": schema.experiment_name,
        "storage_connection": schema.storage_connection,
        "run_mode": schema.run_mode,
        "generate": generation,
        "execute": execution,
        "report": ReportConfig(**schema.report.model_dump()),
    }


def build_critical_value_config(schema: CriticalValueSchema) -> CriticalValueExperimentConfig:
    """Build the critical value dataclass from validated fields."""
    fields = _build_steps(schema)
    fields["generate"] = SampleGenerationConfig(**fields["generate"])
    fields["execute"] = ExecutionConfig(**fields["execute"])
    return CriticalValueExperimentConfig(**fields)


def build_power_config(schema: PowerSchema) -> PowerExperimentConfig:
    """Build the power dataclass from validated fields."""
    fields = _build_steps(schema)
    fields["generate"] = GenerationConfig(**fields["generate"])
    fields["execute"] = PowerExecutionConfig(**fields["execute"])
    return PowerExperimentConfig(**fields)


def build_time_complexity_config(schema: TimeComplexitySchema) -> TimeComplexityExperimentConfig:
    """Build the time complexity dataclass from validated fields."""
    fields = _build_steps(schema)
    fields["generate"] = SampleGenerationConfig(**fields["generate"])
    fields["execute"] = ExecutionConfig(**fields["execute"])
    return TimeComplexityExperimentConfig(**fields)


def _domain_issues(schema: Any) -> list[ConfigIssue]:
    issues = []
    for index, distribution in enumerate(schema.generate.distributions):
        parameters = {
            name: (sum(value) / 2 if isinstance(value, list) else value)
            for name, value in distribution.distribution_params.items()
        }
        try:
            get_available_generator(distribution.distribution_type, parameters)
        except (ValueError, TypeError, StopIteration) as error:
            issues.append(ConfigIssue(("generate", "distributions", index), "distribution", str(error)))

    criteria_types = {
        cls.short_code(): cls
        for cls in get_available_criteria(schema.execute.hypothesis)
        if not getattr(cls, "__abstractmethods__", None)
    }
    for index, criterion in enumerate(schema.execute.criteria):
        criterion_type = criteria_types.get(criterion.criterion_code)
        if criterion_type is None:
            issues.append(
                ConfigIssue(
                    ("execute", "criteria", index, "criterion_code"),
                    "criterion_incompatible",
                    f"Criterion is incompatible with {schema.execute.hypothesis.value}; "
                    f"allowed: {sorted(criteria_types)}",
                )
            )
            continue
        try:
            criterion_type(**(schema.execute.hypothesis_params | criterion.parameters))
        except (ValueError, TypeError) as error:
            issues.append(ConfigIssue(("execute", "criteria", index, "parameters"), "criterion_parameters", str(error)))

    if hasattr(schema.generate, "samples_count"):
        if schema.generate.samples_count < schema.execute.monte_carlo_count:
            issues.append(
                ConfigIssue(
                    ("generate", "samples_count"),
                    "insufficient_samples",
                    "Must be at least execute.monte_carlo_count",
                )
            )
    return issues


@dataclass(frozen=True)
class ExperimentValidationSpec:
    """Schema, domain checks and builder registered for one experiment kind."""

    schema: type[BaseModel]
    build: Callable[[Any], ExperimentConfig]
    domain_issues: Callable[[Any], list[ConfigIssue]] | None = _domain_issues


class ConfigValidationRegistry(Protocol):
    """Configuration-only view of a registry, independent of execution factories."""

    def validation_specs(self) -> Mapping[str, ExperimentValidationSpec]:
        """Return the registered schemas, domain checks and config builders."""
        ...


class ExperimentConfigValidator:
    """Extensible validation service with no CLI or database dependencies."""

    def __init__(self, specs: Mapping[str, ExperimentValidationSpec] | None = None) -> None:
        self._specs: dict[str, ExperimentValidationSpec] = dict(specs or {})

    def validation_specs(self) -> Mapping[str, ExperimentValidationSpec]:
        """Return a snapshot that can be shared with an execution registry."""
        return dict(self._specs)

    def register(self, experiment_type: str, spec: ExperimentValidationSpec) -> None:
        """Register a new experiment kind without changing raw configuration."""
        if experiment_type in self._specs:
            raise ValueError(f"Experiment type already registered: {experiment_type}")
        self._specs[experiment_type] = spec

    def validate(self, raw: RawExperimentConfig) -> ExperimentConfig:
        """Return a prepared config or all issues from the failing stage."""
        data = raw.to_data()
        if not isinstance(data, dict):
            raise ConfigValidationError([ConfigIssue((), "object_required", "Expected a JSON object")])
        kind = data.get("experiment_type")
        if not isinstance(kind, str) or kind not in self._specs:
            code = "missing" if "experiment_type" not in data else "experiment_type"
            raise ConfigValidationError(
                [
                    ConfigIssue(
                        ("experiment_type",),
                        code,
                        f"Expected one of: {', '.join(self._specs)}",
                    )
                ]
            )
        spec = self._specs[kind]
        try:
            schema = spec.schema.model_validate(data)
        except ValidationError as error:
            raise ConfigValidationError(
                [ConfigIssue(tuple(item["loc"]), item["type"], item["msg"]) for item in error.errors()]
            ) from error
        issues = spec.domain_issues(schema) if spec.domain_issues is not None else []
        if issues:
            raise ConfigValidationError(issues)
        config = spec.build(schema)
        if not isinstance(config, ExperimentConfig) or config.experiment_type != kind:
            raise ValueError(f"Config builder for '{kind}' must return an ExperimentConfig of the same experiment type")
        return config


def create_config_validator(registry: ConfigValidationRegistry | None = None) -> ExperimentConfigValidator:
    """Use the supplied registrations, or the built-in validation specs by default."""
    if registry is not None:
        return ExperimentConfigValidator(registry.validation_specs())
    validator = ExperimentConfigValidator()
    validator.register("critical_value", ExperimentValidationSpec(CriticalValueSchema, build_critical_value_config))
    validator.register("power", ExperimentValidationSpec(PowerSchema, build_power_config))
    validator.register("time_complexity", ExperimentValidationSpec(TimeComplexitySchema, build_time_complexity_config))
    return validator


def validate_experiment_config(
    raw: RawExperimentConfig, *, registry: ConfigValidationRegistry | None = None
) -> ExperimentConfig:
    """Validate a registered experiment without loading plugins or opening storage."""
    return create_config_validator(registry).validate(raw)
