import json
import multiprocessing
import traceback
from json import JSONDecodeError
from pathlib import Path

from stattest.experiment import Experiment
from stattest.experiment.configuration.configuration import (
    AlternativeConfiguration,
    ExperimentConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.resolvers.builder_resolver import BuilderResolver
from stattest.resolvers.generator_resolver import GeneratorResolver
from stattest.resolvers.hypothesis_resolver import HypothesisResolver
from stattest.resolvers.listener_resolver import ListenerResolver
from stattest.resolvers.store_resolver import StoreResolver
from stattest.resolvers.test_resolver import TestResolver
from stattest.resolvers.worker_resolver import WorkerResolver


def _parse_json_class_list(resolver, json_dicts_list):
    class_list = list()

    for json_dict in json_dicts_list:
        class_name = json_dict["name"]

        try:
            class_params = json_dict["params"]
        except KeyError:
            class_params = None

        class_ = resolver.load(class_name, params=class_params)
        class_list.append(class_)

    return class_list


def _parse_json_class(resolver, json_dict):
    class_name = json_dict["name"]

    try:
        class_params = json_dict["params"]
    except KeyError:
        class_params = None

    class_ = resolver.load(class_name, params=class_params)

    return class_


def parse_config(path: str):
    try:
        # Configuring experiment
        with Path(path).open() as configFile:
            config_data = json.load(configFile)

        default_threads = multiprocessing.cpu_count()

        alter_config_data = config_data["generator_configuration"]
        try:
            threads = alter_config_data["threads"]
        except KeyError:
            threads = default_threads

        alternative_configuration = AlternativeConfiguration(
            alternatives=_parse_json_class_list(GeneratorResolver, alter_config_data["generators"]),
            sizes=alter_config_data["sizes"],
            count=alter_config_data["count"],
            threads=threads,
            listeners=_parse_json_class_list(ListenerResolver, alter_config_data["listeners"])
        )

        tests_config_data = config_data["test_configuration"]

        tests = _parse_json_class_list(TestResolver, tests_config_data["tests"])
        try:
            test_threads = tests_config_data["threads"]
        except KeyError:
            test_threads = default_threads

        tests_worker_config_data = tests_config_data["worker"]
        tests_worker_params_config_data = tests_worker_config_data["params"]

        critical_value_store = _parse_json_class(StoreResolver, tests_worker_params_config_data["cv_store"])
        # tests_worker_params_config_data["critical_value_store"]["params"]["db_url"]

        hypothesis = _parse_json_class(HypothesisResolver, tests_worker_config_data["params"]["hypothesis"])

        power_calculation_worker = _parse_json_class(WorkerResolver, tests_worker_config_data)
        power_calculation_worker.cv_store = critical_value_store
        power_calculation_worker.hypothesis = hypothesis

        # (tests_worker_params_config_data["alpha"], tests_worker_params_config_data["monte_carlo_count"],

        test_data_tels = _parse_json_class_list(ListenerResolver, tests_config_data["listeners"])

        test_configuration = TestConfiguration(
            tests=tests,
            threads=test_threads,
            worker=power_calculation_worker,
            listeners=test_data_tels,
        )

        report_data = config_data["report_configuration"]
        report_builder = _parse_json_class(BuilderResolver, report_data["report_builder"])
        report_listeners = _parse_json_class_list(ListenerResolver, report_data["listeners"])
        report_configuration = ReportConfiguration(report_builder=report_builder,
                                                   listeners=report_listeners)

        rvs_store_data = config_data["rvs_store"]
        rvs_store = _parse_json_class(StoreResolver, rvs_store_data)
        # (db_url=rvs_store_data["params"]["db_url"]))

        result_store_data = config_data["result_store"]
        result_store = _parse_json_class(StoreResolver, result_store_data)
        # (db_url=result_store_data["params"]["db_url"]))

        print("Successfully parsed configuration")
        return ExperimentConfiguration(
            alternative_configuration=alternative_configuration,
            test_configuration=test_configuration,
            report_configuration=report_configuration,
            rvs_store=rvs_store,
            result_store=result_store,
        )
    except (JSONDecodeError, TypeError, OSError, FileExistsError):
        print("Error with configuration file")
        return None
