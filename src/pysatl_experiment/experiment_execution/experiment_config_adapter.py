"""Pure adapters from built-in configuration to runtime objects and storage queries."""

from dataclasses import replace

from pysatl_criterion import DistributionType
from pysatl_criterion.generator.model import AbstractRVSGenerator
from pysatl_criterion.utils.generator import get_available_generator
from pysatl_criterion.utils.statistic import get_available_criteria

from pysatl_experiment.configuration import ExperimentConfig, PowerExperimentConfig
from pysatl_experiment.experiment_execution.configured_criterion import ConfiguredCriterion
from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionQuery
from pysatl_experiment.persistence.models.power import PowerQuery
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityQuery
from pysatl_experiment.types import Alternative
from pysatl_experiment.utils.generator_code import make_generator_code


class ExperimentConfigAdapter:
    """Adapt configuration without reading or changing persisted state."""

    def __init__(self, config: ExperimentConfig):
        self.config = config

    @property
    def sample_sizes(self) -> list[int]:
        """Read sample sizes from the step that owns them."""
        if isinstance(self.config, PowerExperimentConfig):
            return self.config.execute.sample_sizes
        return self.config.generate.sample_sizes

    @property
    def alternatives(self) -> list[Alternative]:
        """Adapt configured distributions to the power step's runtime objects."""
        return [
            Alternative(
                distribution_type=generator_code,
                parameters=parameters,
            )
            for generator_code, parameters, _ in self.generator_metadata()
        ]

    def generators(self):
        """Construct generators using midpoint values for parameter ranges."""
        generators = []
        for distribution in self.config.generate.distributions:
            parameters = {
                name: (sum(value) / 2 if isinstance(value, list) else value)
                for name, value in distribution.distribution_params.items()
            }
            generators.append(get_available_generator(DistributionType(distribution.distribution_type), parameters))
        return generators

    def generator_metadata(self) -> list[tuple[str, dict[str, float | list[float]], AbstractRVSGenerator]]:
        """Describe each sample series using configured ranges and resolved defaults."""
        metadata = []
        for distribution, generator in zip(self.config.generate.distributions, self.generators(), strict=True):
            parameters = generator.parameters() | distribution.distribution_params
            generator_code = make_generator_code(distribution.distribution_type, parameters)
            metadata.append((generator_code, parameters, generator))
        return metadata

    def hypothesis_generator_metadata(self):
        """Describe the single source distribution required by critical value execution."""
        metadata = self.generator_metadata()
        if len(metadata) != 1:
            raise ValueError("This execution step currently requires one source distribution")
        return metadata[0]

    def criterion_specs(self) -> list[CriterionSpec]:
        """Resolve importable implementations and full constructor parameters."""
        execution = self.config.execute
        classes = {
            cls.short_code(): cls
            for cls in get_available_criteria(DistributionType(execution.hypothesis))
            if not getattr(cls, "__abstractmethods__", None)
        }
        return [
            CriterionSpec(
                code=classes[item.criterion_code].code(),
                implementation=classes[item.criterion_code],
                parameters=execution.hypothesis_params | item.parameters,
            )
            for item in execution.criteria
        ]

    def criteria_config(self) -> list[ConfiguredCriterion]:
        """Construct statistics for consumers requiring live instances."""
        return [
            ConfiguredCriterion(
                criterion=replace(item, parameters=spec.parameters),
                criterion_code=spec.code,
                statistics_class_object=spec.implementation(**spec.parameters),
            )
            for item, spec in zip(self.config.execute.criteria, self.criterion_specs(), strict=True)
        ]

    def result_queries(self):
        """Describe the results belonging to the configured computations."""
        if self.config.experiment_type == "time_complexity":
            criteria = self.criterion_specs()
            for generator_code, _, _ in self.generator_metadata():
                for criterion in criteria:
                    for size in self.sample_sizes:
                        yield TimeComplexityQuery(
                            experiment_name=self.config.experiment_name,
                            generator_code=generator_code,
                            criterion_code=criterion.code,
                            criterion_parameters=criterion.parameters,
                            sample_size=size,
                            samples_count=self.config.execute.monte_carlo_count,
                        )
            return
        for criterion in self.criterion_specs():
            for size in self.sample_sizes:
                common = dict(
                    criterion_code=criterion.code,
                    criterion_parameters=criterion.parameters,
                    sample_size=size,
                )
                count = self.config.execute.monte_carlo_count
                if self.config.experiment_type == "critical_value":
                    yield LimitDistributionQuery(
                        experiment_name=self.config.experiment_name, **common, monte_carlo_count=count
                    )
                elif isinstance(self.config, PowerExperimentConfig):
                    for alternative in self.alternatives:
                        for alpha in self.config.execute.significance_levels:
                            yield PowerQuery(
                                experiment_name=self.config.experiment_name,
                                **common,
                                monte_carlo_count=count,
                                significance_level=alpha,
                                alternative_code=alternative.distribution_type,
                                alternative_parameters=alternative.parameters,
                            )
