"""Tests for the shared multithreading execution step base class."""

from __future__ import annotations

import sys
import types
from concurrent.futures import Future
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.experiment_execution.parallel import scheduler as scheduler_module
from pysatl_experiment.experiment_execution.parallel.task_spec import TaskSpec
from pysatl_experiment.experiment_execution.step.execution_step import multithreading_execution_step
from pysatl_experiment.experiment_execution.step.execution_step.multithreading_execution_step import (
    ExecutionTaskResult,
    MultithreadingExecutionStep,
)
from pysatl_experiment.persistence.models.random_values import RandomValuesModel
from pysatl_experiment.persistence.random_values_storage import AlchemyRandomValuesStorage


FAKE_STATISTIC_MODULE = "fake_statistics_for_multithreading_tests"
BAD_CRITERION_CODE = "BAD"


class FakeStatistic:
    """Minimal statistic stub that can be instantiated without arguments."""

    def __init__(self) -> None:
        self.code_value = "FAKE"


class InlineExecutor:
    """Process pool stub that executes every submitted callable immediately."""

    instances: ClassVar[list[InlineExecutor]] = []

    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers
        self.submitted: list[tuple[Any, ...]] = []
        self.shutdown_calls: int = 0
        InlineExecutor.instances.append(self)

    def submit(self, fn, *args, **kwargs) -> Future:  # noqa: ANN001
        """Run ``fn`` synchronously and return an already resolved future."""
        self.submitted.append(args)
        future: Future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # noqa: BLE001
            future.set_exception(exc)
        return future

    def shutdown(self, wait: bool = True) -> None:
        """Record that the scheduler stopped the executor."""
        self.shutdown_calls += 1


class StubExecutionStep(MultithreadingExecutionStep):
    """Concrete step that records what the base class persists."""

    def __init__(self, task_specs: list[TaskSpec], saved_batches: list[list[Any]], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.task_specs = task_specs
        self.saved_batches = saved_batches

    def _collect_tasks(self) -> list[TaskSpec]:
        return list(self.task_specs)

    @staticmethod
    def _execute_task(spec: TaskSpec) -> ExecutionTaskResult:
        if spec.criterion_code == BAD_CRITERION_CODE:
            raise ValueError("bad task")
        return ExecutionTaskResult(spec=spec, worker_result=f"result:{spec.criterion_code}")

    def _to_model(self, result: ExecutionTaskResult) -> tuple[str, str]:
        return (result.spec.criterion_code, result.worker_result)

    def _bulk_save(self, models: list[tuple[str, str]]) -> None:
        self.saved_batches.append(list(models))


@pytest.fixture()
def inline_executor(monkeypatch: pytest.MonkeyPatch) -> type[InlineExecutor]:
    """Replace the process pool with a synchronous, deterministic executor."""
    InlineExecutor.instances = []
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)
    return InlineExecutor


@pytest.fixture()
def fake_statistic_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Register an importable module exposing ``FakeStatistic``."""
    module = types.ModuleType(FAKE_STATISTIC_MODULE)
    module.FakeStatistic = FakeStatistic  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, FAKE_STATISTIC_MODULE, module)
    return module


@pytest.fixture()
def storage_factory(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the random values storage with a controllable factory."""
    factory = MagicMock(name="AlchemyRandomValuesStorage")
    monkeypatch.setattr(multithreading_execution_step, "AlchemyRandomValuesStorage", factory)
    return factory


def make_spec(**overrides: Any) -> TaskSpec:
    """Build a task spec whose defaults the loader tests can rely on."""
    values: dict[str, Any] = {
        "experiment_type": ExperimentType.CRITICAL_VALUE,
        "statistic_class_name": "FakeStatistic",
        "statistic_module": FAKE_STATISTIC_MODULE,
        "sample_size": 5,
        "monte_carlo_count": 1,
        "db_path": "sqlite://",
        "experiment_name": "",
        "criterion_code": "KS",
        "sample_generator_code": "NORM",
        "sample_generator_parameters": {"mean": 0.0},
        "alternative_generator": "ALT",
        "hypothesis_generator": "HYP",
    }
    values.update(overrides)
    return TaskSpec(**values)


def make_step(
    task_specs: list[TaskSpec],
    saved_batches: list[list[Any]] | None = None,
    **overrides: Any,
) -> StubExecutionStep:
    """Build a stub step wired to an in-memory batch recorder."""
    values: dict[str, Any] = {
        "experiment_id": 7,
        "experiment_name": "experiment",
        "step_config": [],
        "monte_carlo_count": 1,
        "result_storage": MagicMock(),
        "storage_connection": "sqlite://",
        "parallel_workers": 1,
    }
    values.update(overrides)
    return StubExecutionStep(task_specs, [] if saved_batches is None else saved_batches, **values)


# Checks that the constructor stores every configuration argument.
@pytest.mark.parametrize(
    ("argument", "value"),
    [
        pytest.param("experiment_id", 11, id="experiment-id"),
        pytest.param("experiment_name", "named", id="experiment-name"),
        pytest.param("monte_carlo_count", 42, id="monte-carlo-count"),
        pytest.param("storage_connection", "sqlite:///other.sqlite", id="storage-connection"),
        pytest.param("parallel_workers", 5, id="parallel-workers"),
    ],
)
def test_constructor_stores_configuration_argument(argument: str, value: Any) -> None:
    step_config: list[Any] = [object()]

    step = make_step([], step_config=step_config, **{argument: value})

    assert getattr(step, argument) == value
    assert step.step_config is step_config


# Checks that the constructor keeps the provided step data and result storage.
def test_constructor_keeps_step_config_and_result_storage() -> None:
    step_config: list[Any] = [object()]
    result_storage = MagicMock()

    step = make_step([], step_config=step_config, result_storage=result_storage)

    assert step.step_config is step_config
    assert step.result_storage is result_storage


# Checks that the base class keeps all four template methods abstract.
def test_base_class_declares_four_abstract_methods() -> None:
    assert MultithreadingExecutionStep.__abstractmethods__ == {
        "_collect_tasks",
        "_execute_task",
        "_to_model",
        "_bulk_save",
    }


# Checks that the abstract base class itself cannot be instantiated.
def test_base_class_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        MultithreadingExecutionStep()  # type: ignore[abstract]


# Checks that the abstract method bodies are callable and return None.
def test_abstract_method_bodies_return_none() -> None:
    step = make_step([])

    assert MultithreadingExecutionStep._collect_tasks(step) is None
    assert MultithreadingExecutionStep._execute_task(make_spec()) is None
    assert MultithreadingExecutionStep._to_model(step, ExecutionTaskResult(make_spec(), "payload")) is None
    assert MultithreadingExecutionStep._bulk_save(step, []) is None


# Checks that run executes every collected task and persists the results.
def test_run_executes_all_collected_tasks(inline_executor: type[InlineExecutor]) -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([make_spec(criterion_code="KS"), make_spec(criterion_code="AD")], saved_batches)

    step.run()

    saved = [model for batch in saved_batches for model in batch]
    assert saved == [("KS", "result:KS"), ("AD", "result:AD")]


# Checks that run flushes a partially filled buffer once all tasks are done.
def test_run_flushes_partial_buffer_on_completion(inline_executor: type[InlineExecutor]) -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([make_spec(criterion_code=code) for code in ("A", "B", "C", "D", "E")], saved_batches)

    step.run()

    assert saved_batches == [
        [("A", "result:A"), ("B", "result:B")],
        [("C", "result:C"), ("D", "result:D")],
        [("E", "result:E")],
    ]


# Checks that run without tasks never touches the result storage.
def test_run_without_tasks_saves_nothing(inline_executor: type[InlineExecutor]) -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([], saved_batches)

    step.run()

    assert saved_batches == []


# Checks that run returns None.
def test_run_returns_none(inline_executor: type[InlineExecutor]) -> None:
    step = make_step([make_spec()])

    assert step.run() is None


# Checks that the scheduler is created with the configured worker count.
def test_run_uses_configured_parallel_workers(inline_executor: type[InlineExecutor]) -> None:
    step = make_step([make_spec()], parallel_workers=3)

    step.run()

    assert [executor.max_workers for executor in inline_executor.instances] == [3]
    assert inline_executor.instances[0].shutdown_calls == 1


# Checks that a failing task propagates and already buffered results are saved.
def test_run_flushes_buffered_results_when_a_task_fails(inline_executor: type[InlineExecutor]) -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([make_spec(criterion_code="OK"), make_spec(criterion_code=BAD_CRITERION_CODE)], saved_batches)

    with pytest.raises(ValueError, match="bad task"):
        step.run()

    assert saved_batches == [[("OK", "result:OK")]]


# Checks that save_batch converts buffered results and persists the models.
def test_save_batch_converts_results_and_persists_models() -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([], saved_batches)
    results = [ExecutionTaskResult(make_spec(criterion_code="KS"), "result:KS")]

    step.save_batch(results)

    assert saved_batches == [[("KS", "result:KS")]]


# Checks that save_batch skips the storage call for an empty batch.
def test_save_batch_skips_storage_for_empty_batch() -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([], saved_batches)

    step.save_batch([])

    assert saved_batches == []


# Checks that save_batch preserves the order of the buffered results.
@pytest.mark.parametrize("codes", [("A", "B", "C"), ("C", "B", "A"), ("B",)])
def test_save_batch_preserves_result_order(codes: tuple[str, ...]) -> None:
    saved_batches: list[list[Any]] = []
    step = make_step([], saved_batches)
    results = [ExecutionTaskResult(make_spec(criterion_code=code), f"result:{code}") for code in codes]

    step.save_batch(results)

    assert saved_batches == [[(code, f"result:{code}") for code in codes]]


# Checks that the task result container keeps both of its components.
def test_execution_task_result_stores_spec_and_worker_result() -> None:
    spec = make_spec()

    result = ExecutionTaskResult(spec=spec, worker_result="payload")

    assert result.spec is spec
    assert result.worker_result == "payload"


# Checks that task results compare by value.
@pytest.mark.parametrize("worker_result", ["payload", 0, [1, 2]])
def test_execution_task_result_equality(worker_result: Any) -> None:
    assert ExecutionTaskResult(make_spec(), worker_result) == ExecutionTaskResult(make_spec(), worker_result)


# Checks that the loader reads the stored samples and builds the statistic.
def test_load_samples_and_statistics_returns_samples_and_statistic(
    storage_factory: MagicMock, fake_statistic_module: types.ModuleType
) -> None:
    storage_factory.return_value.get_count_data.return_value = [
        MagicMock(data=[0.1, 0.2]),
        MagicMock(data=[0.3, 0.4]),
    ]

    samples, statistics = MultithreadingExecutionStep._load_samples_and_statistics(make_spec(monte_carlo_count=2))

    assert samples == [[0.1, 0.2], [0.3, 0.4]]
    assert isinstance(statistics, FakeStatistic)
    storage_factory.assert_called_once_with("sqlite://")
    storage_factory.return_value.init.assert_called_once_with()


# Checks that the loader builds the count query directly from the task spec.
def test_load_samples_and_statistics_builds_query_from_spec(
    storage_factory: MagicMock, fake_statistic_module: types.ModuleType
) -> None:
    storage_factory.return_value.get_count_data.return_value = [MagicMock(data=[0.5])]

    MultithreadingExecutionStep._load_samples_and_statistics(
        make_spec(sample_size=3, monte_carlo_count=1, experiment_name="exp")
    )

    query = storage_factory.return_value.get_count_data.call_args[0][0]
    assert query.generator_code == "NORM"
    assert query.experiment_name == "exp"
    assert query.sample_size == 3
    assert query.count == 1
    assert query.generator_parameters == {"mean": 0.0}


# Checks that the loader uses the fallback generator code when none is given.
def test_load_samples_and_statistics_uses_generator_fallback(
    storage_factory: MagicMock, fake_statistic_module: types.ModuleType
) -> None:
    storage_factory.return_value.get_count_data.return_value = [MagicMock(data=[0.5])]

    MultithreadingExecutionStep._load_samples_and_statistics(make_spec(sample_generator_code=""))

    query = storage_factory.return_value.get_count_data.call_args[0][0]
    assert query.generator_code == "ALT"


# Checks that the loader rejects missing or insufficient stored samples.
@pytest.mark.parametrize(
    ("rows", "monte_carlo_count"),
    [
        pytest.param(None, 1, id="no-rows"),
        pytest.param([], 1, id="empty-row-list"),
        pytest.param([MagicMock(data=[0.1])], 2, id="too-few-rows"),
    ],
)
def test_load_samples_and_statistics_raises_for_insufficient_data(
    storage_factory: MagicMock, rows: list[Any] | None, monte_carlo_count: int
) -> None:
    storage_factory.return_value.get_count_data.return_value = rows

    with pytest.raises(ValueError, match="Not enough data in storage."):
        MultithreadingExecutionStep._load_samples_and_statistics(make_spec(monte_carlo_count=monte_carlo_count))


# Checks that the loader works against a real SQLite random values storage.
def test_load_samples_and_statistics_with_real_storage(tmp_path: Path, fake_statistic_module: types.ModuleType) -> None:
    db_url = f"sqlite:///{tmp_path / 'random_values.sqlite'}"
    storage = AlchemyRandomValuesStorage(db_url)
    storage.init()
    for index, value in enumerate((1.0, 2.0), start=1):
        storage.insert_data(
            RandomValuesModel(
                generator_code="NORM",
                generator_parameters=[0.0, 1.0],
                sample_size=5,
                experiment_name=str(index),
                data=[value] * 5,
            )
        )
    spec = make_spec(
        db_path=db_url,
        sample_size=5,
        monte_carlo_count=2,
        sample_generator_code="NORM",
        sample_generator_parameters=[0.0, 1.0],
    )

    samples, statistics = MultithreadingExecutionStep._load_samples_and_statistics(spec)

    assert samples == [[1.0] * 5, [2.0] * 5]
    assert isinstance(statistics, FakeStatistic)


# Checks the resolution order of the sample generator code.
@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        pytest.param({"sample_generator_code": "SAMPLE"}, "SAMPLE", id="sample-code-first"),
        pytest.param({"sample_generator_code": ""}, "ALT", id="alternative-second"),
        pytest.param({"sample_generator_code": "", "alternative_generator": ""}, "HYP", id="hypothesis-last"),
        pytest.param(
            {"sample_generator_code": "SAMPLE", "alternative_generator": "ALT"},
            "SAMPLE",
            id="sample-code-beats-alternative",
        ),
        pytest.param(
            {"sample_generator_code": "SAMPLE", "alternative_generator": "ALT", "hypothesis_generator": "HYP"},
            "SAMPLE",
            id="all-codes-set",
        ),
    ],
)
def test_get_sample_generator_code_resolution_order(overrides: dict[str, Any], expected: str) -> None:
    assert MultithreadingExecutionStep._get_sample_generator_code(make_spec(**overrides)) == expected
