"""Tests for generation-only sample production."""

from pathlib import Path

import numpy as np
import pytest
from pysatl_criterion import DistributionType

from pysatl_experiment.experiment_execution.step.generation_only import (
    GenerationOnlyStep,
    GenerationOnlyStepData,
)
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage
from pysatl_experiment.persistence.models.generated_samples import GeneratedSampleModel, GenerationRunModel


PARAMETERS = {
    "mean": {"type": "random_uniform", "low": -5.0, "high": 5.0},
    "var": {"type": "random_uniform", "low": 0.5, "high": 5.0},
}

def _storage_and_run(db_path: Path, count: int = 3, seed: int = 42) -> tuple[GeneratedSamplesStorage, int]:
    storage = GeneratedSamplesStorage(f"sqlite:///{db_path}")
    storage.init()
    run_id = storage.create_run(
        GenerationRunModel(
            name="normal_training_samples",
            distribution="normal",
            sample_sizes=[10],
            samples_count=count,
            parameter_config=PARAMETERS,
            seed=seed,
            config_fingerprint=f"normal-{db_path.name}",
        )
    )
    return storage, run_id


def _step(
    storage: GeneratedSamplesStorage,
    run_id: int,
    count: int = 3,
    seed: int = 42,
    parallel_workers: int = 1,
) -> GenerationOnlyStep:
    return GenerationOnlyStep(
        GenerationOnlyStepData(
            generation_run_id=run_id,
            distribution=DistributionType.NORMAL,
            sample_sizes=[10],
            samples_count=count,
            parameter_config=PARAMETERS,
            seed=seed,
            parallel_workers=parallel_workers,
        ),
        storage,
    )


def test_generation_draws_and_stores_parameters_for_every_sample(tmp_path: Path) -> None:
    storage, run_id = _storage_and_run(tmp_path / "samples.sqlite")

    _step(storage, run_id).run()

    means = []
    for sample_num in range(1, 4):
        sample = storage.get_sample(run_id, sample_size=10, sample_num=sample_num)
        assert sample is not None
        assert len(sample.data) == 10
        assert -5.0 <= sample.parameters["mean"] < 5.0
        assert 0.5 <= sample.parameters["var"] < 5.0
        means.append(sample.parameters["mean"])
    assert len(set(means)) == 3
    assert storage.get_run(run_id).is_complete is False


def test_generation_is_reproducible_for_the_same_seed(tmp_path: Path) -> None:
    first_storage, first_run_id = _storage_and_run(tmp_path / "first.sqlite")
    _step(first_storage, first_run_id).run()
    first = first_storage.get_sample(first_run_id, sample_size=10, sample_num=2)

    second_storage, second_run_id = _storage_and_run(tmp_path / "second.sqlite")
    _step(second_storage, second_run_id).run()
    second = second_storage.get_sample(second_run_id, sample_size=10, sample_num=2)

    assert first is not None
    assert second is not None
    assert second.parameters == first.parameters
    assert second.sample_seed == first.sample_seed
    assert np.array_equal(second.data, first.data)


def test_parallel_generation_matches_sequential_generation(tmp_path: Path) -> None:
    sequential_storage, sequential_run_id = _storage_and_run(
        tmp_path / "sequential.sqlite", count=6
    )
    _step(sequential_storage, sequential_run_id, count=6, parallel_workers=1).run()

    parallel_storage, parallel_run_id = _storage_and_run(
        tmp_path / "parallel.sqlite", count=6
    )
    _step(parallel_storage, parallel_run_id, count=6, parallel_workers=2).run()

    for sample_num in range(1, 7):
        sequential = sequential_storage.get_sample(
            sequential_run_id, sample_size=10, sample_num=sample_num
        )
        parallel = parallel_storage.get_sample(
            parallel_run_id, sample_size=10, sample_num=sample_num
        )
        assert sequential is not None
        assert parallel is not None
        assert parallel.parameters == sequential.parameters
        assert parallel.sample_seed == sequential.sample_seed
        assert np.array_equal(parallel.data, sequential.data)


def test_parameter_draws_do_not_depend_on_json_key_order(tmp_path: Path) -> None:
    first_storage, first_run_id = _storage_and_run(tmp_path / "first-order.sqlite")
    _step(first_storage, first_run_id).run()
    first = first_storage.get_sample(first_run_id, sample_size=10, sample_num=1)

    reversed_parameters = dict(reversed(list(PARAMETERS.items())))
    second_storage = GeneratedSamplesStorage(f"sqlite:///{tmp_path / 'second-order.sqlite'}")
    second_storage.init()
    second_run_id = second_storage.create_run(
        GenerationRunModel(
            name="normal_training_samples",
            distribution="normal",
            sample_sizes=[10],
            samples_count=3,
            parameter_config=reversed_parameters,
            seed=42,
            config_fingerprint="normal-reversed",
        )
    )
    GenerationOnlyStep(
        GenerationOnlyStepData(
            generation_run_id=second_run_id,
            distribution=DistributionType.NORMAL,
            sample_sizes=[10],
            samples_count=3,
            parameter_config=reversed_parameters,
            seed=42,
        ),
        second_storage,
    ).run()
    second = second_storage.get_sample(second_run_id, sample_size=10, sample_num=1)

    assert first is not None
    assert second is not None
    assert second.parameters == first.parameters
    assert np.array_equal(second.data, first.data)


def test_generation_changes_with_root_seed(tmp_path: Path) -> None:
    first_storage, first_run_id = _storage_and_run(tmp_path / "first-seed.sqlite", count=1)
    _step(first_storage, first_run_id, count=1).run()
    first = first_storage.get_sample(first_run_id, sample_size=10, sample_num=1)

    second_storage, second_run_id = _storage_and_run(tmp_path / "second-seed.sqlite", count=1, seed=43)
    _step(second_storage, second_run_id, count=1, seed=43).run()
    second = second_storage.get_sample(second_run_id, sample_size=10, sample_num=1)

    assert first is not None
    assert second is not None
    assert second.parameters != first.parameters
    assert not np.array_equal(second.data, first.data)


def test_generation_resumes_without_replacing_existing_samples(tmp_path: Path) -> None:
    reference_storage, reference_run_id = _storage_and_run(tmp_path / "reference.sqlite")
    _step(reference_storage, reference_run_id).run()
    reference_samples = [
        reference_storage.get_sample(reference_run_id, sample_size=10, sample_num=number) for number in range(1, 4)
    ]

    resumed_storage, resumed_run_id = _storage_and_run(tmp_path / "resumed.sqlite")
    first = reference_samples[0]
    assert first is not None
    resumed_storage.insert_sample(
        GeneratedSampleModel(
            generation_run_id=resumed_run_id,
            sample_size=first.sample_size,
            sample_num=first.sample_num,
            parameters=first.parameters,
            sample_seed=first.sample_seed,
            data=first.data,
        )
    )

    _step(resumed_storage, resumed_run_id).run()

    for number, expected in enumerate(reference_samples, start=1):
        actual = resumed_storage.get_sample(resumed_run_id, sample_size=10, sample_num=number)
        assert expected is not None
        assert actual is not None
        assert actual.parameters == expected.parameters
        assert np.array_equal(actual.data, expected.data)


@pytest.mark.parametrize(
    ("generated", "message"),
    [
        (np.zeros(9), "returned shape"),
        (np.full(10, np.inf), "returned non-finite observations"),
    ],
)
def test_generation_rejects_invalid_generator_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    generated: np.ndarray,
    message: str,
) -> None:
    class InvalidGenerator:
        def generate(self, size: int, random_state: np.random.Generator) -> np.ndarray:
            return generated

    monkeypatch.setattr(
        "pysatl_experiment.experiment_execution.step.generation_only.get_available_generator",
        lambda distribution, parameters: InvalidGenerator(),
    )
    storage, run_id = _storage_and_run(tmp_path / "invalid.sqlite", count=1)

    with pytest.raises(ValueError, match=message):
        _step(storage, run_id, count=1).run()

    assert storage.get_existing_sample_numbers(run_id, sample_size=10) == set()


@pytest.mark.parametrize(
    ("distribution", "parameters"),
    [
        (DistributionType.NORMAL, {"mean": 0.0, "var": 1.0}),
        (DistributionType.EXPONENTIAL, {"lam": 1.0}),
        (DistributionType.WEIBULL, {"a": 1.0, "k": 2.0}),
        (DistributionType.GAMMA, {"alfa": 2.0, "beta": 1.0}),
        (DistributionType.BETA, {"a": 2.0, "b": 3.0}),
        (DistributionType.LOG_NORMAL, {"s": 0.5, "mu": 0.0}),
        (DistributionType.STUDENT, {"df": 5.0}),
        (DistributionType.UNIFORM, {"a": -1.0, "b": 2.0}),
        (DistributionType.CAUCHY, {"t": 0.0, "s": 1.0}),
    ],
)
def test_generation_supports_selected_distributions(
    tmp_path: Path,
    distribution: DistributionType,
    parameters: dict[str, float],
) -> None:
    parameter_config = {
        name: {"type": "fixed", "value": value} for name, value in parameters.items()
    }
    storage = GeneratedSamplesStorage(f"sqlite:///{tmp_path / f'{distribution.value}.sqlite'}")
    storage.init()
    run_id = storage.create_run(
        GenerationRunModel(
            name=f"{distribution.value}_training_samples",
            distribution=distribution.value,
            sample_sizes=[10],
            samples_count=1,
            parameter_config=parameter_config,
            seed=42,
            config_fingerprint=distribution.value,
        )
    )

    GenerationOnlyStep(
        GenerationOnlyStepData(
            generation_run_id=run_id,
            distribution=distribution,
            sample_sizes=[10],
            samples_count=1,
            parameter_config=parameter_config,
            seed=42,
        ),
        storage,
    ).run()

    sample = storage.get_sample(run_id, sample_size=10, sample_num=1)
    assert sample is not None
    assert sample.parameters == parameters
    assert len(sample.data) == 10
    assert np.isfinite(sample.data).all()
