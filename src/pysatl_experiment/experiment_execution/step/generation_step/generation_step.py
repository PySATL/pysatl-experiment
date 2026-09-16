"""Random sample generation step implementation."""

import importlib
import math
from dataclasses import dataclass
from typing import Any

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
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage, RandomValuesModel


@dataclass
class GenerationTaskSpec:
    """
    Serializable task specification for random sample generation.

    Attributes
    ----------
    generator_class_name : str
        Generator class name.
    generator_module : str
        Module containing generator implementation.
    generator_code : str
        Generator code used by random values storage.
    generator_parameters : dict[str, Any]
        Generator parameters used by random values storage and worker initialization.
    sample_size : int
        Size of generated samples.
    samples_count : int
        Number of samples to generate in this task.
    experiment_name : str
        Experiment name used to scope generated samples.
    """

    generator_class_name: str
    generator_module: str
    generator_code: str
    generator_parameters: dict[str, Any]
    sample_size: int
    samples_count: int
    experiment_name: str


GenerationResult = list[RandomValuesModel]


class GenerationStep(
    MultithreadingGenerationStep[
        GenerationData,
        GenerationTaskSpec,
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
        )
        self.ctx = ctx
        self.random_values_storage = random_values_storage

    @override
    def _collect_tasks(self) -> list[GenerationTaskSpec]:
        task_specs = []
        for data in self.step_config:
            for samples_count in self._split_samples_count(data.samples_count):
                task_specs.append(self._to_task_spec(data, samples_count))

        return task_specs

    @property
    def ctxs(self) -> list[GenerationData]:
        """Return generation tasks."""
        return self.ctx.data_list

    @staticmethod
    @override
    def _execute_task(spec: GenerationTaskSpec) -> GenerationResult:
        generator = GenerationStep._load_generator(spec)
        samples = GenerationStep._generate_samples(generator, spec.sample_size, spec.samples_count)
        return [
            RandomValuesModel(
                generator_code=spec.generator_code,
                generator_parameters=spec.generator_parameters,
                sample_size=spec.sample_size,
                experiment_name=spec.experiment_name,
                data=sample,
            )
            for sample in samples
        ]

    @override
    def _to_models(self, result: GenerationResult) -> list[RandomValuesModel]:
        return result

    @override
    def _bulk_save(self, models: list[RandomValuesModel]) -> None:
        self.random_values_storage.bulk_insert_data(models)

    def _split_samples_count(self, samples_count: int) -> list[int]:
        if samples_count <= 0:
            return []

        target_tasks_count = max(1, self.parallel_workers * 4)
        chunk_size = max(1, math.ceil(samples_count / target_tasks_count))
        chunks = []
        remaining_samples = samples_count
        while remaining_samples > 0:
            current_chunk_size = min(chunk_size, remaining_samples)
            chunks.append(current_chunk_size)
            remaining_samples -= current_chunk_size

        return chunks

    def _to_task_spec(self, data: GenerationData, samples_count: int) -> GenerationTaskSpec:
        generator = data.generator
        return GenerationTaskSpec(
            generator_class_name=generator.__class__.__name__,
            generator_module=generator.__class__.__module__,
            generator_code=generator.code(),
            generator_parameters=generator.parameters(),
            sample_size=data.sample_size,
            samples_count=samples_count,
            experiment_name=self.ctx.experiment_name,
        )

    @staticmethod
    def _load_generator(spec: GenerationTaskSpec) -> AbstractRVSGenerator:
        generator_module = importlib.import_module(spec.generator_module)
        generator_class = getattr(generator_module, spec.generator_class_name)
        return generator_class(**spec.generator_parameters)

    @staticmethod
    @profile
    def _generate_samples(generator: AbstractRVSGenerator, size: int, count: int) -> list[list[float]]:
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
        list[list[float]]
            Generated samples.
        """
        samples = []
        for _ in range(count):
            sample = list(generator.generate(size))
            samples.append(sample)

        return samples

    def _save_samples_to_storage(self, samples: list[list[float]], experiment_name: str, data: GenerationData) -> None:
        """
        Save generated samples to storage.

        Parameters
        ----------
        samples : list[list[float]]
            Generated samples.
        experiment_name : str
            Sample size.
        data : GenerationStepContext
            Generation task configuration.
        """
        data_to_save = [
            RandomValuesModel(
                generator_code=data.generator.code(),
                generator_parameters=data.generator.parameters(),
                sample_size=len(sample),
                experiment_name=experiment_name,
                data=sample,
            )
            for sample in samples
        ]

        self.random_values_storage.bulk_insert_data(data_to_save)
