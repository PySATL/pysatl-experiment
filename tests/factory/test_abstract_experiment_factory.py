import os
import sys
import types
from pathlib import Path

import pytest

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
from pysatl_experiment.factory.model.abstract_experiment_factory.abstract_experiment_factory import (
    AbstractExperimentFactory,
)


# Stub line_profiler to avoid optional dependency issues in imports
_lp = types.ModuleType("line_profiler")


def _profile(func):
    return func


_lp.profile = _profile
sys.modules.setdefault("line_profiler", _lp)


# ----------------- Fakes / helpers -----------------


class FakeRandomValuesStorage:
    def __init__(self):
        self.deleted_all_queries = []

    def init(self):  # pragma: no cover
        pass

    def delete_all_data(self, query):
        self.deleted_all_queries.append(query)


class FakeResultStorage:
    def __init__(self):
        self.deleted_queries = []

    def init(self):  # pragma: no cover
        pass

    def delete_data(self, query):
        self.deleted_queries.append(query)


class FakeExperimentStorage:
    def __init__(self, experiment_id: int = 123):
        self._id = experiment_id

    def init(self):  # pragma: no cover
        pass

    def get_experiment_id(self, query):
        return self._id


class FakeStatistics:
    @staticmethod
    def code() -> str:
        return "FAKE_CODE"


class DummyStep:
    def __init__(self, name: str):
        self.name = name


class ConcreteFactory(
    AbstractExperimentFactory[TimeComplexityExperimentData, DummyStep, DummyStep, DummyStep, FakeResultStorage]
):
    def __init__(
        self,
        experiment_data: TimeComplexityExperimentData,
        data_storage: FakeRandomValuesStorage,
        result_storage: FakeResultStorage,
        experiment_storage: FakeExperimentStorage,
    ):
        super().__init__(experiment_data)
        self._ds = data_storage
        self._rs = result_storage
        self._es = experiment_storage

    # Deterministic overrides
    def _get_hypothesis_generator_metadata(self):  # type: ignore[override]
        return "FAKEGEN", [1.0], object()

    def _get_criteria_config(self):  # type: ignore[override]
        crit = Criterion(criterion_code="FAKE", parameters=[])
        return [
            CriterionConfig(
                criterion=crit, criterion_code=FakeStatistics.code(), statistics_class_object=FakeStatistics()
            )
        ]

    # Storage initializers
    def _init_data_storage(self):  # type: ignore[override]
        return self._ds

    def _init_result_storage(self):  # type: ignore[override]
        return self._rs

    def _init_experiment_storage(self):  # type: ignore[override]
        return self._es

    # Step creators
    def _create_generation_step(self, data_storage):  # type: ignore[override]
        return DummyStep("generation")

    def _create_execution_step(self, data_storage, result_storage, experiment_storage):  # type: ignore[override]
        return DummyStep("execution")

    def _create_report_building_step(self, result_storage):  # type: ignore[override]
        return DummyStep("report")


def build_tc_data(
    results_path: Path, run_mode: RunMode, is_gen_done: bool, is_exec_done: bool
) -> TimeComplexityExperimentData:
    config = TimeComplexityExperimentConfig(
        experiment_type=ExperimentType.TIME_COMPLEXITY,
        storage_connection=os.fspath(results_path / "test.sqlite"),
        run_mode=run_mode,
        hypothesis=Hypothesis.EXPONENTIAL,
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[])],
        report_mode=ReportMode.WITH_CHART,
    )
    steps_done = type(
        "StepsDone", (), {"is_generation_step_done": is_gen_done, "is_execution_step_done": is_exec_done}
    )()
    return TimeComplexityExperimentData(
        name="abstract_test",
        config=config,
        steps_done=steps_done,
        results_path=results_path,
    )


@pytest.fixture()
def tmp_results_path(tmp_path: Path) -> Path:
    return tmp_path


def test_create_experiment_steps_reuse_sets_steps(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    ds = FakeRandomValuesStorage()
    rs = FakeResultStorage()
    es = FakeExperimentStorage(experiment_id=11)
    factory = ConcreteFactory(data, ds, rs, es)

    steps = factory.create_experiment_steps()
    # Should not delete anything in REUSE
    assert ds.deleted_all_queries == []
    assert rs.deleted_queries == []

    # Both generation and execution present; report always present
    assert steps.generation_step is not None and isinstance(steps.generation_step, DummyStep)
    assert steps.execution_step is not None and isinstance(steps.execution_step, DummyStep)
    assert steps.report_building_step is not None and isinstance(steps.report_building_step, DummyStep)
    assert steps.experiment_id == 11


def test_create_experiment_steps_overwrite_deletes_and_respects_steps_done(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.OVERWRITE, is_gen_done=True, is_exec_done=True)
    ds = FakeRandomValuesStorage()
    rs = FakeResultStorage()
    es = FakeExperimentStorage(experiment_id=22)
    factory = ConcreteFactory(data, ds, rs, es)

    steps = factory.create_experiment_steps()

    # Overwrite triggers deletion of sample data for each sample size
    assert len(ds.deleted_all_queries) == len(data.config.sample_sizes)
    # Overwrite triggers deletion of result queries (1 criterion code × sizes)
    assert len(rs.deleted_queries) == len(data.config.sample_sizes)

    # Since steps_done indicates both done, generation/execution should be None; report present
    assert steps.generation_step is None
    assert steps.execution_step is None
    assert steps.report_building_step is not None


def test_create_experiment_steps_partial_steps_done(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=True, is_exec_done=False)
    ds = FakeRandomValuesStorage()
    rs = FakeResultStorage()
    es = FakeExperimentStorage(experiment_id=33)
    factory = ConcreteFactory(data, ds, rs, es)

    steps = factory.create_experiment_steps()
    # Generation skipped, execution included, report included
    assert steps.generation_step is None
    assert steps.execution_step is not None
    assert steps.report_building_step is not None
