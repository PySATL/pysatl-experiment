"""Random sample generation step implementation."""

from dataclasses import dataclass

from line_profiler import profile
from typing_extensions import override

from pysatl_experiment.experiment.generator import AbstractRVSGenerator
from pysatl_experiment.experiment.model.experiment_step import IExperimentStep
from pysatl_experiment.persistence.model.random_values import IRandomValuesStorage, RandomValuesModel


@dataclass
class GenerationStepData:
    """
    Configuration for random sample generation.

    Attributes
    ----------
    generator : AbstractRVSGenerator
        Generator instance.
    generator_name : str
        Generator identifier.
    generator_parameters : list[float]
        Generator parameters.
    sample_size : int
        Size of generated samples.
    count : int
        Number of samples to generate.
    """

    generator: AbstractRVSGenerator
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    count: int


class GenerationStep(IExperimentStep):
    """Generate random samples and store them in persistent storage."""

    def __init__(
        self,
        step_config: list[GenerationStepData],
        data_storage: IRandomValuesStorage,
    ) -> None:
        """
        Initialize generation step.

        Parameters
        ----------
        step_config : list[GenerationStepData]
            Sample generation configurations.
        data_storage : IRandomValuesStorage
            Storage for generated samples.
        """
        self.step_config = step_config
        self.data_storage = data_storage

    @profile
    @override
    def run(self) -> None:
        """Execute sample generation step."""
        for step_data in self.step_config:
            samples = self._generate_samples(step_data)
            self._save_samples_to_storage(samples, step_data.sample_size, step_data)

    @profile
    def _generate_samples(self, step_data: GenerationStepData) -> list[list[float]]:
        """
        Generate random samples.

        Parameters
        ----------
        step_data : GenerationStepData
            Generation task configuration.

        Returns
        -------
        list[list[float]]
            Generated samples.
        """
        samples = []
        for i in range(step_data.count):
            sample = list(step_data.generator.generate(step_data.sample_size))
            samples.append(sample)

        return samples

    def _save_samples_to_storage(
        self, samples: list[list[float]], sample_size: int, step_data: GenerationStepData
    ) -> None:
        """
        Save generated samples to storage.

        Parameters
        ----------
        samples : list[list[float]]
            Generated samples.
        sample_size : int
            Sample size.
        step_data : GenerationStepData
            Generation task configuration.
        """
        for i in range(len(samples)):
            sample = samples[i]
            generator_name = step_data.generator_name
            generator_parameters = step_data.generator_parameters
            sample_num = i + 1
            data_to_save = RandomValuesModel(
                generator_name=generator_name,
                generator_parameters=generator_parameters,
                sample_size=sample_size,
                sample_num=sample_num,
                data=sample,
            )
            self.data_storage.insert_data(data_to_save)
