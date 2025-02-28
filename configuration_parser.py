import json
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
from stattest.experiment.generator import *
from stattest.experiment.generator.generators import *
from stattest.experiment.hypothesis import *
from stattest.experiment.listener.listeners import *
from stattest.experiment.report.model import *
from stattest.experiment.test.worker import *
from stattest.persistence.db_store import *
from stattest.persistence.db_store.result_store import *
from stattest.test import *
from stattest.test.weibull import *


def _find_class(class_name):
    return globals()[class_name]


def _call_class_by_name(class_name):
    class_ = _find_class(class_name)
    return class_()


def _find_list_of_classes(class_names_list):
    return list(map(lambda x: _call_class_by_name(x), class_names_list))


def _parse_params(class_name, class_params):
    new_params = class_params

    return class_name(new_params)


def _parse_alternatives(json_dicts_list):
    res_list = list()

    for json_dict in json_dicts_list:
        gen_name = _find_class(json_dict["name"])
        gen_params = json_dict["params"]
        res_list.append(_parse_params(gen_name, gen_params))

    return res_list


def parse_config(path: str):
    try:
        # Configuring experiment
        with Path(path).open() as configFile:
            config_data = json.load(configFile)

        alter_config_data = config_data["alternative_configuration"]

        # TODO: default count of threads is multiprocessing.cpu_count()??
        alternative_configuration = AlternativeConfiguration(
            alternatives=_parse_alternatives(alter_config_data["alternatives"]),
            sizes=alter_config_data["sizes"],
            count=alter_config_data["count"],
            threads=alter_config_data["threads"],
            listeners=_find_list_of_classes(alter_config_data["listeners"])
        )

        tests_config_data = config_data["test_configuration"]

        tests = _find_list_of_classes(tests_config_data["tests"])
        test_threads = tests_config_data["threads"]

        tests_worker_config_data = tests_config_data["worker"]
        tests_worker_params_config_data = tests_worker_config_data["params"]

        critical_value_store = _find_class(
            tests_worker_params_config_data["critical_value_store"]["name"])(
            db_url=tests_worker_params_config_data["critical_value_store"]["params"]["db_url"])
        hypothesis = _find_class(tests_worker_config_data["params"]["hypothesis"])

        power_calculation_worker = _find_class(tests_worker_config_data["name"])(
            tests_worker_params_config_data["alpha"], tests_worker_params_config_data["monte_carlo_count"],
            critical_value_store, hypothesis=hypothesis
        )
        test_data_tels = _find_list_of_classes(tests_config_data["listeners"])

        test_configuration = TestConfiguration(
            tests=tests,
            threads=test_threads,
            worker=power_calculation_worker,
            listeners=test_data_tels,
        )

        report_data = config_data["report_configuration"]
        report_builder = _find_class(report_data["report_builder"])
        report_listeners = _find_list_of_classes(report_data["listeners"])
        report_configuration = ReportConfiguration(report_builder=report_builder,
                                                   listeners=report_listeners)

        rvs_store_data = config_data["rvs_store"]
        rvs_store = _find_class(rvs_store_data["name"])(db_url=rvs_store_data["params"]["db_url"])

        result_store_data = config_data["result_store"]
        result_store = (_find_class(result_store_data["name"])
                        (db_url=result_store_data["params"]["db_url"]))

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

#  TODO: dict alternatives, support for tests dict
#  TODO: add parsing test
#  TODO: update docker_file
