"""Shared assembly for experiments using standard random sample generation."""

from abc import ABC

from pysatl_experiment.experiment_execution.experiment_factory.abstract_experiment_factory import (
    RS,
    AbstractExperimentFactory,
    D,
    E,
    ExecutionTaskT,
    R,
)
from pysatl_experiment.experiment_execution.step.generation_step.generation_step import GenerationStep
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage


class StandardGenerationExperimentFactory(
    AbstractExperimentFactory[D, GenerationStep, E, R, RS, GenerationData, ExecutionTaskT], ABC
):
    """Specialize generation tasks and their step for the built-in experiments."""

    def _create_generation_step(
        self, data_storage: IRandomValuesStorage, tasks: list[GenerationData]
    ) -> GenerationStep:
        return GenerationStep(
            ctx=GenerationStepContext(
                data_list=tasks,
                experiment_name=self.config.experiment_name,
                parallel_workers=self.config.generate.parallel_workers,
            ),
            random_values_storage=data_storage,
        )
