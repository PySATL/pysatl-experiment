"""Plan missing time complexity tasks without changing persisted data."""

from pysatl_experiment.configuration import ExperimentConfig
from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.experiment_storages import ExperimentStorages
from pysatl_experiment.experiment_execution.planning.generation import plan_generation
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.task_spec import TimeComplexityTask
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import GenerationData
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityQuery
from pysatl_experiment.types import SampleSetSpec


def plan_time_complexity_tasks(
    experiment_config: ExperimentConfig, storages: ExperimentStorages, state: ExperimentRunState
) -> ExperimentTaskPlan[GenerationData, TimeComplexityTask]:
    """Plan unfinished time complexity work using saved results."""
    generation = None if state.generation_done else plan_generation(experiment_config, storages.data)
    if state.execution_done:
        return ExperimentTaskPlan(generation=generation, execution=None)
    adapter = ExperimentConfigAdapter(experiment_config)
    config = experiment_config.execute
    monte_carlo_count = config.monte_carlo_count
    result_storage = storages.result
    criteria_config = adapter.criterion_specs()
    step_config: list[TimeComplexityTask] = []
    for generator_code, _, _ in adapter.generator_metadata():
        for criterion_config in criteria_config:
            for sample_size in adapter.sample_sizes:
                query = TimeComplexityQuery(
                    experiment_name=experiment_config.experiment_name,
                    generator_code=generator_code,
                    criterion_code=criterion_config.code,
                    criterion_parameters=criterion_config.parameters,
                    sample_size=sample_size,
                    samples_count=monte_carlo_count,
                )
                result = result_storage.get_data(query)
                if result is None:
                    step_data = TimeComplexityTask(
                        criterion=criterion_config,
                        sample_set=SampleSetSpec(
                            experiment_name=experiment_config.experiment_name,
                            generator_code=generator_code,
                            sample_size=sample_size,
                            samples_count=monte_carlo_count,
                        ),
                    )
                    step_config.append(step_data)

    return ExperimentTaskPlan(generation=generation, execution=step_config)
