from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, cast

from pysatl_criterion.persistence.limit_distribution.sqlite.sqlite import (
    SQLiteLimitDistributionStorage,
)
from pysatl_criterion.persistence.model.common.data_storage.data_storage import IDataStorage
from pysatl_criterion.persistence.model.limit_distribution.limit_distribution import (
    LimitDistributionQuery,
)
from pysatl_criterion.statistics import (
    AbstractExponentialityGofStatistic,
    AbstractNormalityGofStatistic,
    AbstractWeibullGofStatistic,
)
from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.experiment_data.experiment_data import ExperimentData
from stattest.configuration.model.experiment_type.experiment_type import ExperimentType
from stattest.configuration.model.hypothesis.hypothesis import Hypothesis
from stattest.configuration.model.run_mode.run_mode import RunMode
from stattest.experiment.generator import AbstractRVSGenerator
from stattest.experiment.generator.generators import (
    ExponentialGenerator,
    NormalGenerator,
    WeibullGenerator,
)
from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.experiment_new.model.experiment_step.experiment_step import IExperimentStep
from stattest.persistence.experiment.sqlite.sqlite import SQLiteExperimentStorage
from stattest.persistence.model.experiment.experiment import ExperimentQuery, IExperimentStorage
from stattest.persistence.model.power.power import PowerQuery
from stattest.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllQuery,
)
from stattest.persistence.model.time_complexity.time_complexity import TimeComplexityQuery
from stattest.persistence.power.sqlite.sqlite import SQLitePowerStorage
from stattest.persistence.random_values.sqlite.sqlite import SQLiteRandomValuesStorage
from stattest.persistence.time_complexity.sqlite.sqlite import SQLiteTimeComplexityStorage


D = TypeVar("D", contravariant=True, bound=ExperimentData)
G = TypeVar("G", covariant=True, bound=IExperimentStep)
E = TypeVar("E", covariant=True, bound=IExperimentStep)
R = TypeVar("R", covariant=True, bound=IExperimentStep)
RS = TypeVar("RS", bound=IDataStorage)


class AbstractExperimentFactory(Generic[D, G, E, R, RS], ABC):
    """
    Abstract experiment factory interface.
    """

    def __init__(self, experiment_data: D):
        self.experiment_data = experiment_data

    def create_experiment_steps(self) -> ExperimentSteps:
        """
        Create experiment steps.

        :return: experiment steps.
        """

        data_storage = self._init_data_storage()
        result_storage = self._init_result_storage()
        experiment_storage = self._init_experiment_storage()

        run_mode = self.experiment_data.config.run_mode
        if run_mode == RunMode.OVERWRITE:
            self._delete_sample_data(data_storage)
            self._delete_results_from_storage(result_storage)

        experiment_id = self._get_experiment_id(experiment_storage)
        experiment_steps = ExperimentSteps(
            experiment_id=experiment_id,
            experiment_storage=experiment_storage,
            generation_step=None,
            execution_step=None,
            report_building_step=None,
        )

        is_generation_step_done = self.experiment_data.steps_done.is_generation_step_done
        is_execution_step_done = self.experiment_data.steps_done.is_execution_step_done

        if not is_generation_step_done:
            generation_step = self._create_generation_step(data_storage)
            experiment_steps.generation_step = generation_step

        if not is_execution_step_done:
            execution_step = self._create_execution_step(
                data_storage, result_storage, experiment_storage
            )
            experiment_steps.execution_step = execution_step

        report_building_step = self._create_report_building_step(result_storage)
        experiment_steps.report_building_step = report_building_step

        return experiment_steps

    @abstractmethod
    def _create_generation_step(self, data_storage: IRandomValuesStorage) -> G:
        """
        Create generation step.

        :param data_storage: random values storage.

        :return: generation step.
        """
        pass

    @abstractmethod
    def _create_execution_step(
        self,
        data_storage: IRandomValuesStorage,
        result_storage: RS,
        experiment_storage: IExperimentStorage,
    ) -> E:
        """
        Create execution step.

        :param data_storage: random values storage.
        :param result_storage: result storage.
        :param experiment_storage: experiment storage.

        :return: execution step.
        """
        pass

    @abstractmethod
    def _create_report_building_step(self, result_storage: RS) -> R:
        """
        Create report building step.

        :param result_storage: result storage.

        :return: report building step.
        """
        pass

    def _delete_sample_data(self, data_storage: IRandomValuesStorage) -> None:
        """
        Delete sample data.

        :param data_storage: random values storage.
        """

        experiment_type = self.experiment_data.config.experiment_type
        if experiment_type == ExperimentType.CRITICAL_VALUE:
            self._delete_hypothesis_sample_data(data_storage)
        elif experiment_type == ExperimentType.POWER:
            self._delete_alternatives_sample_data(data_storage)
        elif experiment_type == ExperimentType.TIME_COMPLEXITY:
            self._delete_hypothesis_sample_data(data_storage)

    def _delete_hypothesis_sample_data(self, data_storage: IRandomValuesStorage) -> None:
        """
        Delete hypothesis sample data.

        :param data_storage: random values storage.
        """

        generator_name, generator_parameters, _ = self._get_hypothesis_generator_metadata()
        sample_sizes = self.experiment_data.config.sample_sizes

        for sample_size in sample_sizes:
            all_data_query = RandomValuesAllQuery(
                generator_name=generator_name,
                generator_parameters=generator_parameters,
                sample_size=sample_size,
            )
            data_storage.delete_all_data(all_data_query)

    def _delete_alternatives_sample_data(self, data_storage: IRandomValuesStorage) -> None:
        """
        Delete alternatives sample data.

        :param data_storage: random values storage.
        """

        alternatives_config = self.experiment_data.config.alternatives
        sample_sizes = self.experiment_data.config.sample_sizes

        for sample_size in sample_sizes:
            for alternative in alternatives_config:
                generator_name = alternative.generator_name
                generator_parameters = alternative.parameters
                all_data_query = RandomValuesAllQuery(
                    generator_name=generator_name,
                    generator_parameters=generator_parameters,
                    sample_size=sample_size,
                )
                data_storage.delete_all_data(all_data_query)

    def _get_hypothesis_generator_metadata(self) -> tuple[str, list[float], AbstractRVSGenerator]:
        """
        Get hypothesis generator metadata.

        :return: generator name, generator parameters, generator object
        """

        hypothesis_generator: AbstractRVSGenerator
        generator_name = ""
        generator_parameters = []

        hypothesis = self.experiment_data.config.hypothesis
        if hypothesis == Hypothesis.NORMAL:
            hypothesis_generator = NormalGenerator()
            generator_name = "NORMALGENERATOR"
            generator_parameters = [hypothesis_generator.mean, hypothesis_generator.var]
        elif hypothesis == Hypothesis.EXPONENTIAL:
            hypothesis_generator = ExponentialGenerator()
            generator_name = "EXPONENTIALGENERATOR"
            generator_parameters = [hypothesis_generator.lam]
        elif hypothesis == Hypothesis.WEIBULL:
            hypothesis_generator = WeibullGenerator()
            generator_name = "WEIBULLGENERATOR"
            generator_parameters = [hypothesis_generator.a, hypothesis_generator.k]
        else:
            raise ValueError(f"Unknown hypothesis: {hypothesis}")

        return generator_name, generator_parameters, hypothesis_generator

    def _get_criteria_config(self) -> list[CriterionConfig]:
        """
        Get criteria config (criterion from user + criterion code + statistics class object).
        """

        config = self.experiment_data.config
        hypothesis = config.hypothesis

        base_class: type[Any]
        if hypothesis == Hypothesis.NORMAL:
            base_class = AbstractNormalityGofStatistic
        elif hypothesis == Hypothesis.EXPONENTIAL:
            base_class = AbstractExponentialityGofStatistic
        elif hypothesis == Hypothesis.WEIBULL:
            base_class = AbstractWeibullGofStatistic
        else:
            raise ValueError("Unknown hypothesis")

        criteria_config = []
        subclasses = base_class.__subclasses__()
        for sub in subclasses:
            if getattr(sub, "__abstractmethods__", None):
                continue
            potential_code = sub.code()
            potential_short_code = sub.code().split("_")[0]
            for criterion in config.criteria:
                short_code = criterion.criterion_code
                if potential_short_code == short_code:
                    criterion_config = CriterionConfig(
                        criterion=criterion,
                        criterion_code=potential_code,
                        statistics_class_object=sub(),
                    )
                    criteria_config.append(criterion_config)

        return criteria_config

    def _delete_results_from_storage(self, result_storage: IDataStorage) -> None:
        """
        Delete results from storage.

        :param result_storage: result storage.
        """

        experiment_type = self.experiment_data.config.experiment_type
        sample_sizes = self.experiment_data.config.sample_sizes
        monte_carlo_count = self.experiment_data.config.monte_carlo_count

        statistics_codes = []
        criteria_config = self._get_criteria_config()
        for criterion_config in criteria_config:
            statistics_codes.append(criterion_config.criterion_code)

        queries: list[Any] = []
        if experiment_type == ExperimentType.CRITICAL_VALUE:
            queries = self._create_critical_value_queries(
                statistics_codes=statistics_codes,
                sample_sizes=sample_sizes,
                monte_carlo_count=monte_carlo_count,
            )
        elif experiment_type == ExperimentType.POWER:
            queries = self._create_power_queries(
                statistics_codes=statistics_codes,
                sample_sizes=sample_sizes,
                monte_carlo_count=monte_carlo_count,
            )
        elif experiment_type == ExperimentType.TIME_COMPLEXITY:
            queries = self._create_time_complexity_queries(
                statistics_codes=statistics_codes,
                sample_sizes=sample_sizes,
                monte_carlo_count=monte_carlo_count,
            )
        else:
            raise ValueError("Unknown experiment type")

        for query in queries:
            result_storage.delete_data(query)

    def _create_critical_value_queries(
        self,
        statistics_codes: list[str],
        sample_sizes: list[int],
        monte_carlo_count: int,
    ) -> list[LimitDistributionQuery]:
        """
        Create critical values queries.

        :param statistics_codes: statistics codes.
        :param sample_sizes: sample sizes.
        :param monte_carlo_count: monte carlo count.

        :return: critical values queries.
        """

        queries = []
        for code in statistics_codes:
            for size in sample_sizes:
                query = LimitDistributionQuery(
                    criterion_code=code,
                    criterion_parameters=[],
                    sample_size=size,
                    monte_carlo_count=monte_carlo_count,
                )
                queries.append(query)

        return queries

    def _create_time_complexity_queries(
        self,
        statistics_codes: list[str],
        sample_sizes: list[int],
        monte_carlo_count: int,
    ) -> list[TimeComplexityQuery]:
        """
        Create time complexity queries.

        :param statistics_codes: statistics codes.
        :param sample_sizes: sample sizes.
        :param monte_carlo_count: monte carlo count.

        :return: time complexity queries.
        """

        queries = []
        for code in statistics_codes:
            for size in sample_sizes:
                query = TimeComplexityQuery(
                    criterion_code=code,
                    criterion_parameters=[],
                    sample_size=size,
                    monte_carlo_count=monte_carlo_count,
                )
                queries.append(query)

        return queries

    def _create_power_queries(
        self,
        statistics_codes: list[str],
        sample_sizes: list[int],
        monte_carlo_count: int,
    ) -> list[PowerQuery]:
        """
        Create power queries.

        :param statistics_codes: statistics codes.
        :param sample_sizes: sample sizes.
        :param monte_carlo_count: monte carlo count.

        :return: power queries.
        """

        queries = []
        significance_levels = self.experiment_data.config.significance_levels
        alternatives = self.experiment_data.config.alternatives

        for code in statistics_codes:
            for size in sample_sizes:
                for significance_level in significance_levels:
                    for alternative in alternatives:
                        alternative_code = alternative.generator_name
                        alternative_parameters = alternative.parameters
                        query = PowerQuery(
                            criterion_code=code,
                            criterion_parameters=[],
                            sample_size=size,
                            monte_carlo_count=monte_carlo_count,
                            significance_level=significance_level,
                            alternative_code=alternative_code,
                            alternative_parameters=alternative_parameters,
                        )
                        queries.append(query)

        return queries

    def _get_experiment_id(self, storage: IExperimentStorage) -> int:
        """
        Get experiment id.

        :storage: experiment configuration storage.

        :return: experiment id.
        """

        config = self.experiment_data.config
        experiment_type = config.experiment_type

        criteria = {criterion.criterion_code: criterion.parameters for criterion in config.criteria}

        significance_levels = []
        alternatives = {}
        if experiment_type == ExperimentType.CRITICAL_VALUE:
            significance_levels = config.significance_levels
        elif experiment_type == ExperimentType.POWER:
            significance_levels = config.significance_levels
            alternatives = {
                alternative.generator_name: alternative.parameters
                for alternative in config.alternatives
            }

        query = ExperimentQuery(
            experiment_type=experiment_type.value,
            storage_connection=config.storage_connection,
            run_mode=config.run_mode.value,
            hypothesis=config.hypothesis.value,
            generator_type=config.generator_type.value,
            executor_type=config.executor_type.value,
            report_builder_type=config.report_builder_type.value,
            sample_sizes=config.sample_sizes,
            monte_carlo_count=config.monte_carlo_count,
            criteria=criteria,
            significance_levels=significance_levels,
            alternatives=alternatives,
        )

        experiment_id = storage.get_experiment_id(query)
        if experiment_id is None:
            raise ValueError("Experiment not found")

        return experiment_id

    def _init_data_storage(self) -> IRandomValuesStorage:
        """
        Init data storage.

        :return: data storage.
        """

        storage_connection = self.experiment_data.config.storage_connection
        data_storage = SQLiteRandomValuesStorage(storage_connection)
        data_storage.init()

        return data_storage

    def _init_experiment_storage(self) -> IExperimentStorage:
        """
        Init experiment configuration storage.

        :return: data storage.
        """

        storage_connection = self.experiment_data.config.storage_connection
        data_storage = SQLiteExperimentStorage(storage_connection)
        data_storage.init()

        return data_storage

    def _init_result_storage(self) -> RS:
        """
        Init result storage.

        :return: result storage.
        """

        experiment_type = self.experiment_data.config.experiment_type
        storage_connection = self.experiment_data.config.storage_connection
        if experiment_type == ExperimentType.CRITICAL_VALUE:
            limit_distribution_storage = SQLiteLimitDistributionStorage(storage_connection)
            limit_distribution_storage.init()
            return cast(RS, limit_distribution_storage)
        elif experiment_type == ExperimentType.POWER:
            power_storage = SQLitePowerStorage(storage_connection)
            power_storage.init()
            return cast(RS, power_storage)
        elif experiment_type == ExperimentType.TIME_COMPLEXITY:
            time_complexity_storage = SQLiteTimeComplexityStorage(storage_connection)
            time_complexity_storage.init()
            return cast(RS, time_complexity_storage)
        else:
            raise ValueError(f"Unsupported experiment type: {experiment_type}")

    def _get_generator_class_object(
        self, generator_name: str, generator_parameters: list[float]
    ) -> AbstractRVSGenerator:
        """
        Get generator class object by name and parameters.

        :param generator_name: generator name.
        :param generator_parameters: generator parameters.

        :return: generator class object.
        """

        subclasses = AbstractRVSGenerator.__subclasses__()
        for sub in subclasses:
            sub_name = sub.__name__.upper()
            if sub_name == generator_name:
                # arguments are passed in the order of the parameters list,
                # which is set by the user in CLI
                return sub(*generator_parameters)

        raise ValueError(f"Unknown generator: {generator_name}")
