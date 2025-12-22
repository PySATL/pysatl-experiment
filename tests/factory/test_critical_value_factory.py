import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.experiment_config.critical_value.critical_value import (
    CriticalValueExperimentConfig,
)
from pysatl_experiment.configuration.experiment_data.critical_value.critical_value import CriticalValueExperimentData
from pysatl_experiment.configuration.model.criterion.criterion import Criterion
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.experiment_new.step.execution.critical_value.critical_value import CriticalValueExecutionStep
from pysatl_experiment.experiment_new.step.generation.generation import GenerationStep
from pysatl_experiment.experiment_new.step.report_building.critical_value.critical_value import (
    CriticalValueReportBuildingStep,
)
from pysatl_experiment.factory.critical_value.critical_value import CriticalValueExperimentFactory


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
    def __init__(self, counts_by_size: dict[int, int]):
        self.counts_by_size = counts_by_size

    def init(self):  # pragma: no cover
        pass

    def get_data(self, query):  # pragma: no cover
        return None

    def get_rvs_count(self, query):
        return self.counts_by_size.get(query.sample_size, 0)

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


class FakeLimitDistributionStorage:
    def __init__(self, has_result: set[tuple[str, int, int]]):
        # key: (criterion_code, sample_size, monte_carlo_count)
        self.has_result = has_result

    def init(self):  # pragma: no cover
        pass

    def get_data(self, query):
        key = (query.criterion_code, query.sample_size, query.monte_carlo_count)
        return object() if key in self.has_result else None

    def insert_data(self, model):  # pragma: no cover
        pass

    def delete_data(self, query):  # pragma: no cover
        pass

    def get_data_for_cv(self, query):
        # Accepts a query with fields: criterion_code, sample_size
        for crit_code, size, _mc in self.has_result:
            if crit_code == query.criterion_code and size == query.sample_size:
                return object()
        return None


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


class DeterministicCVFactory(CriticalValueExperimentFactory):
    def __init__(self, experiment_data: CriticalValueExperimentData, fake_generator: FakeGenerator):
        super().__init__(experiment_data)
        self._fake_generator = fake_generator

    def _get_hypothesis_generator_metadata(self):  # type: ignore[override]
        return "FAKEGENERATOR", [1.0], self._fake_generator

    def _get_criteria_config(self):  # type: ignore[override]
        crit = Criterion(criterion_code="FAKE", parameters=[0.0])
        return [
            CriterionConfig(
                criterion=crit, criterion_code=FakeStatistics.code(), statistics_class_object=FakeStatistics()
            )
        ]


# ---------- Fixtures and builders ----------


@pytest.fixture()
def tmp_results_path(tmp_path: Path) -> Path:
    return tmp_path


def build_cv_data(results_path: Path) -> CriticalValueExperimentData:
    config = CriticalValueExperimentConfig(
        experiment_type=ExperimentType.CRITICAL_VALUE,
        storage_connection=os.fspath(results_path / "test.sqlite"),
        run_mode=RunMode.REUSE,
        hypothesis=Hypothesis.EXPONENTIAL,
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[0.0])],
        report_mode=ReportMode.WITH_CHART,
        significance_levels=[0.05, 0.1],
        parallel_workers=1,
    )
    return CriticalValueExperimentData(
        name="cv_test",
        config=config,
        steps_done=type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})(),
        results_path=results_path,
    )


# ---------- Tests ----------


def test_generation_step_builds_needed_entries(tmp_results_path: Path):
    data = build_cv_data(tmp_results_path)
    fake_gen = FakeGenerator()
    factory = DeterministicCVFactory(data, fake_gen)

    # We have enough for size 10, but not for 20
    rvs_storage = FakeRandomValuesStorage(counts_by_size={10: 5, 20: 2})

    gen_step = factory._create_generation_step(rvs_storage)
    assert isinstance(gen_step, GenerationStep)
    assert len(gen_step.step_config) == 1
    s0 = gen_step.step_config[0]
    assert s0.sample_size == 20
    assert s0.count == 3
    assert s0.generator_name == "FAKEGENERATOR"
    assert s0.generator_parameters == [1.0]


def test_execution_step_includes_missing_results(tmp_results_path: Path):
    data = build_cv_data(tmp_results_path)
    fake_gen = FakeGenerator()
    factory = DeterministicCVFactory(data, fake_gen)

    rvs_storage = FakeRandomValuesStorage(counts_by_size={10: 5, 20: 5})
    # Present only for (FAKE_CODE, 10, 5)
    limit_storage = FakeLimitDistributionStorage(has_result={(FakeStatistics.code(), 10, 5)})
    exp_storage = FakeExperimentStorage(experiment_id=99)

    exec_step = factory._create_execution_step(rvs_storage, limit_storage, exp_storage)
    assert isinstance(exec_step, CriticalValueExecutionStep)
    assert exec_step.experiment_id == 99
    assert exec_step.monte_carlo_count == 5
    assert exec_step.hypothesis_generator_data.generator_name == "FAKEGENERATOR"
    assert exec_step.hypothesis_generator_data.parameters == [1.0]

    # Only one missing: size 20
    assert len(exec_step.step_config) == 1
    sd = exec_step.step_config[0]
    assert sd.sample_size == 20
    assert sd.statistics.code() == "FAKE_CODE"


def test_report_building_step_sets_expected_fields(tmp_results_path: Path):
    data = build_cv_data(tmp_results_path)
    fake_gen = FakeGenerator()
    factory = DeterministicCVFactory(data, fake_gen)

    limit_storage = FakeLimitDistributionStorage(has_result=set())
    rb_step = factory._create_report_building_step(limit_storage)
    assert isinstance(rb_step, CriticalValueReportBuildingStep)

    assert [c.criterion_code for c in rb_step.criteria_config] == [FakeStatistics.code()]
    assert rb_step.significance_levels == data.config.significance_levels
    assert rb_step.sizes == sorted(data.config.sample_sizes)
    assert rb_step.monte_carlo_count == data.config.monte_carlo_count
    assert rb_step.result_storage is limit_storage
    assert rb_step.results_path == data.results_path
    assert rb_step.with_chart == data.config.report_mode
