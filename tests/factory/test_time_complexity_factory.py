import os
import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest
from numpy import float64

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.experiment_config.time_complexity.time_complexity import (
    TimeComplexityExperimentConfig,
)
from pysatl_experiment.configuration.experiment_data.time_complexity.time_complexity import TimeComplexityExperimentData
from pysatl_experiment.configuration.model.criterion.criterion import Criterion
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.experiment_new.step.execution.time_complexity.time_complexity import TimeComplexityExecutionStep
from pysatl_experiment.experiment_new.step.generation.generation import GenerationStep
from pysatl_experiment.experiment_new.step.report_building.time_complexity.time_complexity import (
    TimeComplexityReportBuildingStep,
)
from pysatl_experiment.factory.time_complexity.time_complexity import TimeComplexityExperimentFactory
from pysatl_experiment.persistence.model.experiment.experiment import IExperimentStorage
from pysatl_experiment.persistence.model.random_values.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.model.time_complexity.time_complexity import ITimeComplexityStorage


# Provide a stub for line_profiler to avoid optional dependency during imports
_lp: Any = types.ModuleType("line_profiler")


def _profile(func):
    return func


_lp.profile = _profile
sys.modules.setdefault("line_profiler", _lp)


# ---------- Fakes / Test Doubles ----------


class FakeGenerator:
    def __init__(self):
        self.called_with_sizes = []

    def generate(self, n):
        # Return a deterministic sample to satisfy typing; tests don't run steps.
        self.called_with_sizes.append(n)
        return [0.0 for _ in range(n)]


class FakeStatistics(AbstractGoodnessOfFitStatistic):
    def execute_statistic(self, rvs, **kwargs) -> float | float64:
        return 0

    @staticmethod
    def code() -> str:
        return "FAKE_CODE"


class FakeRandomValuesStorage:
    def __init__(self, counts_by_size: dict[int, int]):
        self.counts_by_size = counts_by_size
        self.deleted_queries: list[Any] = []

    def init(self):  # pragma: no cover - not used in these tests
        pass

    def get_data(self, query):  # pragma: no cover
        return None

    def get_rvs_count(self, query):
        # Query has attribute sample_size per factory implementation
        return self.counts_by_size.get(query.sample_size, 0)

    def insert_all_data(self, query):  # pragma: no cover
        pass

    def get_all_data(self, query):  # pragma: no cover
        return None

    def delete_all_data(self, query):  # pragma: no cover - not used here
        self.deleted_queries.append(query)

    def insert_data(self, model):  # pragma: no cover - steps aren't run
        pass

    def delete_data(self, query):  # pragma: no cover
        pass


class FakeTimeComplexityStorage(ITimeComplexityStorage):
    def __init__(self, has_result: set[tuple[str, int, int]]):
        # key: (criterion_code, sample_size, monte_carlo_count)
        self.has_result = has_result
        self.deleted_queries: list[Any] = []

    def init(self):  # pragma: no cover - not used in these tests
        pass

    def get_data(self, query):
        key = (
            query.criterion_code,
            query.sample_size,
            query.monte_carlo_count,
        )
        return object() if key in self.has_result else None

    def delete_data(self, query):  # pragma: no cover - not used here
        self.deleted_queries.append(query)

    def insert_data(self, model):  # pragma: no cover - steps aren't run
        pass


class FakeExperimentStorage(IExperimentStorage):
    def __init__(self, experiment_id: int):
        self._id = experiment_id

    def init(self):  # pragma: no cover - not used in these tests
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


class DeterministicTCFactory(TimeComplexityExperimentFactory):
    """Factory with deterministic overrides to avoid heavy dependencies."""

    def __init__(self, experiment_data: TimeComplexityExperimentData, fake_generator: FakeGenerator):
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


# ---------- Fixtures ----------


@pytest.fixture()
def tmp_results_path(tmp_path: Path) -> Path:
    return tmp_path


def build_time_complexity_data(results_path: Path) -> TimeComplexityExperimentData:
    config = TimeComplexityExperimentConfig(
        experiment_type=ExperimentType.TIME_COMPLEXITY,
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
        parallel_workers=1,
    )
    return TimeComplexityExperimentData(
        name="tc_test",
        config=config,
        steps_done=type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})(),
        results_path=results_path,
    )


# ---------- Tests ----------


def test_create_generation_step_builds_needed_entries(tmp_results_path: Path):
    data = build_time_complexity_data(tmp_results_path)
    fake_generator = FakeGenerator()
    factory = DeterministicTCFactory(data, fake_generator)

    # Pretend we already have counts for size 10 but not enough for 20
    rvs_storage = cast(IRandomValuesStorage, FakeRandomValuesStorage(counts_by_size={10: 5, 20: 2}))

    gen_step = factory._create_generation_step(rvs_storage)
    assert isinstance(gen_step, GenerationStep)

    # For size 10, rvs_count == monte_carlo -> no work; for size 20 needed = 3
    assert len(gen_step.step_config) == 1
    step0 = gen_step.step_config[0]
    assert step0.sample_size == 20
    assert step0.count == 3  # 5 - 2
    assert step0.generator_name == "FAKEGENERATOR"
    assert step0.generator_parameters == [1.0]


def test_create_execution_step_includes_missing_results(tmp_results_path: Path):
    data = build_time_complexity_data(tmp_results_path)
    fake_generator = FakeGenerator()
    factory = DeterministicTCFactory(data, fake_generator)

    rvs_storage = cast(IRandomValuesStorage, FakeRandomValuesStorage(counts_by_size={10: 5, 20: 5}))

    # Only (code, 10, 5) exists; (code, 20, 5) is missing -> expect one step
    tc_storage = FakeTimeComplexityStorage(has_result={(FakeStatistics.code(), 10, 5)})
    exp_storage = FakeExperimentStorage(experiment_id=42)

    exec_step = factory._create_execution_step(rvs_storage, tc_storage, exp_storage)
    assert isinstance(exec_step, TimeComplexityExecutionStep)
    assert exec_step.experiment_id == 42
    assert exec_step.monte_carlo_count == 5
    assert exec_step.hypothesis_generator_data.generator_name == "FAKEGENERATOR"
    assert exec_step.hypothesis_generator_data.parameters == [1.0]

    assert len(exec_step.step_config) == 1
    sd = exec_step.step_config[0]
    assert sd.sample_size == 20
    assert sd.statistics.code() == "FAKE_CODE"


def test_create_report_building_step_sets_expected_fields(tmp_results_path: Path):
    data = build_time_complexity_data(tmp_results_path)
    fake_generator = FakeGenerator()
    factory = DeterministicTCFactory(data, fake_generator)

    tc_storage = FakeTimeComplexityStorage(has_result=set())
    rb_step = factory._create_report_building_step(tc_storage)
    assert isinstance(rb_step, TimeComplexityReportBuildingStep)

    # Validate fields propagated from experiment data and criteria config
    assert [c.criterion_code for c in rb_step.criteria_config] == [FakeStatistics.code()]
    assert rb_step.sizes == sorted(data.config.sample_sizes)
    assert rb_step.monte_carlo_count == data.config.monte_carlo_count
    assert rb_step.result_storage is tc_storage
    assert rb_step.results_path == data.results_path
    assert rb_step.with_chart == data.config.report_mode
