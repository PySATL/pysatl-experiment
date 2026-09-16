"""Tests for random sample generation step."""

from collections.abc import Iterable

from pysatl_criterion import DistributionType
from pysatl_criterion.utils.generator import get_available_generator

from pysatl_experiment.experiment_execution.step.generation_step.generation_step import GenerationStep
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)
from pysatl_experiment.persistence.models.random_values import (
    IRandomValuesStorage,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)


class CollectingRandomValuesStorage(IRandomValuesStorage):
    """In-memory storage test double collecting inserted random values."""

    def __init__(self) -> None:
        self.models: list[RandomValuesModel] = []

    def init(self) -> None:
        pass

    def get_data(self, query: RandomValuesQuery) -> RandomValuesModel | None:
        return None

    def insert_data(self, data: RandomValuesModel) -> None:
        self.models.append(data)

    def delete_data(self, query: RandomValuesQuery) -> None:
        pass

    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        return 0

    def bulk_insert_data(self, data_list: Iterable[RandomValuesModel]) -> None:
        self.models.extend(data_list)

    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel] | None:
        return None

    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        pass

    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel] | None:
        return None


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
                )
            ],
            experiment_name="parallel_generation",
            parallel_workers=2,
        ),
        random_values_storage=storage,
    )

    step.run()

    assert len(storage.models) == 7
    assert {model.generator_code for model in storage.models} == {generator.code()}
    assert {model.experiment_name for model in storage.models} == {"parallel_generation"}
    assert {model.sample_size for model in storage.models} == {3}
    assert all(len(model.data) == 3 for model in storage.models)
