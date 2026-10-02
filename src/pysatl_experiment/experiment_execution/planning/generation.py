"""Plan missing generation tasks without changing persisted data."""

import random

from pysatl_criterion.utils.generator import get_available_generator

from pysatl_experiment.configuration import ExperimentConfig, PowerExperimentConfig
from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import GenerationData
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter


def plan_generation(config: ExperimentConfig, data_storage: IRandomValuesStorage) -> list[GenerationData]:
    """Schedule only the samples missing from storage."""
    adapter = ExperimentConfigAdapter(config)
    count = (
        config.execute.monte_carlo_count if isinstance(config, PowerExperimentConfig) else config.generate.samples_count
    )
    tasks = []
    for generator_code, parameter_spec, generator in adapter.generator_metadata():
        for size in adapter.sample_sizes:
            query = RandomValuesFilter(
                generator_code=generator_code,
                sample_size=size,
                experiment_name=config.experiment_name,
            )
            missing = max(0, count - data_storage.count(query))
            has_ranges = any(isinstance(value, list) for value in parameter_spec.values())
            if has_ranges:
                for _ in range(missing):
                    parameters = {
                        name: (random.uniform(*value) if isinstance(value, list) else value)  # noqa: S311
                        for name, value in parameter_spec.items()
                    }
                    tasks.append(
                        GenerationData(
                            generator=get_available_generator(
                                generator.distribution_type(), parameters
                            ),
                            sample_size=size,
                            samples_count=1,
                            generator_code=generator_code,
                        )
                    )
            elif missing:
                tasks.append(
                    GenerationData(
                        generator=generator, sample_size=size, samples_count=missing, generator_code=generator_code
                    )
                )
    return tasks
