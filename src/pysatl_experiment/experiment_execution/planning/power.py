"""Plan missing power tasks without changing persisted data."""

from pysatl_experiment.configuration import ExperimentConfig
from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.experiment_storages import ExperimentStorages
from pysatl_experiment.experiment_execution.planning.generation import plan_generation
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.execution_step.power.task_spec import PowerTask
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import GenerationData
from pysatl_experiment.persistence.models.power import PowerQuery
from pysatl_experiment.types import SampleSetSpec


def plan_power_tasks(
    experiment_config: ExperimentConfig, storages: ExperimentStorages, state: ExperimentRunState
) -> ExperimentTaskPlan[GenerationData, PowerTask]:
    """Plan unfinished power work using saved results."""
    generation = None if state.generation_done else plan_generation(experiment_config, storages.data)
    if state.execution_done:
        return ExperimentTaskPlan(generation=generation, execution=None)
    adapter = ExperimentConfigAdapter(experiment_config)
    config = experiment_config.execute
    monte_carlo_count = config.monte_carlo_count
    result_storage = storages.result
    criteria_config = adapter.criterion_specs()

    step_config: list[PowerTask] = []
    for criterion_config in criteria_config:
        for sample_size in adapter.sample_sizes:
            for alternative in adapter.alternatives:
                for significance_level in config.significance_levels:
                    query = PowerQuery(
                        experiment_name=experiment_config.experiment_name,
                        criterion_code=criterion_config.code,
                        criterion_parameters=criterion_config.parameters,
                        sample_size=sample_size,
                        monte_carlo_count=monte_carlo_count,
                        alternative_code=alternative.distribution_type,
                        alternative_parameters=alternative.parameters,
                        significance_level=significance_level,
                    )
                    result = result_storage.get_data(query)
                    if result is None:
                        step_config.append(
                            PowerTask(
                                criterion=criterion_config,
                                sample_set=SampleSetSpec(
                                    experiment_name=experiment_config.experiment_name,
                                    generator_code=alternative.distribution_type,
                                    sample_size=sample_size,
                                    samples_count=monte_carlo_count,
                                ),
                                alternative_parameters=alternative.parameters,
                                significance_level=significance_level,
                            )
                        )

    return ExperimentTaskPlan(generation=generation, execution=step_config)
