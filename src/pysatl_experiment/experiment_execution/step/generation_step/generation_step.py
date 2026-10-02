"""Random sample generation step implementation."""

from collections.abc import Iterator
from dataclasses import dataclass

from line_profiler import profile
from pysatl_criterion.generator.model import AbstractRVSGenerator
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)
from pysatl_experiment.experiment_execution.step.generation_step.multithreading_generation_step import (
    MultithreadingGenerationStep,
)
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.models.random_values import RandomValuesModel
from pysatl_experiment.types import Sample


@dataclass
class GenerationTaskSpec:
    """
    Task specification carrying a configured, picklable generator instance.

    Process execution transfers the generator's state with each task.

    Attributes
    ----------
    generator : AbstractRVSGenerator
        Configured generator used to produce this task's samples.
    sample_size : int
        Size of generated samples.
    samples_count : int
        Number of samples to generate in this task.
    experiment_name : str
        Experiment name used to scope generated samples.
    generator_code : str
        Stable sample-series code shared by all realizations of its parameters.
    """

    generator: AbstractRVSGenerator
    sample_size: int
    samples_count: int
    experiment_name: str
    generator_code: str


GenerationResult = list[RandomValuesModel]


@dataclass(frozen=True)
class GenerationBatch:
    """Requests executed together with a bounded total number of samples."""

    specs: tuple[GenerationTaskSpec, ...]


class GenerationStep(
    MultithreadingGenerationStep[
        GenerationData,
        GenerationBatch,
        GenerationResult,
        RandomValuesModel,
        IRandomValuesStorage,
    ]
):
    """Generate random samples and store them in persistent storage."""

    def __init__(
        self,
        ctx: GenerationStepContext,
        random_values_storage: IRandomValuesStorage,
    ) -> None:
        """
        Initialize generation step.

        Parameters
        ----------
        ctx : GenerationStepContext
            Sample generation configurations.
        random_values_storage : IRandomValuesStorage
            Storage for generated samples.
        """
        super().__init__(
            step_config=ctx.data_list,
            result_storage=random_values_storage,
            parallel_workers=ctx.parallel_workers,
            total_samples=sum(data.samples_count for data in ctx.data_list),
            write_batch_size=ctx.write_batch_size,
        )
        self.ctx = ctx
        self.random_values_storage = random_values_storage
        self.samples_per_task = ctx.samples_per_task

    @override
    def _collect_tasks(self) -> Iterator[GenerationBatch]:
        """Split large requests and pack small ones across generators and sizes."""
        specs = []
        samples_count = 0
        for data in self.step_config:
            remaining = data.samples_count
            while remaining > 0:
                count = min(remaining, self.samples_per_task - samples_count)
                specs.append(self._to_task_spec(data, count))
                samples_count += count
                remaining -= count
                if samples_count == self.samples_per_task:
                    yield GenerationBatch(tuple(specs))
                    specs = []
                    samples_count = 0
        if specs:
            yield GenerationBatch(tuple(specs))

    @property
    def ctxs(self) -> list[GenerationData]:
        """Return generation tasks."""
        return self.ctx.data_list

    @staticmethod
    @override
    def _execute_task(batch: GenerationBatch, context: None) -> GenerationResult:
        models = []
        for spec in batch.specs:
            generator_parameters = spec.generator.parameters().copy()
            samples = GenerationStep._generate_samples(spec.generator, spec.sample_size, spec.samples_count)
            models.extend(
                RandomValuesModel(
                    generator_code=spec.generator_code,
                    generator_parameters=generator_parameters,
                    sample_size=spec.sample_size,
                    experiment_name=spec.experiment_name,
                    data=sample.values,
                )
                for sample in samples
            )
        return models

    @override
    def _to_models(self, result: GenerationResult) -> list[RandomValuesModel]:
        return result

    @override
    def _bulk_save(self, models: list[RandomValuesModel]) -> None:
        self.random_values_storage.bulk_insert(models, batch_size=self.write_batch_size)

    def _to_task_spec(self, data: GenerationData, samples_count: int) -> GenerationTaskSpec:
        return GenerationTaskSpec(
            generator=data.generator,
            sample_size=data.sample_size,
            samples_count=samples_count,
            experiment_name=self.ctx.experiment_name,
            generator_code=data.generator_code,
        )

    @staticmethod
    @profile
    def _generate_samples(generator: AbstractRVSGenerator, size: int, count: int) -> list[Sample]:
        """
        Generate random samples.

        Parameters
        ----------
        generator : AbstractRVSGenerator
            Generator instance.
        size : int
            Size of generated samples.
        count : int
            Number of samples to generate.

        Returns
        -------
        list[Sample]
            Generated samples.
        """
        return [Sample(values=list(generator.generate(size))) for _ in range(count)]
