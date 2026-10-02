"""Tests for random sample generation step."""

import os
from collections.abc import Iterable

from pysatl_criterion import DistributionType
from pysatl_criterion.utils.generator import get_available_generator

from pysatl_experiment.experiment_execution.step.generation_step.generation_step import GenerationStep
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.models.random_values import RandomValuesBatch, RandomValuesFilter, RandomValuesModel


class CollectingRandomValuesStorage(IRandomValuesStorage):
    """In-memory storage test double collecting inserted random values."""

    def __init__(self) -> None:
        self.models: list[RandomValuesModel] = []

    def init(self) -> None:
        pass

    def bulk_insert(self, samples: Iterable[RandomValuesModel], *, batch_size: int = 1000) -> None:
        self.models.extend(samples)

    def count(self, query: RandomValuesFilter) -> int:
        raise NotImplementedError

    def delete(self, query: RandomValuesFilter) -> int:
        raise NotImplementedError

    def read_bulk(
        self, query: RandomValuesFilter, *, after_id: int | None = None, batch_size: int = 1000
    ) -> RandomValuesBatch:
        raise NotImplementedError


class ConfiguredGenerator:
    """Picklable test double kept outside the library's subclass registry."""

    def __init__(self, preset: str) -> None:
        self.preset = preset
        self.value = 0.0
        self.parent_pid = os.getpid()

    def code(self) -> str:
        return self.preset

    def parameters(self) -> dict[str, float]:
        return {"value": self.value}

    def generate(self, size: int) -> list[float]:
        assert os.getpid() != self.parent_pid
        return [self.value] * size


def test_generation_step_generates_samples_in_parallel() -> None:
    generator = get_available_generator(DistributionType.NORMAL, {"mean": 0, "var": 1})
    storage = CollectingRandomValuesStorage()
    step = GenerationStep(
        ctx=GenerationStepContext(
            data_list=[
                GenerationData(
                    generator=generator,
                    sample_size=3,
                    samples_count=7,
                    generator_code="normal_mean_0.0_var_1.0",
                )
            ],
            experiment_name="parallel_generation",
            parallel_workers=2,
        ),
        random_values_storage=storage,
    )

    step.run()

    assert len(storage.models) == 7
    assert {model.generator_code for model in storage.models} == {"normal_mean_0.0_var_1.0"}
    assert {model.experiment_name for model in storage.models} == {"parallel_generation"}
    assert {model.sample_size for model in storage.models} == {3}
    assert all(len(model.data) == 3 for model in storage.models)


def test_generation_transfers_configured_instance_to_worker_processes() -> None:
    generator = ConfiguredGenerator("configured-preset")
    generator.value = 7.5
    storage = CollectingRandomValuesStorage()
    step = GenerationStep(
        ctx=GenerationStepContext(
            data_list=[
                GenerationData(
                    generator=generator, sample_size=3, samples_count=9, generator_code="configured-preset"
                )
            ],
            experiment_name="configured_generation",
            parallel_workers=2,
        ),
        random_values_storage=storage,
    )

    step.run()

    assert len(storage.models) == 9
    assert all(
        model == RandomValuesModel("configured_generation", "configured-preset", {"value": 7.5}, 3, [7.5] * 3)
        for model in storage.models
    )
