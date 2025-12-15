import importlib
from pysatl_experiment.parallel.task_spec import TaskSpec
from pysatl_experiment.persistence.random_values.sqlite.sqlite import SQLiteRandomValuesStorage
from pysatl_experiment.experiment_new.step.execution.common.utils.utils import get_sample_data_from_storage
from pysatl_experiment.worker.power.power import PowerWorker
from pysatl_experiment.worker.critical_value.critical_value import CriticalValueWorker
from pysatl_experiment.worker.time_complexity.time_complexity import TimeComplexityWorker


def universal_execute_task(spec: TaskSpec):
    """
    Universal task function that runs in a subprocess.
    Returns: (experiment_type, criterion_code, sample_size, result_data)
    """

    storage = SQLiteRandomValuesStorage(spec.db_path)
    storage.init()

    if spec.experiment_type in ("critical_value", "time_complexity"):
        data = get_sample_data_from_storage(
            generator_name=spec.hypothesis_generator,
            generator_parameters=spec.hypothesis_parameters,
            sample_size=spec.sample_size,
            count=spec.monte_carlo_count,
            data_storage=storage,
        )
    elif spec.experiment_type == "power":
        data = get_sample_data_from_storage(
            generator_name=spec.alternative_generator,
            generator_parameters=spec.alternative_parameters,
            sample_size=spec.sample_size,
            count=spec.monte_carlo_count,
            data_storage=storage,
        )
    else:
        raise ValueError(f"Unknown experiment type: {spec.experiment_type}")

    stat_module = importlib.import_module(spec.statistic_module)
    stat_class = getattr(stat_module, spec.statistic_class_name)
    statistics = stat_class()

    if spec.experiment_type == "time_complexity":
        worker = TimeComplexityWorker(statistics=statistics, sample_data=data)
        result = worker.execute()
        return ("time_complexity",
                statistics.code(),
                spec.sample_size,
                result.results_times)

    elif spec.experiment_type == "critical_value":
        worker = CriticalValueWorker(statistics=statistics, sample_data=data)
        result = worker.execute()
        return ("critical_value",
                statistics.code(),
                spec.sample_size,
                result.results_statistics)

    elif spec.experiment_type == "power":
        worker = PowerWorker(
            statistics=statistics,
            sample_data=data,
            significance_level=spec.significance_level,
            storage_connection=spec.db_path,
        )
        result = worker.execute()
        return (
            "power",
            statistics.code(),
            spec.sample_size,
            result.results_criteria,
            spec.alternative_generator,
            spec.alternative_parameters,
            spec.significance_level,
        )
    else:
        raise ValueError(f"Unsupported experiment type: {spec.experiment_type}")
