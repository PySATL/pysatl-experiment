import json
import multiprocessing
from json import JSONDecodeError
from pathlib import Path

from stattest.experiment.configuration.configuration import (
    ExperimentConfiguration,
    GeneratorConfiguration,
    ReportConfiguration,
    TestConfiguration,
)
from stattest.parsable import Parsable
from stattest.resolvers.builder_resolver import BuilderResolver
from stattest.resolvers.generator_resolver import GeneratorResolver
from stattest.resolvers.hypothesis_resolver import HypothesisResolver
from stattest.resolvers.iresolver import IResolver
from stattest.resolvers.listener_resolver import ListenerResolver
from stattest.resolvers.store_resolver import StoreResolver
from stattest.resolvers.test_resolver import TestResolver
from stattest.resolvers.worker_resolver import WorkerResolver


class ConfigurationParser:
    @staticmethod
    def _parse_json_class_list(resolver: IResolver, json_dicts_list: list[dict]) -> list[Parsable]:
        class_list = list()

        for json_dict in json_dicts_list:
            class_name = json_dict.get("name")

            class_params = json_dict.get("params")

            class_ = resolver.load(name=class_name, params=class_params)
            class_list.append(class_)

        return class_list

    @staticmethod
    def _parse_json_class(resolver: IResolver, json_dict: dict) -> Parsable:
        class_name = json_dict["name"]

        try:
            class_params = json_dict["params"]
        except KeyError:
            class_params = None

        class_ = resolver.load(name=class_name, params=class_params)

        return class_

    @staticmethod
    def parse_generator_config(config) -> GeneratorConfiguration:
        return GeneratorConfiguration(
            alternatives=ConfigurationParser._parse_json_class_list(
                GeneratorResolver, config["generators"]
            ),
            sizes=config["sizes"],
            count=config["count"],
            skip_if_exists=config.get("skip_if_exists", True),
            clear_before=config.get("clear_before", False),
            skip_step=config.get("skip_step", False),
            show_progress=config.get("show_progress", False),
            threads=config.get("threads", multiprocessing.cpu_count()),
            listeners=ConfigurationParser._parse_json_class_list(
                ListenerResolver, config["listeners"]
            ),
        )

    @staticmethod
    def parse_configs(paths: list[str]) -> list[ExperimentConfiguration]:
        return [ConfigurationParser.parse_config(c) for c in paths]

    @staticmethod
    def parse_config(path: str) -> ExperimentConfiguration | None:
        try:
            # Configuring experiment
            cfg_dir = Path(__file__).parent
            r_path = (cfg_dir / path).resolve()
            with r_path.open() as configFile:
                config_data = json.load(configFile)

            default_threads = multiprocessing.cpu_count()

            generator_configuration = config_data.get("generator_configuration", {})
            alternative_configuration = ConfigurationParser.parse_generator_config(
                generator_configuration
            )

            tests_config_data = config_data["test_configuration"]

            tests = ConfigurationParser._parse_json_class_list(
                TestResolver, tests_config_data["tests"]
            )
            test_threads = tests_config_data.get("threads", default_threads)

            tests_worker_config_data = tests_config_data["worker"]
            tests_worker_params_config_data = tests_worker_config_data["params"]

            critical_value_store = ConfigurationParser._parse_json_class(
                StoreResolver, tests_worker_params_config_data["cv_store"]
            )
            # tests_worker_params_config_data["critical_value_store"]["params"]["db_url"]

            hypothesis = ConfigurationParser._parse_json_class(
                HypothesisResolver, tests_worker_config_data["params"]["hypothesis"]
            )

            power_calculation_worker = ConfigurationParser._parse_json_class(
                WorkerResolver, tests_worker_config_data
            )
            power_calculation_worker.cv_store = critical_value_store
            power_calculation_worker.hypothesis = hypothesis

            test_data_tels = ConfigurationParser._parse_json_class_list(
                ListenerResolver, tests_config_data["listeners"]
            )

            test_configuration = TestConfiguration(
                tests=tests,
                threads=test_threads,
                worker=power_calculation_worker,
                listeners=test_data_tels,
            )

            report_data = config_data["report_configuration"]
            report_builder = ConfigurationParser._parse_json_class(
                BuilderResolver, report_data["report_builder"]
            )
            report_listeners = ConfigurationParser._parse_json_class_list(
                ListenerResolver, report_data["listeners"]
            )
            report_configuration = ReportConfiguration(
                report_builder=report_builder, listeners=report_listeners
            )

            rvs_store_data = config_data["rvs_store"]
            rvs_store = ConfigurationParser._parse_json_class(StoreResolver, rvs_store_data)
            # (db_url=rvs_store_data["params"]["db_url"]))

            result_store_data = config_data["result_store"]
            result_store = ConfigurationParser._parse_json_class(StoreResolver, result_store_data)
            # (db_url=result_store_data["params"]["db_url"]))

            print("Successfully parsed configuration")
            return ExperimentConfiguration(
                alternative_configuration=alternative_configuration,
                test_configuration=test_configuration,
                report_configuration=report_configuration,
                rvs_store=rvs_store,
                result_store=result_store,
            )
        except (JSONDecodeError, TypeError, OSError, FileExistsError) as e:
            print(f"Error with configuration file: {e}")
            return None
