from dataclasses import dataclass

from stattest.experiment.generator import AbstractRVSGenerator
from stattest.persistence.model.random_values.random_values import IRandomValuesStorage


@dataclass
class GenerationStepData:
    """
    Data for generation step.
    """

    generator: AbstractRVSGenerator
    sample_size: int
    count: int


class GenerationStep:
    """
    Standard experiment generation step.
    """

    def __init__(
        self,
        step_config: list[GenerationStepData],
        monte_carlo_count: int,
        data_storage: IRandomValuesStorage,
    ):
        self.step_config = step_config
        self.monte_carlo_count = monte_carlo_count
        self.data_storage = data_storage

    def run(self) -> None:
        """
        Run standard generation step.
        """
        pass
