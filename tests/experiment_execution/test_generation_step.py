"""Tests for the random sample generation step."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pysatl_experiment.experiment_execution.step.generation_step.generation_step import GenerationStep
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)
from pysatl_experiment.persistence.models.random_values import RandomValuesModel


def make_generator(
    code: str = "NORMAL",
    parameters: list[float] | None = None,
    values: list[float] | None = None,
) -> MagicMock:
    """Build a generator double exposing the code/parameters/generate API."""
    generator = MagicMock()
    generator.code.return_value = code
    generator.parameters.return_value = [0.0, 1.0] if parameters is None else parameters
    generator.generate.return_value = [0.1, 0.2] if values is None else values
    return generator


def make_data(
    generator: MagicMock | None = None,
    sample_size: int = 2,
    samples_count: int = 3,
) -> GenerationData:
    """Build a generation data entry with sensible defaults."""
    return GenerationData(
        generator=make_generator() if generator is None else generator,
        sample_size=sample_size,
        samples_count=samples_count,
    )


def make_step(
    data_list: list[GenerationData] | None = None,
    experiment_name: str = "gen_exp",
    storage: MagicMock | None = None,
) -> GenerationStep:
    """Build a generation step wired to a mock random values storage."""
    ctx = GenerationStepContext(
        data_list=[] if data_list is None else data_list,
        experiment_name=experiment_name,
    )
    return GenerationStep(ctx, MagicMock() if storage is None else storage)


# Checks that the constructor stores the context and the random values storage.
def test_constructor_stores_context_and_storage() -> None:
    ctx = GenerationStepContext(data_list=[], experiment_name="named")
    storage = MagicMock()

    step = GenerationStep(ctx, storage)

    assert step.ctx is ctx
    assert step.random_values_storage is storage


# Checks that the ctxs property exposes the underlying data list unchanged.
def test_ctxs_returns_data_list() -> None:
    data_list = [make_data(sample_size=5)]
    ctx = GenerationStepContext(data_list=data_list, experiment_name="gen_exp")

    assert GenerationStep(ctx, MagicMock()).ctxs is data_list


# Checks that run generates and persists samples for every positive-count entry.
def test_run_generates_and_saves_samples() -> None:
    generator = make_generator(values=[0.1, 0.2])
    storage = MagicMock()
    step = make_step(data_list=[make_data(generator=generator, sample_size=2, samples_count=3)], storage=storage)

    step.run()

    assert generator.generate.call_count == 3
    generator.generate.assert_called_with(2)
    storage.bulk_insert_data.assert_called_once()
    models = storage.bulk_insert_data.call_args.args[0]
    assert len(models) == 3
    assert all(isinstance(model, RandomValuesModel) for model in models)


# Checks that run skips generation entirely for non-positive sample counts.
@pytest.mark.parametrize("samples_count", [0, -1, -5])
def test_run_skips_non_positive_sample_count(samples_count: int) -> None:
    generator = make_generator()
    storage = MagicMock()
    step = make_step(data_list=[make_data(generator=generator, samples_count=samples_count)], storage=storage)

    step.run()

    generator.generate.assert_not_called()
    storage.bulk_insert_data.assert_not_called()


# Checks that run handles every data entry in the configured order.
@pytest.mark.parametrize("entry_count", [0, 1, 3])
def test_run_processes_every_data_entry(entry_count: int) -> None:
    storage = MagicMock()
    data_list = [make_data(samples_count=1) for _ in range(entry_count)]
    step = make_step(data_list=data_list, storage=storage)

    step.run()

    assert storage.bulk_insert_data.call_count == entry_count


# Checks that only the entries with a positive count are generated.
def test_run_mixes_positive_and_zero_counts() -> None:
    active = make_generator(values=[0.5])
    inactive = make_generator(values=[0.5])
    storage = MagicMock()
    step = make_step(
        data_list=[
            make_data(generator=inactive, samples_count=0),
            make_data(generator=active, samples_count=2),
        ],
        storage=storage,
    )

    step.run()

    inactive.generate.assert_not_called()
    assert active.generate.call_count == 2
    storage.bulk_insert_data.assert_called_once()


# Checks that _generate_samples requests the requested size the requested number of times.
@pytest.mark.parametrize(("size", "count"), [(1, 1), (5, 3), (10, 0)])
def test_generate_samples_calls_generator(size: int, count: int) -> None:
    generator = make_generator(values=[0.0] * size)
    step = make_step()

    samples = step._generate_samples(generator, size, count)

    assert generator.generate.call_count == count
    assert samples == [[0.0] * size for _ in range(count)]


# Checks that _generate_samples materializes generator output into plain lists.
def test_generate_samples_returns_lists() -> None:
    generator = make_generator()
    generator.generate.return_value = (0.1, 0.2)
    step = make_step()

    samples = step._generate_samples(generator, 2, 1)

    assert samples == [[0.1, 0.2]]
    assert all(isinstance(sample, list) for sample in samples)


# Checks that _save_samples_to_storage builds one populated model per sample.
def test_save_samples_to_storage_builds_models() -> None:
    generator = make_generator(code="UNIF", parameters=[1.0, 2.0])
    storage = MagicMock()
    step = make_step(storage=storage)
    data = make_data(generator=generator, sample_size=2)

    step._save_samples_to_storage([[0.1, 0.2], [0.3, 0.4]], "the_experiment", data)

    models = storage.bulk_insert_data.call_args.args[0]
    assert len(models) == 2
    first = models[0]
    assert first.generator_code == "UNIF"
    assert first.generator_parameters == [1.0, 2.0]
    assert first.sample_size == 2
    assert first.experiment_name == "the_experiment"
    assert first.data == [0.1, 0.2]
    assert models[1].data == [0.3, 0.4]


# Checks that _save_samples_to_storage persists an empty batch without samples.
def test_save_samples_to_storage_with_no_samples() -> None:
    storage = MagicMock()
    step = make_step(storage=storage)

    step._save_samples_to_storage([], "the_experiment", make_data())

    storage.bulk_insert_data.assert_called_once_with([])
