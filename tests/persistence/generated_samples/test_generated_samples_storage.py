"""Tests for generated training sample persistence."""

from pathlib import Path

import numpy as np
import pytest
from sqlalchemy.exc import IntegrityError

from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage
from pysatl_experiment.persistence.generation_run_status_storage import GenerationRunStatusStorage
from pysatl_experiment.persistence.models.generated_samples import GeneratedSampleModel, GenerationRunModel


@pytest.fixture
def storage(tmp_path: Path) -> GeneratedSamplesStorage:
    result = GeneratedSamplesStorage(f"sqlite:///{tmp_path / 'generated.sqlite'}")
    result.init()
    return result


def _run() -> GenerationRunModel:
    return GenerationRunModel(
        name="normal_training_samples",
        distribution="normal",
        sample_sizes=[100],
        samples_count=2,
        parameter_config={
            "mean": {"type": "random_uniform", "low": -5.0, "high": 5.0},
            "var": {"type": "fixed", "value": 1.0},
        },
        seed=42,
        config_fingerprint="normal-config-fingerprint",
    )


def test_create_run_round_trips_generation_configuration(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())

    stored = storage.get_run(run_id)

    assert stored is not None
    assert stored.id == run_id
    assert stored.distribution == "normal"
    assert stored.parameter_config["mean"]["low"] == -5.0
    assert stored.is_complete is False


def test_create_run_reuses_existing_fingerprint(storage: GeneratedSamplesStorage) -> None:
    first_id = storage.create_run(_run())
    second_id = storage.create_run(_run())

    assert second_id == first_id


def test_insert_sample_round_trips_realized_parameters_and_data(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())
    sample = GeneratedSampleModel(
        generation_run_id=run_id,
        sample_size=3,
        sample_num=1,
        parameters={"mean": 1.25, "var": 1.0},
        sample_seed=123,
        data=[0.5, 1.0, 1.5],
    )

    storage.insert_sample(sample)
    stored = storage.get_sample(run_id, sample_size=3, sample_num=1)

    assert stored is not None
    assert stored.parameters == sample.parameters
    assert stored.sample_seed == 123
    assert np.allclose(stored.data, sample.data)
    assert storage.get_existing_sample_numbers(run_id, sample_size=3) == {1}


def test_insert_samples_persists_a_batch(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())
    samples = [
        GeneratedSampleModel(
            generation_run_id=run_id,
            sample_size=3,
            sample_num=sample_num,
            parameters={"mean": float(sample_num), "var": 1.0},
            sample_seed=sample_num,
            data=[float(sample_num)] * 3,
        )
        for sample_num in (1, 2)
    ]

    storage.insert_samples(samples)

    assert storage.get_existing_sample_numbers(run_id, sample_size=3) == {1, 2}


def test_insert_sample_does_not_overwrite_duplicate_number(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())
    original = GeneratedSampleModel(
        generation_run_id=run_id,
        sample_size=3,
        sample_num=1,
        parameters={"mean": 0.0, "var": 1.0},
        sample_seed=123,
        data=[1.0, 2.0, 3.0],
    )
    storage.insert_sample(original)

    with pytest.raises(IntegrityError):
        storage.insert_sample(
            GeneratedSampleModel(
                generation_run_id=run_id,
                sample_size=3,
                sample_num=1,
                parameters={"mean": 4.0, "var": 1.0},
                sample_seed=456,
                data=[4.0, 5.0, 6.0],
            )
        )

    stored = storage.get_sample(run_id, sample_size=3, sample_num=1)
    assert stored is not None
    assert stored.data == original.data


def test_mark_run_complete_updates_only_run_state(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())

    storage.mark_run_complete(run_id)

    stored = storage.get_run(run_id)
    assert stored is not None
    assert stored.is_complete is True


def test_generation_run_status_storage_marks_only_generation_step(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())
    status_storage = GenerationRunStatusStorage(storage)

    status_storage.set_generation_done(run_id)

    stored = storage.get_run(run_id)
    assert stored is not None
    assert stored.is_complete is True
    with pytest.raises(RuntimeError, match="do not have an execution step"):
        status_storage.set_execution_done(run_id)


def test_delete_run_removes_only_its_generated_samples(storage: GeneratedSamplesStorage) -> None:
    run_id = storage.create_run(_run())
    other_run = _run()
    other_run.config_fingerprint = "other-config-fingerprint"
    other_run_id = storage.create_run(other_run)
    storage.insert_sample(
        GeneratedSampleModel(
            generation_run_id=run_id,
            sample_size=3,
            sample_num=1,
            parameters={"mean": 0.0, "var": 1.0},
            sample_seed=123,
            data=[1.0, 2.0, 3.0],
        )
    )
    storage.insert_sample(
        GeneratedSampleModel(
            generation_run_id=other_run_id,
            sample_size=3,
            sample_num=1,
            parameters={"mean": 2.0, "var": 1.0},
            sample_seed=456,
            data=[4.0, 5.0, 6.0],
        )
    )

    stored_run = storage.get_run_by_fingerprint("normal-config-fingerprint")
    assert stored_run is not None
    assert stored_run.id == run_id

    storage.delete_run(run_id)

    assert storage.get_run(run_id) is None
    assert storage.get_sample(run_id, sample_size=3, sample_num=1) is None
    assert storage.get_run_by_fingerprint("normal-config-fingerprint") is None
    assert storage.get_run(other_run_id) is not None
    assert storage.get_sample(other_run_id, sample_size=3, sample_num=1) is not None
