"""Persistence preparation performed only after configuration validation."""

from pysatl_experiment.configuration import ExperimentConfig, PowerExperimentConfig
from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.experiment_storages import ExperimentStorages
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.persistence.models.experiment import ExperimentModel, ExperimentQuery
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter
from pysatl_experiment.types import RunMode


def experiment_query(config: ExperimentConfig) -> ExperimentQuery:
    """Identify an experiment by its name."""
    return ExperimentQuery(experiment_name=config.experiment_name)


def experiment_model(config: ExperimentConfig) -> ExperimentModel:
    """Map configuration to a fresh experiment record."""
    sizes = config.execute.sample_sizes if isinstance(config, PowerExperimentConfig) else config.generate.sample_sizes
    return ExperimentModel(
        experiment_name=config.experiment_name,
        is_generation_done=False,
        is_execution_done=False,
        is_report_building_done=False,
        experiment_type=config.experiment_type,
        storage_connection=config.storage_connection,
        run_mode=config.run_mode.value,
        report_mode=config.report.report_mode.value,
        hypothesis=config.execute.hypothesis,
        generator_type=config.generate.generator_type.value,
        executor_type=config.execute.executor_type.value,
        report_builder_type=config.report.report_builder_type.value,
        sample_sizes=sizes,
        monte_carlo_count=config.execute.monte_carlo_count,
        criteria={item.criterion_code: item.parameters for item in config.execute.criteria},
        alternatives={code: parameters for code, parameters, _ in ExperimentConfigAdapter(config).generator_metadata()},
        significance_levels=config.execute.significance_levels,
        parallel_workers=config.execute.parallel_workers,
    )


def prepare_experiment(config: ExperimentConfig, storages: ExperimentStorages) -> ExperimentRunState:
    """Restore progress and apply run mode before any tasks are planned."""
    storage = storages.experiment
    config.report.results_path.mkdir(parents=True, exist_ok=True)
    query = experiment_query(config)
    existing = storage.get_data(query)
    overwrite = config.run_mode == RunMode.OVERWRITE
    if existing is None or overwrite:
        storage.insert_data(experiment_model(config))
    if overwrite:
        adapter = ExperimentConfigAdapter(config)
        for generator_code, _, _ in adapter.generator_metadata():
            for size in adapter.sample_sizes:
                storages.data.delete(
                    RandomValuesFilter(
                        generator_code=generator_code,
                        sample_size=size,
                        experiment_name=config.experiment_name,
                    )
                )
        for result_query in adapter.result_queries():
            storages.result.delete_data(result_query)
    return ExperimentRunState(
        experiment_name=config.experiment_name,
        generation_done=bool(existing and existing.is_generation_done and not overwrite),
        execution_done=bool(existing and existing.is_execution_done and not overwrite),
    )
