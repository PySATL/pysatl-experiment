"""Random sample generation step implementation."""

from line_profiler import profile
from pysatl_criterion.generator.model import AbstractRVSGenerator
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage, RandomValuesModel


class GenerationStep(IExperimentStep):
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
        self.ctx = ctx
        self.random_values_storage = random_values_storage

    @profile
    @override
    def run(self) -> None:
        """Execute sample generation step."""
        for data in self.ctx.data_list:
            if data.samples_count > 0:
                samples = self._generate_samples(data.generator, data.sample_size, data.samples_count)
                self._save_samples_to_storage(samples, self.ctx.experiment_name, data)

    @property
    def ctxs(self) -> list[GenerationData]:
        """Return generation tasks."""
        return self.ctx.data_list

    @profile
    def _generate_samples(self, generator: AbstractRVSGenerator, size: int, count: int) -> list[list[float]]:
        """
        Generate random samples.

        Parameters
        ----------
        data : GenerationData
            Generation task configuration.

        Returns
        -------
        list[list[float]]
            Generated samples.
        """
        samples = []
        for i in range(count):
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
