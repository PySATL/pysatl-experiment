"""
Abstract factory infrastructure for experiment construction.

The module contains the base factory implementation used to assemble
experiment execution pipelines. It encapsulates common logic shared by all experiment
types and provides extension points for experiment-specific step creation.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, cast

from pysatl_criterion.persistence.models.base import IDataStorage
from pysatl_criterion.persistence.models.limit_distribution import LimitDistributionQuery
from pysatl_criterion.persistence.sqlalchemy.datastorage import AlchemyLimitDistributionStorage
from pysatl_criterion.statistics import (
    AbstractBetaGofStatistic,
    AbstractExponentialityGofStatistic,
    AbstractGammaGofStatistic,
    AbstractLogNormalGofStatistic,
    AbstractNormalityGofStatistic,
    AbstractStudentGofStatistic,
    AbstractUniformGofStatistic,
    AbstractWeibullGofStatistic,
)

from pysatl_experiment.configuration.criteria_config import CriterionConfig
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.hypothesis import Hypothesis
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.experiment.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment.generator import AbstractRVSGenerator
from pysatl_experiment.experiment.generator.generators import (
    BetaRVSGenerator,
    ExponentialGenerator,
    GammaGenerator,
    LognormGenerator,
    NormalGenerator,
    TRVSGenerator,
    UniformGenerator,
    WeibullGenerator,
)
from pysatl_experiment.persistence.criterion_power_storage import AlchemyPowerStorage
from pysatl_experiment.persistence.experiment_storage import AlchemyExperimentStorage
from pysatl_experiment.persistence.model.experiment import ExperimentQuery, IExperimentStorage
from pysatl_experiment.persistence.model.power import PowerQuery
from pysatl_experiment.persistence.model.random_values import IRandomValuesStorage, RandomValuesAllQuery
from pysatl_experiment.persistence.model.time_complexity import TimeComplexityQuery
from pysatl_experiment.persistence.random_values_storage import AlchemyRandomValuesStorage
from pysatl_experiment.persistence.time_complexity_storage import AlchemyTimeComplexityStorage


D = TypeVar("D", contravariant=True, bound=ExperimentData)
G = TypeVar("G", covariant=True, bound=IExperimentStep)
E = TypeVar("E", covariant=True, bound=IExperimentStep)
R = TypeVar("R", covariant=True, bound=IExperimentStep)
RS = TypeVar("RS", bound=IDataStorage)


class AbstractExperimentFactory(Generic[D, G, E, R, RS], ABC):
    """Base factory interface for experiment construction."""

    def __init__(self, experiment_data: D):
        self.experiment_data = experiment_data

    def create_experiment_steps(self) -> ExperimentSteps:
        """
        Create an experiment execution pipeline.

        Returns
        -------
        ExperimentSteps
            Fully configured experiment pipeline containing generation, execution and reporting steps
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
            execution_step = self._create_execution_step(data_storage, result_storage, experiment_storage)
            experiment_steps.execution_step = execution_step

        report_building_step = self._create_report_building_step(result_storage)
        experiment_steps.report_building_step = report_building_step

        return experiment_steps

    @abstractmethod
    def _create_generation_step(self, data_storage: IRandomValuesStorage) -> G:
        """
        Create a generation step.

        This method must be implemented by concrete factories.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Storage containing generated random samples.

        Returns
        -------
        G
            Configured generation step.
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
        Create an execution step.

        This method must be implemented by concrete experiment factories.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
        result_storage : RS
            Experiment result storage.
        experiment_storage : IExperimentStorage
            Experiment metadata storage.

        Returns
        -------
        E
            Configured execution step.

        """
        pass

    @abstractmethod
    def _create_report_building_step(self, result_storage: RS) -> R:
        """
        Create a report-building step.

        This method must be implemented by concrete experiment factories.

        Parameters
        ----------
        result_storage : RS
            Experiment result storage.

        Returns
        -------
        R
            Configured report-building step.

        """
        pass

    def _delete_sample_data(self, data_storage: IRandomValuesStorage) -> None:
        """
        Delete generated sample data.

        Selects an appropriate cleanup strategy depending on the current
        experiment type and removes stored random samples.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
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
        Delete samples generated under the null hypothesis.

        Removes all samples associated with the configured hypothesis
        generator and sample sizes.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
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
        Delete samples generated under alternative distributions.

        Removes all samples associated with configured alternative
        generators and sample sizes.

        Parameters
        ----------
        data_storage : IRandomValuesStorage
            Random values storage.
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
        Resolve metadata for the configured hypothesis generator.

        Creates a generator corresponding to the selected hypothesis and
        extracts information required for storage access and execution.

        Returns
        -------
        tuple[str, list[float], AbstractRVSGenerator]
            Tuple containing generator name, generator parameters and
            generator instance.

        Raises
        ------
        ValueError
            If the configured hypothesis is unsupported.
        """
        hypothesis_generator: AbstractRVSGenerator
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
        elif hypothesis == Hypothesis.GAMMA:
            hypothesis_generator = GammaGenerator()
            generator_name = "GAMMAGENERATOR"
            generator_parameters = [hypothesis_generator.alfa, hypothesis_generator.beta]
        elif hypothesis == Hypothesis.BETA:
            hypothesis_generator = BetaRVSGenerator()
            generator_name = "BETARVSGENERATOR"
            generator_parameters = [hypothesis_generator.a, hypothesis_generator.b]
        elif hypothesis == Hypothesis.LOGNORMAL:
            hypothesis_generator = LognormGenerator()
            generator_name = "LOGNORMGENERATOR"
            generator_parameters = [hypothesis_generator.s, hypothesis_generator.mu]
        elif hypothesis == Hypothesis.STUDENT:
            hypothesis_generator = TRVSGenerator(df=1)
            generator_name = "TRVSGENERATOR"
            generator_parameters = [hypothesis_generator.df]
        elif hypothesis == Hypothesis.UNIFORM:
            hypothesis_generator = UniformGenerator()
            generator_name = "UNIFORMGENERATOR"
            generator_parameters = [hypothesis_generator.a, hypothesis_generator.b]
        else:
            raise ValueError(f"Unknown hypothesis: {hypothesis}")

        # TODO: switch!

        return generator_name, generator_parameters, hypothesis_generator

    _HYPOTHESIS_TO_BASE_CLASS: dict[Hypothesis, type[Any]] = {
        Hypothesis.NORMAL: AbstractNormalityGofStatistic,
        Hypothesis.EXPONENTIAL: AbstractExponentialityGofStatistic,
        Hypothesis.WEIBULL: AbstractWeibullGofStatistic,
        Hypothesis.GAMMA: AbstractGammaGofStatistic,
        Hypothesis.BETA: AbstractBetaGofStatistic,
        Hypothesis.LOGNORMAL: AbstractLogNormalGofStatistic,
        Hypothesis.STUDENT: AbstractStudentGofStatistic,
        Hypothesis.UNIFORM: AbstractUniformGofStatistic,
    }

    def _get_criteria_config(self) -> list[CriterionConfig]:
        """
        Resolve criterion configurations.

        Maps user-provided criterion identifiers to concrete statistic
        implementations compatible with the configured hypothesis.

        Returns
        -------
        list[CriterionConfig]
            Resolved criterion configurations.

        Notes
        -----
        Criteria config consists of criterion from user, criterion code and statistics class object.
        """
        config = self.experiment_data.config
        base_class = self._HYPOTHESIS_TO_BASE_CLASS[config.hypothesis]
        short_code_to_subclass = {}
        for sub in base_class.__subclasses__():
            if getattr(sub, "__abstractmethods__", None):
                continue
            short_code_to_subclass[sub.code().split("_")[0]] = sub

        criteria_config = []
        for criterion in config.criteria:
            if criterion.criterion_code not in short_code_to_subclass:
                continue
            sub = short_code_to_subclass[criterion.criterion_code]
            criteria_config.append(
                CriterionConfig(
                    criterion=criterion,
                    criterion_code=sub.code(),
                    statistics_class_object=sub(),
                )
            )

        return criteria_config

    def _delete_results_from_storage(self, result_storage: IDataStorage) -> None:
        """
        Delete experiment results from storage.

        Creates storage queries corresponding to the current experiment
        configuration and removes all matching result records.

        Parameters
        ----------
        result_storage : IDataStorage
            Experiment result storage.
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

    @staticmethod
    def _create_critical_value_queries(
        statistics_codes: list[str],
        sample_sizes: list[int],
        monte_carlo_count: int,
    ) -> list[LimitDistributionQuery]:
        """
        Create critical value storage queries.

        Parameters
        ----------
        statistics_codes : list[str]
            Statistic implementation codes.
        sample_sizes : list[int]
            Sample sizes.
        monte_carlo_count : int
            Monte Carlo iteration count.

        Returns
        -------
        list[LimitDistributionQuery]
            Queries identifying critical value results.
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

    @staticmethod
    def _create_time_complexity_queries(
        statistics_codes: list[str],
        sample_sizes: list[int],
        monte_carlo_count: int,
    ) -> list[TimeComplexityQuery]:
        """
        Create time complexity storage queries.

        Parameters
        ----------
        statistics_codes : list[str]
            Statistic implementation codes.
        sample_sizes : list[int]
            Sample sizes.
        monte_carlo_count : int
            Monte Carlo iteration count.

        Returns
        -------
        list[TimeComplexityQuery]
            Queries identifying time complexity results.
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
        Create statistical power storage queries.

        Parameters
        ----------
        statistics_codes : list[str]
            Statistic implementation codes.
        sample_sizes : list[int]
            Sample sizes.
        monte_carlo_count : int
            Monte Carlo iteration count.

        Returns
        -------
        list[PowerQuery]
            Queries identifying power estimation results.
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
        Resolve experiment identifier.

        Builds an experiment query from the current configuration and
        retrieves the corresponding experiment identifier.

        Parameters
        ----------
        storage : IExperimentStorage
            Experiment metadata storage.

        Returns
        -------
        int
            Experiment identifier.

        Raises
        ------
        ValueError
            If the experiment configuration is not registered.
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
            alternatives = {alternative.generator_name: alternative.parameters for alternative in config.alternatives}

        query = ExperimentQuery(
            experiment_type=experiment_type.value,
            storage_connection=config.storage_connection,
            run_mode=config.run_mode.value,
            report_mode=config.report_mode.value,
            hypothesis=config.hypothesis.value,
            generator_type=config.generator_type.value,
            executor_type=config.executor_type.value,
            report_builder_type=config.report_builder_type.value,
            sample_sizes=config.sample_sizes,
            monte_carlo_count=config.monte_carlo_count,
            criteria=criteria,
            significance_levels=significance_levels,
            alternatives=alternatives,
            parallel_workers=config.parallel_workers,
        )

        experiment_id = storage.get_experiment_id(query)
        if experiment_id is None:
            raise ValueError("Experiment not found")

        return experiment_id

    def _init_data_storage(self) -> IRandomValuesStorage:
        """
        Initialize random values storage.

        Returns
        -------
        IRandomValuesStorage
            Initialized random values storage.
        """
        storage_connection = self.experiment_data.config.storage_connection
        data_storage = AlchemyRandomValuesStorage(storage_connection)
        data_storage.init()

        return data_storage

    def _init_experiment_storage(self) -> IExperimentStorage:
        """
        Initialize experiment metadata storage.

        Returns
        -------
        IExperimentStorage
            Initialized experiment metadata storage.
        """
        storage_connection = self.experiment_data.config.storage_connection
        data_storage = AlchemyExperimentStorage(storage_connection)
        data_storage.init()

        return data_storage

    def _init_result_storage(self) -> RS:
        """
        Initialize result storage.

        Creates and initializes a storage implementation corresponding
        to the configured experiment type.

        Returns
        -------
        RS
            Initialized result storage.

        Raises
        ------
        ValueError
            If the experiment type is unsupported.
        """
        experiment_type = self.experiment_data.config.experiment_type
        storage_connection = self.experiment_data.config.storage_connection
        if experiment_type == ExperimentType.CRITICAL_VALUE:
            limit_distribution_storage = AlchemyLimitDistributionStorage(storage_connection)
            limit_distribution_storage.init()
            return cast(RS, limit_distribution_storage)
        elif experiment_type == ExperimentType.POWER:
            power_storage = AlchemyPowerStorage(storage_connection)
            power_storage.init()
            return cast(RS, power_storage)
        elif experiment_type == ExperimentType.TIME_COMPLEXITY:
            time_complexity_storage = AlchemyTimeComplexityStorage(storage_connection)
            time_complexity_storage.init()
            return cast(RS, time_complexity_storage)
        else:
            raise ValueError(f"Unsupported experiment type: {experiment_type}")

    def _get_generator_class_object(
        self, generator_name: str, generator_parameters: list[float]
    ) -> AbstractRVSGenerator:
        """
        Create a generator instance by name.

        Parameters
        ----------
        generator_name : str
            Generator class name.
        generator_parameters : list[float]
            Generator constructor parameters.

        Returns
        -------
        AbstractRVSGenerator
            Configured generator instance.

        Raises
        ------
        ValueError
            If the generator implementation cannot be found.

        Notes
        -----
        Parameters are passed to the constructor in the same order as
        specified by the experiment configuration.
        """
        subclasses = AbstractRVSGenerator.__subclasses__()
        for sub in subclasses:
            sub_name = sub.__name__.upper()
            if sub_name == generator_name:
                # Arguments are passed in the order of the parameters list,
                # which is set by the user in CLI
                return cast(type[AbstractRVSGenerator], sub)(*generator_parameters)

        raise ValueError(f"Unknown generator: {generator_name}")


# TODO: warnings!!
# TODO: refactor factory layer?
