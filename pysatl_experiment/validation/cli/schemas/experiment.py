from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator, model_validator

from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.validation.cli.commands.common.checker import SQLiteCriticalValueChecker
from pysatl_experiment.validation.cli.schemas.alternative import Alternative
from pysatl_experiment.validation.cli.schemas.criteria import CriteriaConfig, Criterion


class BaseExperimentConfig(BaseModel):
    """Base configuration for all experiment types.

    This class defines the common set of parameters that are required for any
    type of experiment.

    Attributes:
        hypothesis (Hypothesis): The statistical hypothesis to be tested.
        run_mode (RunMode): The mode in which the experiment will be run
        report_mode (ReportMode): The mode for generating reports.
        generator_type (StepType): The type of the data generator step.
        executor_type (StepType): The type of the execution step.
        report_builder_type (StepType): The type of the report builder step.
        criteria (list[Criterion]): A list of criteria for the experiment.
        storage_connection (str): The connection string or path for data storage.
        sample_sizes (list[int]): A list of sample sizes to be used in the experiment.
        monte_carlo_count (int): The number of Monte Carlo simulations to run.
    """

    hypothesis: Hypothesis
    run_mode: RunMode
    report_mode: ReportMode
    generator_type: StepType
    executor_type: StepType
    report_builder_type: StepType
    criteria: list[Criterion]
    storage_connection: str
    sample_sizes: list[int]
    monte_carlo_count: int
    parallel_workers: int

    @field_validator("generator_type", "executor_type", "report_builder_type")
    @classmethod
    def check_custom_step(cls, value):
        if value == StepType.CUSTOM:
            raise ValueError(f"Type of '{value}' is not valid.\nPossible value are: Standard")
        return value

    @field_validator("sample_sizes")
    @classmethod
    def check_sample_sizes(cls, value):
        if any(size < 10 for size in value):
            raise ValueError("Sample sizes must be greater than 10.")
        return value

    @field_validator("monte_carlo_count")
    @classmethod
    def check_monte_carlo(cls, value):
        if value < 100:
            raise ValueError("Monte Carlo count must be greater than 100.")
        return value

    @model_validator(mode="after")
    def validate_using_criteria_config(self) -> "BaseExperimentConfig":
        try:
            data_to_validate = {
                "hypothesis": self.hypothesis,
                "criteria": self.criteria,
            }
            CriteriaConfig.model_validate(data_to_validate)

        except ValidationError as e:
            error_message = e.errors()[0]["msg"]
            raise ValueError(error_message)

        return self


class PowerConfig(BaseExperimentConfig):
    """
    Configuration specific to a power analysis experiment.

    This extends the base configuration with parameters required for
    calculating statistical power.

    Attributes:
        experiment_type (Literal["power"]): The type of the experiment.
        alternatives (list[Alternative]): A list of alternative hypotheses.
        significance_levels (list[float]): A list of significance levels (alpha).
    """

    experiment_type: Literal["power"]
    alternatives: list[Alternative]
    significance_levels: list[float]

    @model_validator(mode="after")
    def validate_dependencies_on_critical_values(self, info: ValidationInfo) -> "PowerConfig":
        if not info.context or "critical_value_checker" not in info.context:
            raise ValueError("CriticalValueChecker must be provided in the validation context.")

        checker: SQLiteCriticalValueChecker = info.context["critical_value_checker"]
        missing_combinations = []

        hypothesis_name_map = {
            "NORMAL": "NORMALITY",
            "EXPONENTIAL": "EXPONENTIALITY",
            "WEIBULL": "WEIBULL",
        }
        family_part = "GOODNESS_OF_FIT"
        hypothesis_part = hypothesis_name_map.get(self.hypothesis.name)

        if not hypothesis_part:
            raise ValueError(f"Unknown hypothesis '{self.hypothesis.name}' for constructing criterion name.")

        for criterion in self.criteria:
            for size in self.sample_sizes:
                full_name_to_check = f"{criterion.criterion_code.upper()}_{hypothesis_part}_{family_part}"

                if not checker.check_exists(self.hypothesis.name, full_name_to_check, size):
                    for alpha in self.significance_levels:
                        missing_combinations.append(
                            f"  - Hypothesis: {self.hypothesis.name}, "
                            f"Criterion: {criterion.criterion_code}, "
                            f"Sample Size: {size}, "
                            f"Significance: {alpha}"
                        )

        if missing_combinations:
            unique_missing = sorted(list(set(missing_combinations)))
            error_message = (
                "Power experiment cannot be run because the following critical values are missing.\n"
                "Please run a 'critical_value' experiment for them first:\n"
            )
            error_message += "\n".join(unique_missing)
            raise ValueError(error_message)

        return self


class CriticalValueConfig(BaseExperimentConfig):
    """
    Configuration specific to a critical value computation experiment.

    This extends the base configuration with parameters needed for
    determining critical values.

    Attributes:
        experiment_type (Literal["critical_value"]): The type of the experiment.
        significance_levels (list[float]): A list of significance levels (alpha).
    """

    experiment_type: Literal["critical_value"]
    significance_levels: list[float]


class TimeComplexityConfig(BaseExperimentConfig):
    """
    Configuration for a time complexity analysis experiment.

    This extends the base configuration for experiments focused on measuring
    computational time complexity.

    Attributes:
        experiment_type (Literal["time_complexity"]): The type of the experiment.
    """

    experiment_type: Literal["time_complexity"]
    pass


Experiment = Union[PowerConfig, CriticalValueConfig, TimeComplexityConfig]


class ExperimentConfig(BaseModel):
    """
    The main container for an experiment's configuration.

    This model holds the name of the experiment and a specific configuration
    object, which can be one of the defined experiment types.

    Attributes:
        name (str): The name of the experiment.
        config (Experiment): The specific configuration for the experiment,
            discriminated by `experiment_type`.
    """

    name: str
    config: Experiment = Field(discriminator="experiment_type")

    @field_validator("name")
    @classmethod
    def check_experiment_name(cls, value) -> str:
        bad_names = [
            "CON",
            "AUX",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "LPT1",
            "LPT2",
            "LPT3",
            "PRN",
            "NUL",
        ]
        if value.upper() in bad_names:
            raise ValueError(f"The name mustn't be: {bad_names}")

        bad_chars = ["\\", "/", "\\0", ":", "*", "?", "<", ">", "|", "' '"]
        if any(char in value for char in bad_chars):
            found_bad_chars = [char for char in bad_chars if char in value]
            raise ValueError(f"Name '{value}' contain invalid characters: {', '.join(found_bad_chars)}")

        if not value.strip():
            raise ValueError("Name cannot be empty or consist only of whitespace.")

        return value

    @field_validator("config")
    @classmethod
    def check_config(cls, value):
        if value is None:
            raise ValueError("Missing config")
        return value
