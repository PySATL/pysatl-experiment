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


if __name__ == "__main__":
    try:
        print("Starting experiment")
        # TODO: tested only on Weibull

        # Configuring experiment
        with Path("config_examples/weibull_experiment.json").open() as configFile:
            configData = json.load(configFile)

        alterConfigData = configData["alternative_configuration"]

        # TODO: default count of threads is multiprocessing.cpu_count()??
        alternative_configuration = AlternativeConfiguration(
            alternatives=_parse_alternatives(alterConfigData["alternatives"]),
            sizes=alterConfigData["sizes"],
            count=alterConfigData["count"],
            threads=alterConfigData["threads"],
            listeners=_find_list_of_classes(alterConfigData["listeners"])
        )

        testsConfigData = configData["test_configuration"]

        tests = _find_list_of_classes(testsConfigData["tests"])
        test_threads = testsConfigData["threads"]

        testsWorkerConfigData = testsConfigData["worker"]
        testsWorkerParamsConfigData = testsWorkerConfigData["params"]

        critical_value_store = _find_class(
            testsWorkerParamsConfigData["critical_value_store"]["name"])(
            db_url=testsWorkerParamsConfigData["critical_value_store"]["params"]["db_url"])
        hypothesis = _find_class(testsWorkerConfigData["params"]["hypothesis"])

        power_calculation_worker = _find_class(testsWorkerConfigData["name"])(
            testsWorkerParamsConfigData["alpha"], testsWorkerParamsConfigData["monte_carlo_count"],
            critical_value_store, hypothesis=hypothesis
        )
        test_data_tels = _find_list_of_classes(testsConfigData["listeners"])

        test_configuration = TestConfiguration(
            tests=tests,
            threads=test_threads,
            worker=power_calculation_worker,
            listeners=test_data_tels,
        )

        reportData = configData["report_configuration"]
        report_builder = _find_class(reportData["report_builder"])
        report_listeners = _find_list_of_classes(reportData["listeners"])
        report_configuration = ReportConfiguration(report_builder=report_builder
                                                   , listeners=report_listeners)

        rvsStoreData = configData["rvs_store"]
        rvs_store = _find_class(rvsStoreData["name"])(db_url=rvsStoreData["params"]["db_url"])

        resultStoreData = configData["result_store"]
        result_store = (_find_class(resultStoreData["name"])
                        (db_url=resultStoreData["params"]["db_url"]))

        experiment_configuration = ExperimentConfiguration(
            alternative_configuration=alternative_configuration,
            test_configuration=test_configuration,
            report_configuration=report_configuration,
            rvs_store=rvs_store,
            result_store=result_store,
        )
        experiment = Experiment(experiment_configuration)

        # Execute experiment
        experiment.execute()

        print("Success")
    except (JSONDecodeError, TypeError, OSError, FileExistsError):
        print("Error with configuration file")
        traceback.print_exc()  # TODO: remove later
    finally:
        print("Ending work")

#  TODO: dict alternatives, support for tests dict
#  TODO: add parsing test
