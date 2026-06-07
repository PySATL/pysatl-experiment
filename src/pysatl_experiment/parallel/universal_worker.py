"""Universal parallel task execution utilities."""

import importlib

from src.pysatl_experiment.configuration.model.experiment_type import ExperimentType
from src.pysatl_experiment.experiment.step.execution.common.utils import get_sample_data_from_storage
from src.pysatl_experiment.parallel.task_spec import TaskSpec
from src.pysatl_experiment.persistence.random_values_storage import AlchemyRandomValuesStorage
from src.pysatl_experiment.worker.critical_value import CriticalValueWorker, CriticalValueWorkerResult
from src.pysatl_experiment.worker.power import PowerWorker, PowerWorkerResult
from src.pysatl_experiment.worker.time_complexity import TimeComplexityWorker, TimeComplexityWorkerResult


def universal_execute_task(spec: TaskSpec):
    """
    Execute experiment task in subprocess.

    Parameters
    ----------
    spec : TaskSpec
        Serialized task specification.

    Returns
    -------
    tuple
        Experiment execution result payload with following format:
         (experiment_type, criterion_code, sample_size, result_data).
    """
    storage = AlchemyRandomValuesStorage(spec.db_path)
    storage.init()

    match spec.experiment_type:
        case ExperimentType.CRITICAL_VALUE | ExperimentType.TIME_COMPLEXITY:
            data = get_sample_data_from_storage(
                generator_name=spec.hypothesis_generator,
                generator_parameters=spec.hypothesis_parameters,
                sample_size=spec.sample_size,
                count=spec.monte_carlo_count,
                data_storage=storage,
            )
        case ExperimentType.POWER:
            data = get_sample_data_from_storage(
                generator_name=spec.alternative_generator,
                generator_parameters=spec.alternative_parameters,
                sample_size=spec.sample_size,
                count=spec.monte_carlo_count,
                data_storage=storage,
            )
        case _:
            raise ValueError(f"Unknown experiment type: {spec.experiment_type}.")

    stat_module = importlib.import_module(spec.statistic_module)
    stat_class = getattr(stat_module, spec.statistic_class_name)
    statistics = stat_class()

    match spec.experiment_type:
        case ExperimentType.TIME_COMPLEXITY:
            time_worker = TimeComplexityWorker(statistics=statistics, sample_data=data)
            time_result: TimeComplexityWorkerResult = time_worker.execute()

            return ExperimentType.TIME_COMPLEXITY, statistics.code(), spec.sample_size, time_result.results_times

        case ExperimentType.CRITICAL_VALUE:
            crit_worker = CriticalValueWorker(statistics=statistics, sample_data=data)
            crit_result: CriticalValueWorkerResult = crit_worker.execute()

            return ExperimentType.CRITICAL_VALUE, statistics.code(), spec.sample_size, crit_result.results_statistics

        case ExperimentType.POWER:
            if spec.significance_level is None:
                raise ValueError("Significance level is required for power experiment.")

            power_worker = PowerWorker(
                statistics=statistics,
                sample_data=data,
                significance_level=spec.significance_level,
                storage_connection=spec.db_path,
            )
            power_result: PowerWorkerResult = power_worker.execute()

            return (
                ExperimentType.POWER,
                statistics.code(),
                spec.sample_size,
                power_result.results_criteria,
                spec.alternative_generator,
                spec.alternative_parameters,
                spec.significance_level,
            )

        case _:
            raise ValueError(f"Unsupported experiment type: {spec.experiment_type}.")
