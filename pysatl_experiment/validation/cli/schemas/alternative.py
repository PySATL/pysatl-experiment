import inspect
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType
from pysatl_experiment.experiment.generator import AbstractRVSGenerator


class Alternative(BaseModel):
    """
    Specifies an alternative hypothesis generator and its parameters.

    This model supports instantiation from a space-separated string
    (e.g., passing "MyGenerator 1.0 5.5" instead of a dictionary).

    During validation, it dynamically checks if the `generator_name` exists
    among subclasses of `AbstractRVSGenerator`. It also introspects the
    generator's `__init__` method to ensure the count of provided `parameters`
    matches the required unique arguments of that generator.

    Attributes:
        generator_name (str): The name of the generator class (case-insensitive).
        parameters (list[float]): A list of numerical parameters required by
        the generator's constructor.
    """

    generator_name: str
    parameters: list[float]

    @field_validator("generator_name")
    @classmethod
    def normalize_and_resolve_generator_name(cls, value):
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
    Configuration container for a list of alternatives.

    Ensures that alternatives are only defined for experiment types that
    support them (e.g., POWER analysis).

    Attributes:
    experiment_type (ExperimentType): The context of the current experiment.
    alternatives (list[Alternative]): The list of defined alternatives.
    Must be empty if `experiment_type` is not POWER.
    """

    experiment_type: ExperimentType
    alternatives: list[Alternative] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_alternatives_are_allowed(self):
        if self.experiment_type != ExperimentType.POWER and self.alternatives:
            raise ValueError(f"Alternatives are not supported for the experiment type '{self.experiment_type.value}'.")
        return self
