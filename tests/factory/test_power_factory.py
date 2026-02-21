import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.experiment_config.power.power import PowerExperimentConfig
from pysatl_experiment.configuration.experiment_data.power.power import PowerExperimentData
from pysatl_experiment.configuration.model.alternative.alternative import Alternative
from pysatl_experiment.configuration.model.criterion.criterion import Criterion
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.experiment_new.step.execution.power.power import PowerExecutionStep
from pysatl_experiment.experiment_new.step.generation.generation import GenerationStep
from pysatl_experiment.experiment_new.step.report_building.power.power import PowerReportBuildingStep
from pysatl_experiment.factory.power.power import PowerExperimentFactory


# Provide a stub for line_profiler to avoid optional dependency during imports
_lp: Any = types.ModuleType("line_profiler")


def _profile(func):
    return func


_lp.profile = _profile
sys.modules.setdefault("line_profiler", _lp)


# ---------- Fakes ----------


class FakeGenerator:
    def __init__(self):
        self.called = []

    def generate(self, n):  # pragma: no cover - we don't run steps in these tests
        self.called.append(n)
        return [0.0 for _ in range(n)]


class FakeStatistics:
    @staticmethod
    def code() -> str:
        return "FAKE_CODE"


class FakeRandomValuesStorage:
    def __init__(self, counts_by_key: dict[tuple[str, tuple[float, ...], int], int]):
        # key: (generator_name, parameters_tuple, sample_size)
        self.counts_by_key = counts_by_key

    def init(self):  # pragma: no cover
        pass

    def get_data(self, query):  # pragma: no cover
        return None

    def get_rvs_count(self, query):
        key = (
            query.generator_name,
            tuple(query.generator_parameters),
            query.sample_size,
        )
        return self.counts_by_key.get(key, 0)

    def insert_data(self, model):  # pragma: no cover
        pass

    def delete_data(self, query):  # pragma: no cover
        pass

    def insert_all_data(self, query):  # pragma: no cover
        pass

    def get_all_data(self, query):  # pragma: no cover
        return None

    def delete_all_data(self, query):  # pragma: no cover
        pass

    def get_count_data(self, query):  # pragma: no cover
        return None


class FakePowerStorage:
    def __init__(self, has_result: set[tuple[str, int, int, str, tuple[float, ...], float]]):
        # key: (criterion_code, sample_size, monte_carlo_count, alternative_code, alternative_parameters,
        # significance_level)
        self.has_result = has_result

    def init(self):  # pragma: no cover
        pass

    def get_data(self, query):
        key = (
            query.criterion_code,
            query.sample_size,
            query.monte_carlo_count,
            query.alternative_code,
            tuple(query.alternative_parameters),
            query.significance_level,
        )
        return object() if key in self.has_result else None

    def insert_data(self, model):  # pragma: no cover
        pass

    def delete_data(self, query):  # pragma: no cover
        pass


class FakeExperimentStorage:
    def __init__(self, experiment_id: int):
        self._id = experiment_id

    def init(self):  # pragma: no cover
        pass

    def get_data(self, query):  # pragma: no cover
        return None

    def insert_data(self, data):  # pragma: no cover
        pass

    def delete_data(self, query):  # pragma: no cover
        pass

    def get_experiment_id(self, query):
        return self._id

    def set_generation_done(self, experiment_id: int):  # pragma: no cover
        pass

    def set_execution_done(self, experiment_id: int):  # pragma: no cover
        pass

    def set_report_building_done(self, experiment_id: int):  # pragma: no cover
        pass


class DeterministicPowerFactory(PowerExperimentFactory):
    """Factory overrides to keep behavior deterministic and fast for tests."""

    def __init__(self, experiment_data: PowerExperimentData, fake_generator: FakeGenerator):
        super().__init__(experiment_data)
        self._fake_generator = fake_generator

    def _get_criteria_config(self):  # type: ignore[override]
        crit = Criterion(criterion_code="FAKE", parameters=[0.0])
        return [
            CriterionConfig(
                criterion=crit, criterion_code=FakeStatistics.code(), statistics_class_object=FakeStatistics()
            )
        ]

    def _get_generator_class_object(self, generator_name: str, generator_parameters: list[float]):  # type: ignore[override]
        # Ignore input and return our fake generator
        return self._fake_generator


# ---------- Fixtures and builders ----------


@pytest.fixture()
def tmp_results_path(tmp_path: Path) -> Path:
    return tmp_path


def build_power_data(results_path: Path) -> PowerExperimentData:
    config = PowerExperimentConfig(
        experiment_type=ExperimentType.POWER,
        storage_connection=os.fspath(results_path / "test.sqlite"),
        run_mode=RunMode.REUSE,
        hypothesis=Hypothesis.EXPONENTIAL,
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[0.0])],
        report_mode=ReportMode.WITH_CHART,
        alternatives=[
            Alternative(generator_name="ALT_A", parameters=[0.1]),
            Alternative(generator_name="ALT_B", parameters=[0.2]),
        ],
        significance_levels=[0.05, 0.1],
        parallel_workers=1,
    )
    return PowerExperimentData(
        name="power_test",
        config=config,
        steps_done=type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})(),
        results_path=results_path,
    )


# ---------- Tests ----------


def test_generation_step_builds_needed_by_alternative(tmp_results_path: Path):
    data = build_power_data(tmp_results_path)
    fake_gen = FakeGenerator()
    factory = DeterministicPowerFactory(data, fake_gen)

    # Counts per (alt_name, params, size). For ALT_A we have 5 already, ALT_B only 2 → need 3
    counts: dict[tuple[str, tuple[float, ...], int], int] = {
        ("ALT_A", (0.1,), 10): 5,
        ("ALT_B", (0.2,), 10): 2,
    }
    rvs_storage = FakeRandomValuesStorage(counts_by_key=counts)

    gen_step = factory._create_generation_step(rvs_storage)
    assert isinstance(gen_step, GenerationStep)

    # Expect only one GenerationStepData for ALT_B
    assert len(gen_step.step_config) == 1
    step = gen_step.step_config[0]
    assert step.sample_size == 10
    assert step.count == 3
    assert step.generator_name == "ALT_B"
    assert step.generator_parameters == [0.2]


def test_execution_step_includes_missing_results_combinations(tmp_results_path: Path):
    data = build_power_data(tmp_results_path)
    fake_gen = FakeGenerator()
    factory = DeterministicPowerFactory(data, fake_gen)

    rvs_storage = FakeRandomValuesStorage(counts_by_key={})

    # build present results for one combination only: (FAKE_CODE, 10, 5, ALT_A, [0.1], 0.05)
    present: set[tuple[str, int, int, str, tuple[float, ...], float]] = {
        (FakeStatistics.code(), 10, 5, "ALT_A", (0.1,), 0.05)
    }
    power_storage = FakePowerStorage(has_result=present)
    exp_storage = FakeExperimentStorage(experiment_id=7)

    exec_step = factory._create_execution_step(rvs_storage, power_storage, exp_storage)
    assert isinstance(exec_step, PowerExecutionStep)
    assert exec_step.experiment_id == 7
    assert exec_step.monte_carlo_count == 5

    # We have 2 alternatives × 2 sig levels = 4 combinations for the single sample size
    # One is present, expect 3 remaining in step_config
    assert len(exec_step.step_config) == 3
    combo_set = {
        (sd.alternative.generator_name, tuple(sd.alternative.parameters), sd.significance_level)
        for sd in exec_step.step_config
    }
    assert ("ALT_A", (0.1,), 0.1) in combo_set
    assert ("ALT_B", (0.2,), 0.05) in combo_set
    assert ("ALT_B", (0.2,), 0.1) in combo_set


def test_report_building_step_sets_expected_fields(tmp_results_path: Path):
    data = build_power_data(tmp_results_path)
    fake_gen = FakeGenerator()
    factory = DeterministicPowerFactory(data, fake_gen)

    power_storage = FakePowerStorage(has_result=set())
    rb_step = factory._create_report_building_step(power_storage)
    assert isinstance(rb_step, PowerReportBuildingStep)

    assert [c.criterion_code for c in rb_step.criteria_config] == [FakeStatistics.code()]
    assert rb_step.significance_levels == data.config.significance_levels
    assert rb_step.alternatives == data.config.alternatives
    assert rb_step.sizes == sorted(data.config.sample_sizes)
    assert rb_step.monte_carlo_count == data.config.monte_carlo_count
    assert rb_step.result_storage is power_storage
    assert rb_step.results_path == data.results_path
    assert rb_step.with_chart == data.config.report_mode
