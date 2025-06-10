from dataclasses import dataclass

from stattest.experiment.generator import AbstractRVSGenerator
from stattest.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesModel,
)


@dataclass
class GenerationStepData:
    """
    Data for generation step.
    """

    generator: AbstractRVSGenerator
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    count: int


class GenerationStep:
    """
    Standard experiment generation step.
    """

    def __init__(
        self,
        step_config: list[GenerationStepData],
        data_storage: IRandomValuesStorage,
    ):
        self.step_config = step_config
        self.data_storage = data_storage

    def run(self) -> None:
        """
        Run standard generation step.
        """

        for step_data in self.step_config:
            samples = self._generate_samples(step_data)
            self._save_samples_to_storage(samples, step_data.sample_size, step_data)

    def _generate_samples(self, step_data: GenerationStepData) -> list[list[float]]:
        """
        Generate samples.

        :param step_data: generation step data.

        :return: samples.
        """

        samples = []
        for i in range(step_data.count):
            sample = step_data.generator.generate(step_data.sample_size)
            samples.append(sample)

        return samples

    def _save_samples_to_storage(
        self, samples: list[list[float]], sample_size: int, step_data: GenerationStepData
    ) -> None:
        """
        Save data to storage.

        :param samples: data to save.
        :param sample_size: sample size.
        :param step_data: step data.
        """

        for i in range(1, len(samples) + 1):
            sample = samples[i]
            generator_name = step_data.generator_name
            generator_parameters = step_data.generator_parameters
            data_to_save = RandomValuesModel(
                generator_name=generator_name,
                generator_parameters=generator_parameters,
                sample_size=sample_size,
                sample_num=i,
                data=sample,
            )
            self.data_storage.insert_data(data_to_save)
