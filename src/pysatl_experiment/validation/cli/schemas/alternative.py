"""
Alternative hypothesis configuration and validation.

This module defines structures for specifying alternative hypothesis
generators used in statistical experiments. It supports both string-based
and structured initialization, and performs runtime validation against
available generator implementations.
"""

import inspect
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.pysatl_experiment.configuration.model.experiment_type import ExperimentType
from src.pysatl_experiment.experiment.generator import AbstractRVSGenerator


class Alternative(BaseModel):
    """
    Specification of an alternative hypothesis generator.

    This model defines a generator and its numeric parameters used in
    statistical simulation experiments. It supports parsing from a
    space-separated string and validates generator existence and parameter
    correctness via introspection.

    Attributes
    ----------
    generator_name : str
        Name of the generator class (case-insensitive, resolved to uppercase).
    parameters : list[float]
        Numerical parameters passed to the generator constructor.

    Raises
    ------
    ValueError
        If generator name is invalid, ambiguous, or parameters are incorrect.
    """

    generator_name: str
    parameters: list[float]

    @field_validator("generator_name")
    @classmethod
    def normalize_and_resolve_generator_name(cls, value):
        """
        Resolve and normalize generator name.

        Converts user input to uppercase and tries to match it against
        available generator classes.

        Parameters
        ----------
        value : str
            User-provided generator name or prefix.

        Returns
        -------
        str
            Fully resolved generator class name in uppercase.

        Raises
        ------
        ValueError
            If no generator matches or multiple ambiguous matches exist.
        """
        available_generators: list[str] = [
            gen_cls.__name__.upper() for gen_cls in AbstractRVSGenerator.__subclasses__()
        ]

        user_prefix = value.upper()

        matches = [full_name for full_name in available_generators if full_name.startswith(user_prefix)]

        if len(matches) == 1:
            return matches[0]

        if not matches:
            raise ValueError(
                f"Generator prefix '{value}' did not match any available generators.\n"
                f"Available are: [{', '.join(available_generators)}]"
            )
        else:
            raise ValueError(
                f"Generator prefix '{value}' is ambiguous. It matches: [{', '.join(matches)}]. Please be more specific."
            )

    @model_validator(mode="before")
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        """
        Parse alternative configuration from a space-separated string.

        Converts string input into structured Alternative model.

        Parameters
        ----------
        data : Any
            Either a string in format "Generator param1 param2 ..."
            or a dictionary.

        Returns
        -------
        dict | Any
            Parsed dictionary if input was string, otherwise original value.

        Raises
        ------
        ValueError
            If input string is empty or parameters are invalid.
        """
        if not isinstance(data, str):
            return data

        parts = data.split()
        if not parts:
            raise ValueError("Alternative string cannot be empty.")

        generator_name = parts[0]
        try:
            parameters = [float(p) for p in parts[1:]]
        except ValueError:
            raise ValueError(f"All parameters for generator '{generator_name}' must be numbers.")

        return {"generator_name": generator_name, "parameters": parameters}

    @model_validator(mode="after")
    def validate_generator_logic(self):
        """
        Validate generator existence and parameter consistency.

        Checks whether:
        - generator exists among AbstractRVSGenerator subclasses
        - number of provided parameters matches constructor signature

        Returns
        -------
        Alternative
            Validated instance.

        Raises
        ------
        ValueError
            If generator is not found or parameter count mismatches.
        """
        generator_by_name: dict[str, type[AbstractRVSGenerator]] = {
            gen_cls.__name__.upper(): gen_cls for gen_cls in AbstractRVSGenerator.__subclasses__()
        }

        generator_cls = generator_by_name.get(self.generator_name.upper())
        if not generator_cls:
            available_generators = ", ".join(generator_by_name.keys())
            raise ValueError(
                f"Generator '{self.generator_name}' is not found.\n Available generators are: [{available_generators}]"
            )

        base_params = set(inspect.signature(AbstractRVSGenerator.__init__).parameters.keys())

        sig = inspect.signature(generator_cls.__init__)

        unique_param_names = [p.name for p in sig.parameters.values() if p.name not in base_params and p.name != "self"]

        if len(self.parameters) != len(unique_param_names):
            expected_params = ", ".join(unique_param_names)
            raise ValueError(
                f"Generator '{self.generator_name}' expects {len(unique_param_names)} "
                f"unique parameters ({expected_params}), "
                f"but received {len(self.parameters)}."
            )
        return self


class AlternativesConfig(BaseModel):
    """
    Container for multiple alternative hypotheses.

    Ensures that alternative hypotheses are only defined for supported
    experiment types (e.g., POWER analysis).

    Attributes
    ----------
    experiment_type : ExperimentType
        Type of experiment controlling whether alternatives are allowed.
    alternatives : list[Alternative]
        List of alternative hypothesis definitions.

    Raises
    ------
    ValueError
        If alternatives are provided for unsupported experiment types.
    """

    experiment_type: ExperimentType
    alternatives: list[Alternative] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_alternatives_are_allowed(self) -> "AlternativesConfig":
        """
        Ensure alternatives are allowed for selected experiment type.

        Alternatives are only valid for POWER experiments.

        Returns
        -------
        AlternativesConfig
            Validated configuration.

        Raises
        ------
        ValueError
            If alternatives are used with unsupported experiment type.
        """
        if self.experiment_type != ExperimentType.POWER and self.alternatives:
            raise ValueError(f"Alternatives are not supported for the experiment type '{self.experiment_type.value}'.")
        return self


# TODO: check warning decorators
