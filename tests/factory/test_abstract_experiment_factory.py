"""Tests for abstract experiment factory base logic."""

import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from pysatl_criterion import DistributionType
from pysatl_criterion.generator.model import AbstractRVSGenerator
from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic

from pysatl_experiment.configuration.criteria_config import CriterionConfig
from pysatl_experiment.configuration.experiment_config.time_complexity_experiment_config import (
    TimeComplexityExperimentConfig,
)
from pysatl_experiment.configuration.experiment_data.time_complexity import TimeComplexityExperimentData
from pysatl_experiment.configuration.models.criterion import Criterion
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.configuration.models.step_type import StepType
from pysatl_experiment.experiment_execution.experiment_factory import AbstractExperimentFactory
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep


# Stub line_profiler to avoid optional dependency issues in imports
_lp: Any = types.ModuleType("line_profiler")


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

    def get_data(self, query):  # pragma: no cover
        return None

    def insert_data(self, data):  # pragma: no cover
        pass


class FakeExperimentStorage:
    def __init__(self, experiment_id: int = 123):
        self._id = experiment_id

    def init(self):  # pragma: no cover
        pass

    def get_experiment_id(self, query):
        return self._id


class FakeStatistics(AbstractGoodnessOfFitStatistic):  # TODO!!!!!!!!!!!
    @staticmethod
    def code() -> str:
        return "FAKE_CODE"


class DummyStep(IExperimentStep):
    def run(self) -> None:
        pass

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
        return "FAKEGEN", [1.0], AbstractRVSGenerator()  # TODO!!!!!!!!

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

    # Deterministic overrides for cleanup hooks  TODO: add tests
    def _delete_sample_data(self, data_storage):  # type: ignore[override]
        for sample_size in self.experiment_data.config.sample_sizes:
            data_storage.delete_all_data(sample_size)

    def _delete_results_from_storage(self, result_storage):  # type: ignore[override]
        for sample_size in self.experiment_data.config.sample_sizes:
            result_storage.delete_data(sample_size)


class MinimalConcreteFactory(AbstractExperimentFactory[Any, DummyStep, DummyStep, DummyStep, FakeResultStorage]):
    """Factory subclass preserving default concrete methods for testing."""

    def _create_generation_step(self, random_values_storage: Any) -> DummyStep:  # type: ignore[override]
        return DummyStep("generation")

    def _create_execution_step(self, data_storage: Any, result_storage: Any, experiment_storage: Any) -> DummyStep:  # type: ignore[override]
        return DummyStep("execution")

    def _create_report_building_step(self, result_storage: Any) -> DummyStep:  # type: ignore[override]
        return DummyStep("report")

    def _init_result_storage(self) -> FakeResultStorage:  # type: ignore[override]
        return FakeResultStorage()

    def _delete_sample_data(self, data_storage: Any) -> None:  # type: ignore[override]
        pass

    def _delete_results_from_storage(self, result_storage: Any) -> None:  # type: ignore[override]
        pass


def build_tc_data(
    results_path: Path, run_mode: RunMode, is_gen_done: bool, is_exec_done: bool
) -> TimeComplexityExperimentData:
    config = TimeComplexityExperimentConfig(
        experiment_type=ExperimentType.TIME_COMPLEXITY,
        storage_connection=os.fspath(results_path / "test.sqlite"),
        run_mode=run_mode,
        hypothesis=DistributionType.EXPONENTIAL,
        hypothesis_params={},  # TODO: {"scale": 1.0}
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[])],
        report_mode=ReportMode.WITH_CHART,
        parallel_workers=1,
    )
    steps_done = type(
        "StepsDone", (), {"is_generation_step_done": is_gen_done, "is_execution_step_done": is_exec_done}
    )()
    return TimeComplexityExperimentData(
        experiment_name="abstract_test",
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


# Checks that _init_data_storage instantiates and initializes AlchemyRandomValuesStorage.
def test_init_data_storage(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    data.config.storage_connection = "sqlite://"
    factory = MinimalConcreteFactory(experiment_data=data)
    storage = factory._init_data_storage()
    assert storage is not None
    assert storage._initialized is True


# Checks that _init_experiment_storage instantiates and initializes AlchemyExperimentStorage.
def test_init_experiment_storage(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    data.config.storage_connection = "sqlite://"
    factory = MinimalConcreteFactory(experiment_data=data)
    storage = factory._init_experiment_storage()
    assert storage is not None
    assert storage._initialized is True


# Checks that _get_experiment_id correctly resolves an existing time complexity experiment.
def test_get_experiment_id_time_complexity(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    factory = MinimalConcreteFactory(experiment_data=data)
    mock_storage = FakeExperimentStorage(experiment_id=42)
    exp_id = factory._get_experiment_id(mock_storage)
    assert exp_id == 42


# Checks that _get_experiment_id correctly resolves an existing critical value experiment.
def test_get_experiment_id_critical_value(tmp_results_path: Path):
    from pysatl_experiment.configuration.experiment_config.critical_value_experiment_config import (
        CriticalValueExperimentConfig,
    )
    from pysatl_experiment.configuration.experiment_data.critical_value import CriticalValueExperimentData

    config = CriticalValueExperimentConfig(
        experiment_type=ExperimentType.CRITICAL_VALUE,
        storage_connection=os.fspath(tmp_results_path / "test.sqlite"),
        run_mode=RunMode.REUSE,
        hypothesis=DistributionType.EXPONENTIAL,
        hypothesis_params={},
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[])],
        report_mode=ReportMode.WITH_CHART,
        parallel_workers=1,
        significance_levels=[0.05, 0.01],
    )
    steps_done = type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})()
    data = CriticalValueExperimentData(
        experiment_name="cv_test",
        config=config,
        steps_done=steps_done,
        results_path=tmp_results_path,
    )
    factory = MinimalConcreteFactory(experiment_data=data)
    mock_storage = FakeExperimentStorage(experiment_id=55)
    exp_id = factory._get_experiment_id(mock_storage)
    assert exp_id == 55


# Checks that _get_experiment_id correctly resolves an existing power experiment.
def test_get_experiment_id_power(tmp_results_path: Path):
    from pysatl_experiment.configuration.experiment_config.power_experiment_config import PowerExperimentConfig
    from pysatl_experiment.configuration.experiment_data.power import PowerExperimentData
    from pysatl_experiment.configuration.models.alternative import Alternative

    config = PowerExperimentConfig(
        experiment_type=ExperimentType.POWER,
        storage_connection=os.fspath(tmp_results_path / "test.sqlite"),
        run_mode=RunMode.REUSE,
        hypothesis=DistributionType.EXPONENTIAL,
        hypothesis_params={},
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[])],
        report_mode=ReportMode.WITH_CHART,
        parallel_workers=1,
        significance_levels=[0.05],
        alternatives=[Alternative(distribution_type=DistributionType.NORMAL, parameters={"loc": 0.0, "scale": 1.0})],
    )
    steps_done = type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})()
    data = PowerExperimentData(
        experiment_name="power_test",
        config=config,
        steps_done=steps_done,
        results_path=tmp_results_path,
    )
    factory = MinimalConcreteFactory(experiment_data=data)
    mock_storage = FakeExperimentStorage(experiment_id=77)
    exp_id = factory._get_experiment_id(mock_storage)
    assert exp_id == 77


# Checks that _get_experiment_id raises ValueError when experiment is not found in storage.
def test_get_experiment_id_not_found_raises(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    factory = MinimalConcreteFactory(experiment_data=data)
    mock_storage = FakeExperimentStorage(experiment_id=None)
    with pytest.raises(ValueError, match="Experiment not found"):
        factory._get_experiment_id(mock_storage)


# Checks that _get_criteria_config filters unknown criteria and maps known criteria to statistics subclasses.
def test_get_criteria_config(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    data.config.hypothesis = DistributionType.NORMAL
    data.config.criteria = [
        Criterion(criterion_code="UNKNOWN_CRIT", parameters=[]),
        Criterion(criterion_code="KS", parameters=[]),
    ]
    factory = MinimalConcreteFactory(experiment_data=data)
    criteria_configs = factory._get_criteria_config()
    assert len(criteria_configs) == 1
    assert criteria_configs[0].criterion.criterion_code == "KS"
    assert criteria_configs[0].criterion_code == "KS_NORMALITY_GOODNESS_OF_FIT"
    assert criteria_configs[0].statistics_class_object is not None


# Checks that _create_critical_value_queries produces product of statistics and sample sizes (2x3=6).
def test_create_critical_value_queries():
    statistics_codes = ["STAT_A", "STAT_B"]
    sample_sizes = [10, 20, 50]
    monte_carlo_count = 100
    queries = AbstractExperimentFactory._create_critical_value_queries(
        statistics_codes=statistics_codes,
        sample_sizes=sample_sizes,
        monte_carlo_count=monte_carlo_count,
    )
    assert len(queries) == 6
    assert queries[0].criterion_code == "STAT_A"
    assert queries[0].sample_size == 10
    assert queries[0].monte_carlo_count == 100
    assert queries[-1].criterion_code == "STAT_B"
    assert queries[-1].sample_size == 50


# Checks that _create_time_complexity_queries produces product of statistics and sample sizes (2x3=6).
def test_create_time_complexity_queries():
    statistics_codes = ["STAT_A", "STAT_B"]
    sample_sizes = [10, 20, 50]
    monte_carlo_count = 100
    queries = AbstractExperimentFactory._create_time_complexity_queries(
        experiment_name="tc_exp",
        statistics_codes=statistics_codes,
        sample_sizes=sample_sizes,
        monte_carlo_count=monte_carlo_count,
    )
    assert len(queries) == 6
    assert queries[0].experiment_name == "tc_exp"
    assert queries[0].criterion_code == "STAT_A"
    assert queries[0].sample_size == 10
    assert queries[0].samples_count == 100
    assert queries[-1].criterion_code == "STAT_B"
    assert queries[-1].sample_size == 50


# Checks that _create_power_queries produces product of stats, sample sizes, sig levels, and alts (2x2x2x2=16).
def test_create_power_queries(tmp_results_path: Path):
    from pysatl_experiment.configuration.experiment_config.power_experiment_config import PowerExperimentConfig
    from pysatl_experiment.configuration.experiment_data.power import PowerExperimentData
    from pysatl_experiment.configuration.models.alternative import Alternative

    config = PowerExperimentConfig(
        experiment_type=ExperimentType.POWER,
        storage_connection=os.fspath(tmp_results_path / "test.sqlite"),
        run_mode=RunMode.REUSE,
        hypothesis=DistributionType.EXPONENTIAL,
        hypothesis_params={},
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[])],
        report_mode=ReportMode.WITH_CHART,
        parallel_workers=1,
        significance_levels=[0.05, 0.01],
        alternatives=[
            Alternative(distribution_type=DistributionType.NORMAL, parameters={"loc": 0.0}),
            Alternative(distribution_type=DistributionType.WEIBULL, parameters={"c": 1.5}),
        ],
    )
    steps_done = type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})()
    data = PowerExperimentData(
        experiment_name="power_exp",
        config=config,
        steps_done=steps_done,
        results_path=tmp_results_path,
    )
    factory = MinimalConcreteFactory(experiment_data=data)
    queries = factory._create_power_queries(
        statistics_codes=["STAT_1", "STAT_2"],
        sample_sizes=[10, 20],
        monte_carlo_count=50,
    )
    assert len(queries) == 16
    assert queries[0].criterion_code == "STAT_1"
    assert queries[0].sample_size == 10
    assert queries[0].significance_level == 0.05
    assert queries[0].alternative_code == DistributionType.NORMAL
    assert queries[0].monte_carlo_count == 50


# Checks that _delete_hypothesis_sample_data issues delete_all_data for each sample size.
def test_delete_hypothesis_sample_data(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    factory = MinimalConcreteFactory(experiment_data=data)
    fake_storage = FakeRandomValuesStorage()
    factory._get_hypothesis_generator_metadata = lambda: ("EXP_GEN", {"scale": 1.0}, None)  # type: ignore[method-assign]
    factory._delete_hypothesis_sample_data(fake_storage)

    assert len(fake_storage.deleted_all_queries) == len(data.config.sample_sizes)
    assert fake_storage.deleted_all_queries[0].generator_code == "EXP_GEN"
    assert fake_storage.deleted_all_queries[0].sample_size == data.config.sample_sizes[0]
    assert fake_storage.deleted_all_queries[0].experiment_name == data.experiment_name


# Checks that _delete_alternatives_sample_data issues delete_all_data for every alternative and sample size.
def test_delete_alternatives_sample_data(tmp_results_path: Path):
    from pysatl_experiment.configuration.experiment_config.power_experiment_config import PowerExperimentConfig
    from pysatl_experiment.configuration.experiment_data.power import PowerExperimentData
    from pysatl_experiment.configuration.models.alternative import Alternative

    config = PowerExperimentConfig(
        experiment_type=ExperimentType.POWER,
        storage_connection=os.fspath(tmp_results_path / "test.sqlite"),
        run_mode=RunMode.REUSE,
        hypothesis=DistributionType.EXPONENTIAL,
        hypothesis_params={},
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        sample_sizes=[10, 20],
        monte_carlo_count=5,
        criteria=[Criterion(criterion_code="FAKE", parameters=[])],
        report_mode=ReportMode.WITH_CHART,
        parallel_workers=1,
        significance_levels=[0.05],
        alternatives=[
            Alternative(distribution_type=DistributionType.NORMAL, parameters={"loc": 0.0}),
            Alternative(distribution_type=DistributionType.WEIBULL, parameters={"c": 1.5}),
        ],
    )
    steps_done = type("StepsDone", (), {"is_generation_step_done": False, "is_execution_step_done": False})()
    data = PowerExperimentData(
        experiment_name="power_alt_del",
        config=config,
        steps_done=steps_done,
        results_path=tmp_results_path,
    )
    factory = MinimalConcreteFactory(experiment_data=data)
    fake_storage = FakeRandomValuesStorage()
    factory._delete_alternatives_sample_data(fake_storage)

    assert len(fake_storage.deleted_all_queries) == 4
    assert fake_storage.deleted_all_queries[0].generator_code == DistributionType.NORMAL
    assert fake_storage.deleted_all_queries[0].sample_size == 10
    assert fake_storage.deleted_all_queries[1].generator_code == DistributionType.WEIBULL
    assert fake_storage.deleted_all_queries[1].sample_size == 10


# Checks that _get_generator_class_object successfully instantiates a known generator subclass.
def test_get_generator_class_object_found(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    factory = MinimalConcreteFactory(experiment_data=data)

    class CustomTestGenerator(AbstractRVSGenerator):
        def __init__(self, param1: float = 1.0, param2: float = 2.0):
            self.param1 = param1
            self.param2 = param2

        @classmethod
        def code(cls) -> str:
            return "CUSTOM"

        @classmethod
        def distribution_type(cls) -> DistributionType:
            return DistributionType.NORMAL

        def parameters(self) -> dict[str, float]:
            return {"param1": self.param1, "param2": self.param2}

        def generate(self, size: int):
            return []

    gen = factory._get_generator_class_object("CUSTOMTESTGENERATOR", {"param1": 10.0, "param2": 20.0})
    assert isinstance(gen, CustomTestGenerator)
    assert gen.param1 == 10.0
    assert gen.param2 == 20.0


# Checks that _get_generator_class_object raises ValueError for unknown generator names.
def test_get_generator_class_object_unknown_raises(tmp_results_path: Path):
    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    factory = MinimalConcreteFactory(experiment_data=data)
    with pytest.raises(ValueError, match="Unknown generator: NONEXISTENT_GEN"):
        factory._get_generator_class_object("NONEXISTENT_GEN", {})


# Checks that _get_hypothesis_generator_metadata retrieves generator code, parameters, and instance.
def test_get_hypothesis_generator_metadata(tmp_results_path: Path):
    from unittest.mock import MagicMock, patch

    data = build_tc_data(tmp_results_path, RunMode.REUSE, is_gen_done=False, is_exec_done=False)
    factory = MinimalConcreteFactory(experiment_data=data)

    mock_gen = MagicMock()
    mock_gen.code.return_value = "EXP_GEN_CODE"
    mock_gen.parameters.return_value = {"scale": 1.0}

    with patch(
        "pysatl_experiment.experiment_execution.experiment_factory.abstract_experiment_factory.get_available_generator",
        return_value=mock_gen,
    ) as mock_get_gen:
        code, params, instance = factory._get_hypothesis_generator_metadata()
        mock_get_gen.assert_called_once_with(data.config.hypothesis, None)
        assert code == "EXP_GEN_CODE"
        assert params == {"scale": 1.0}
        assert instance is mock_gen
