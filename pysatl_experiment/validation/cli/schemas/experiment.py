"""
Experiment configuration models.

This module defines the full configuration hierarchy for experiments,
including base configuration and specialized variants for power analysis,
critical value computation, and time complexity experiments.
"""

from typing import Any, Literal, Union

from pydantic import BaseModel, Field, ValidationError, ValidationInfo, field_validator, model_validator

from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode
from pysatl_experiment.configuration.model.step_type.step_type import StepType
from pysatl_experiment.validation.cli.commands.common.checker import SQLiteCriticalValueChecker
from pysatl_experiment.validation.cli.schemas.alternative import Alternative
from pysatl_experiment.validation.cli.schemas.criteria import CriteriaConfig, Criterion


class BaseExperimentConfig(BaseModel):
    """
    Base configuration for all experiments.

    Defines common parameters shared across all experiment types.

    Attributes
    ----------
    hypothesis : Hypothesis
        Statistical hypothesis being tested.
    run_mode : RunMode
        Execution mode of the experiment.
    report_mode : ReportMode
        Controls report generation behavior.
    generator_type : StepType
        Type of data generator step.
    executor_type : StepType
        Type of execution step.
    report_builder_type : StepType
        Type of report builder step.
    criteria : list[Criterion]
        List of statistical criteria.
    storage_connection : str
        Storage backend connection string.
    sample_sizes : list[int]
        Sample sizes used in experiment.
    monte_carlo_count : int
        Number of Monte Carlo simulations.
    parallel_workers : int
        Number of parallel workers.

    Raises
    ------
    ValueError
        If validation of criteria or numeric constraints fails.
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
        """
        Disallow CUSTOM step type for core pipeline steps.

        Parameters
        ----------
        value : StepType
            Step type value.

        Returns
        -------
        StepType
            Validated step type.

        Raises
        ------
        ValueError
            If StepType.CUSTOM is used.
        """
        if value == StepType.CUSTOM:
            raise ValueError(f"Type of '{value}' is not valid.\nPossible value are: Standard")
        return value

    @field_validator("sample_sizes")
    @classmethod
    def check_sample_sizes(cls, value):
        """
        Validate sample sizes.

        Ensures all sample sizes are >= 10.

        Parameters
        ----------
        value : list[int]
            List of sample sizes.

        Returns
        -------
        list[int]
            Validated sample sizes.

        Raises
        ------
        ValueError
            If any sample size is below 10.
        """
        if any(size < 10 for size in value):
            raise ValueError("Sample sizes must be greater than 10.")  # TODO: fix magic constant!
        return value

    @field_validator("monte_carlo_count")
    @classmethod
    def check_monte_carlo(cls, value):
        """
        Validate Monte Carlo simulation count.

        Parameters
        ----------
        value : int
            Number of simulations.

        Returns
        -------
        int
            Validated value.

        Raises
        ------
        ValueError
            If value is less than 100.
        """
        if value < 100:
            raise ValueError("Monte Carlo count must be greater than 100.")  # TODO: fix magic constant!
        return value

    @model_validator(mode="after")
    def validate_using_criteria_config(self) -> "BaseExperimentConfig":
        """
        Validate criteria compatibility via CriteriaConfig.

        Delegates validation to CriteriaConfig model.

        Returns
        -------
        BaseExperimentConfig
            Validated configuration.

        Raises
        ------
        ValueError
            If criteria are incompatible with hypothesis.
        """
        try:
            data_to_validate = {
                "hypothesis": self.hypothesis,
                "criteria": self.criteria,
            }
            CriteriaConfig.model_validate(data_to_validate)

        except ValidationError as e:
            error_messages = [err["msg"] for err in e.errors()]
            raise ValueError("\n".join(error_messages))

        return self


class PowerConfig(BaseExperimentConfig):
    """
    Configuration for power analysis experiments.

    Extends base configuration with alternative hypotheses and significance
    levels, and validates availability of required critical values.

    Attributes
    ----------
    experiment_type : Literal["power"]
        Experiment type discriminator.
    alternatives : list[Alternative]
        Alternative hypotheses used in power analysis.
    significance_levels : list[float]
        Significance levels (alpha values).

    Raises
    ------
    ValueError
        If required critical values are missing or configuration is invalid.
    """

    experiment_type: Literal["power"]
    alternatives: list[Alternative]
    significance_levels: list[float]

    @model_validator(mode="before")
    @classmethod
    def validate_dependencies_on_critical_values(cls, value: Any, info: ValidationInfo) -> "PowerConfig":
        """
        Validate availability of required critical values.

        Ensures that all required (criterion, sample size) combinations
        exist in storage before running power analysis.

        Parameters
        ----------
        value : Any
            Raw configuration dictionary.
        info : ValidationInfo
            Validation context containing SQLiteCriticalValueChecker.

        Returns
        -------
        dict
            Original configuration if validation succeeds.

        Raises
        ------
        ValueError
            If required critical values are missing or checker is absent.
        """
        if not info.context or "critical_value_checker" not in info.context:
            raise ValueError("CriticalValueChecker must be provided in the validation context.")

        checker: SQLiteCriticalValueChecker | None = info.context["critical_value_checker"]
        if checker is None:
            raise ValueError("storage_connection must be set to check for critical values.")

        missing_combinations = []

        criteria = value.get("criteria", [])
        sample_sizes = value.get("sample_sizes", [])
        significance_levels = value.get("significance_levels", [])
        hypothesis_name = str(value.get("hypothesis", "")).upper()

        hypothesis_name_map = {
            "NORMAL": "NORMALITY",
            "EXPONENTIAL": "EXPONENTIALITY",
            "WEIBULL": "WEIBULL",
        }
        family_part = "GOODNESS_OF_FIT"
        hypothesis_part = hypothesis_name_map.get(hypothesis_name)

        if not hypothesis_part:
            raise ValueError(f"Unknown hypothesis '{hypothesis_name}' for constructing criterion name.")

        for criterion in criteria:
            code = criterion["criterion_code"] if isinstance(criterion, dict) else criterion.criterion_code
            full_name = f"{code.upper()}_{hypothesis_part}_{family_part}"
            for size in sample_sizes:
                if not checker.check_exists(full_name, size):
                    for alpha in significance_levels:
                        missing_combinations.append(
                            f"  - Hypothesis: {hypothesis_name}, "
                            f"Criterion: {code}, "
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

        return value


class CriticalValueConfig(BaseExperimentConfig):
    """
    Configuration for critical value computation experiments.

    Attributes
    ----------
    experiment_type : Literal["critical_value"]
        Experiment type discriminator.
    significance_levels : list[float]
        Significance levels (alpha values).
    """

    experiment_type: Literal["critical_value"]
    significance_levels: list[float]


class TimeComplexityConfig(BaseExperimentConfig):
    """
    Configuration for time complexity analysis experiments.

    Attributes
    ----------
    experiment_type : Literal["time_complexity"]
        Experiment type discriminator.
    """

    experiment_type: Literal["time_complexity"]
    pass


Experiment = Union[PowerConfig, CriticalValueConfig, TimeComplexityConfig]


class ExperimentConfig(BaseModel):
    """
    Root experiment configuration container.

    Holds experiment name and strongly typed configuration model selected
    by discriminator field `experiment_type`.

    Attributes
    ----------
    name : str
        Name of the experiment (validated against OS constraints).
    config : Experiment
        Experiment-specific configuration object.

    Raises
    ------
    ValueError
        If name is invalid or configuration is missing.
    """

    name: str
    config: Experiment = Field(discriminator="experiment_type")

    @field_validator("name")
    @classmethod
    def check_experiment_name(cls, value) -> str:
        """
        Validate experiment name.

        Ensures name:
        - is not reserved (Windows-style names)
        - contains no invalid filesystem characters
        - is not empty

        Parameters
        ----------
        value : str
            Experiment name.

        Returns
        -------
        str
            Validated experiment name.

        Raises
        ------
        ValueError
            If name is invalid or contains forbidden characters.
        """
        if value.endswith(".json"):
            value = value[:-5]

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
            raise ValueError(f"The name mustn't be: {bad_names}.")

        bad_chars = ["\\", "/", "\x00", ":", "*", "?", "<", ">", "|", " "]
        if any(char in value for char in bad_chars):
            found_bad_chars = [char for char in bad_chars if char in value]
            raise ValueError(f"Name '{value}' contain invalid characters: {', '.join(found_bad_chars)}.")

        if not value.strip():
            raise ValueError("Name cannot be empty or consist only of whitespace.")

        return value

    @field_validator("config")
    @classmethod
    def check_config(cls, value):
        """
        Validate presence of experiment configuration.

        Parameters
        ----------
        value : Experiment
            Configuration object.

        Returns
        -------
        Experiment
            Validated configuration.

        Raises
        ------
        ValueError
            If configuration is missing.
        """
        if value is None:
            raise ValueError("Missing config.")
        return value


# TODO: make an issue for dots in messages!!!
