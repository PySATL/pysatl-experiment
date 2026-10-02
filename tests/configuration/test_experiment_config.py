"""Contracts for raw JSON and prepared experiment configurations."""

import json
from pathlib import Path

import pytest

from pysatl_experiment.configuration import (
    CriterionConfig,
    CriticalValueConfig,
    CriticalValueExperimentConfig,
    DistributionConfig,
    ExecutionConfig,
    GenerationConfig,
    PowerConfig,
    PowerExecutionConfig,
    PowerExperimentConfig,
    RawExperimentConfig,
    ReportConfig,
    SampleGenerationConfig,
    TimeComplexityConfig,
    TimeComplexityExperimentConfig,
)
from pysatl_experiment.types import ReportMode, RunMode, StepType


EXAMPLES = Path(__file__).resolve().parents[2] / "experiment_example" / "configs"


@pytest.mark.parametrize(
    ("filename", "config_class", "marker", "generation_class", "execution_class"),
    [
        (
            "critical_values/normal_critical_values.json",
            CriticalValueExperimentConfig,
            CriticalValueConfig,
            SampleGenerationConfig,
            ExecutionConfig,
        ),
        ("power/normal_power.json", PowerExperimentConfig, PowerConfig, GenerationConfig, PowerExecutionConfig),
        (
            "time_complexity/laplace_time_complexity.json",
            TimeComplexityExperimentConfig,
            TimeComplexityConfig,
            SampleGenerationConfig,
            ExecutionConfig,
        ),
    ],
)
def test_example_can_be_represented(filename, config_class, marker, generation_class, execution_class):
    data = json.loads((EXAMPLES / filename).read_text())
    raw = RawExperimentConfig.from_dict(data)
    assert raw.to_dict() == data

    generation = dict(raw.generate)
    generation["generator_type"] = StepType(generation["generator_type"])
    generation["distributions"] = [DistributionConfig(**item) for item in generation["distributions"]]
    execution = dict(raw.execute)
    execution["executor_type"] = StepType(execution["executor_type"])
    execution["criteria"] = [CriterionConfig(**item) for item in execution["criteria"]]
    # The caller must explicitly resolve values missing from a raw document.
    execution.setdefault("parallel_workers", 1)
    config = config_class(
        experiment_name=raw.experiment_name,
        storage_connection=raw.storage_connection,
        run_mode=RunMode(raw.run_mode),
        generate=generation_class(**generation),
        execute=execution_class(**execution),
        report=ReportConfig(
            report_builder_type=StepType(raw.report["report_builder_type"]),
            report_mode=ReportMode(raw.report["report_mode"]),
            results_path=Path("user_data/.results"),
        ),
    )
    assert isinstance(config, marker)
    assert config.experiment_type == data["experiment_type"]
    assert config.execute.criteria[0].parameters == data["execute"]["criteria"][0]["parameters"]


def test_raw_preserves_absent_null_invalid_and_extension_values():
    assert RawExperimentConfig().generate is None
    assert RawExperimentConfig().to_dict() == {}
    data = {"generate": None, "execute": {"future_option": None}, "run_mode": 17, "plugin": {}}
    raw = RawExperimentConfig.from_dict(data)
    assert raw.to_dict() == data
    data["execute"]["future_option"] = "changed"
    assert raw.execute["future_option"] is None


@pytest.mark.parametrize("parameters", [None, {"scale": None}, [None]])
def test_prepared_parameters_reject_null(parameters):
    with pytest.raises(ValueError, match="must not be None"):
        CriterionConfig(criterion_code="KS", parameters=parameters)


def test_prepared_steps_are_required():
    with pytest.raises(TypeError):
        PowerExperimentConfig(experiment_name="power", storage_connection="sqlite://", run_mode=RunMode.REUSE)
    with pytest.raises(ValueError, match="generate must not be None"):
        PowerExperimentConfig(
            experiment_name="power",
            storage_connection="sqlite://",
            run_mode=RunMode.REUSE,
            generate=None,
            execute=None,
            report=None,
        )


@pytest.mark.parametrize(
    ("target", "source", "expected_type"),
    [
        ("generate", "report", "GenerationConfig"),
        ("report", "execute", "ReportConfig"),
        ("execute", "generate", "ExecutionConfig"),
    ],
)
def test_configuration_rejects_a_different_step_config(target, source, expected_type):
    steps = {
        "generate": GenerationConfig(generator_type=StepType.STANDARD, parallel_workers=1, distributions=[]),
        "report": ReportConfig(
            report_builder_type=StepType.STANDARD,
            report_mode=ReportMode.WITH_CHART,
            results_path=Path("user_data/.results"),
        ),
        "execute": PowerExecutionConfig(
            hypothesis="normal",
            hypothesis_params={},
            criteria=[],
            executor_type=StepType.STANDARD,
            monte_carlo_count=1000,
            parallel_workers=1,
            significance_levels=[0.05],
            sample_sizes=[200],
        ),
    }
    steps[target] = steps[source]
    with pytest.raises(TypeError, match=f"{target} must be an instance of {expected_type}"):
        PowerExperimentConfig(
            experiment_name="power",
            storage_connection="sqlite://",
            run_mode=RunMode.REUSE,
            **steps,
        )
