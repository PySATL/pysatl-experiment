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


def _parse_generators(json_dicts_list):
    res_list = list()

    for json_dict in json_dicts_list:
        gen_name = json_dict["name"]

        try:
            gen_params = json_dict["params"]
        except KeyError:
            gen_params = None

        generator = GeneratorResolver.load(generator_name=gen_name, params=gen_params)
        res_list.append(generator)

    return res_list


def _parse_listeners(json_dicts_list):
    res_list = list()

    for json_dict in json_dicts_list:
        lstn_name = json_dict["name"]

        try:
            lstn_params = json_dict["params"]
        except KeyError:
            lstn_params = None

        listener = ListenerResolver.load(listener_name=lstn_name, params=lstn_params)

        res_list.append(listener)

    return res_list


def _parse_hypothesis(json_dict):
    hyp_name = json_dict["name"]

    try:
        hyp_params = json_dict["params"]
    except KeyError:
        hyp_params = None

    hyp = HypothesisResolver.load(hypothesis_name=hyp_name, params=hyp_params)

    return hyp


def _parse_tests(json_dicts_list):
    res_list = list()

    for json_dict in json_dicts_list:
        test_name = json_dict["name"]

        try:
            test_params = json_dict["params"]
        except KeyError:
            test_params = None

        generator = TestResolver.load(test_name=test_name, params=test_params)
        res_list.append(generator)

    return res_list


def _parse_worker(json_dict):
    worker_name = json_dict["name"]

    try:
        worker_params = json_dict["params"]
    except KeyError:
        worker_params = None

    worker = WorkerResolver.load(worker_name=worker_name, params=worker_params)
    return worker


def _parse_store(json_dict):
    store_name = json_dict["name"]

    try:
        store_params = json_dict["params"]
    except KeyError:
        store_params = None

    store = StoreResolver.load(store_name=store_name, params=store_params)

    return store


def _parse_builder(json_dict):
    builder_name = json_dict["name"]

    try:
        builder_params = json_dict["params"]
    except KeyError:
        builder_params = None

    builder = BuilderResolver.load(builder_name=builder_name, params=builder_params)

    return builder


def parse_config(path: str):
    try:
        # Configuring experiment
        with Path(path).open() as configFile:
            config_data = json.load(configFile)

        default_threads = multiprocessing.cpu_count()

        alter_config_data = config_data["alternative_configuration"]
        try:
            threads = alter_config_data["threads"]
        except KeyError:
            threads = default_threads

        alternative_configuration = AlternativeConfiguration(
            alternatives=_parse_generators(alter_config_data["alternatives"]),
            sizes=alter_config_data["sizes"],
            count=alter_config_data["count"],
            threads=threads,
            listeners=_parse_listeners(alter_config_data["listeners"])
        )

        tests_config_data = config_data["test_configuration"]

        tests = _parse_tests(tests_config_data["tests"])
        try:
            test_threads = tests_config_data["threads"]
        except KeyError:
            test_threads = default_threads

        tests_worker_config_data = tests_config_data["worker"]
        tests_worker_params_config_data = tests_worker_config_data["params"]

        critical_value_store = _parse_store(tests_worker_params_config_data["cv_store"])
        # tests_worker_params_config_data["critical_value_store"]["params"]["db_url"]

        hypothesis = _parse_hypothesis(tests_worker_config_data["params"]["hypothesis"])

        power_calculation_worker = _parse_worker(tests_worker_config_data)
        power_calculation_worker.cv_store = critical_value_store
        power_calculation_worker.hypothesis = hypothesis

        # (tests_worker_params_config_data["alpha"], tests_worker_params_config_data["monte_carlo_count"],

        test_data_tels = _parse_listeners(tests_config_data["listeners"])

        test_configuration = TestConfiguration(
            tests=tests,
            threads=test_threads,
            worker=power_calculation_worker,
            listeners=test_data_tels,
        )

        report_data = config_data["report_configuration"]
        report_builder = _parse_builder(report_data["report_builder"])
        report_listeners = _parse_listeners(report_data["listeners"])
        report_configuration = ReportConfiguration(report_builder=report_builder,
                                                   listeners=report_listeners)

        rvs_store_data = config_data["rvs_store"]
        rvs_store = (_parse_store(rvs_store_data))
        # (db_url=rvs_store_data["params"]["db_url"]))

        result_store_data = config_data["result_store"]
        result_store = (_parse_store(result_store_data))
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
        traceback.print_exc()  # TODO: remove later
        return None


if __name__ == "__main__":
    # TODO: tested only on Weibull
    print("Parsing configuration")
    testPath = "config_examples/weibull_experiment.json"

    experiment_configuration = parse_config(testPath)

    if experiment_configuration is not None:
        experiment = Experiment(experiment_configuration)
        print("Starting experiment")

        # Execute experiment
        experiment.execute()
        print("Success")

    print("Ending work")

#  TODO: different methods for different stores?? also, fool check
#  TODO: add big parsing test
#  TODO: update docker_file
