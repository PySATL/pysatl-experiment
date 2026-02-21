from pydantic import BaseModel, Field, ValidationInfo, field_validator

from pysatl_experiment.cli.commands.common.common import get_statistics_short_codes_for_hypothesis
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


class Criterion(BaseModel):
    """
    Represents a single statistical criterion.

    A criterion is defined by its unique code (which is automatically
    converted to uppercase) and an optional list of parameters.

    Attributes:
        criterion_code (str): The short code identifying the criterion (e.g., "KS", "AD").
        parameters (list): An optional list of parameters for the criterion.
    """

    criterion_code: str
    parameters: list = Field(default_factory=list)

    @field_validator("criterion_code", mode="before")
    @classmethod
    def code_to_upper(cls, v: str) -> str:
        return v.upper()


class CriteriaConfig(BaseModel):
    """
    A configuration container for a list of criteria.

    This model validates that all specified criteria are compatible with the
    given statistical hypothesis. It dynamically fetches the allowed
    criterion codes for the hypothesis and raises an error if any of the
    provided criteria are not in the allowed list.

    Attributes:
        hypothesis (Hypothesis): The hypothesis against which the criteria are tested.
        criteria (list[Criterion]): A list of criteria to be used in the experiment.
    """

    hypothesis: Hypothesis
    criteria: list[Criterion]

    @field_validator("criteria")
    @classmethod
    def criteria_must_be_compatible_with_hypothesis(
        cls, criteria_list: list[Criterion], info: ValidationInfo
    ) -> list[Criterion]:
        if "hypothesis" not in info.data:
            return criteria_list

        hypothesis = info.data["hypothesis"]
        valid_codes = get_statistics_short_codes_for_hypothesis(hypothesis.value)

        if not valid_codes:
            raise ValueError(f"No matching values were found for hypothesis '{hypothesis.value}'.")

        invalid_codes = [crit.criterion_code for crit in criteria_list if crit.criterion_code not in valid_codes]

        if invalid_codes:
            raise ValueError(
                f"Criteria '{', '.join(invalid_codes)}' are incompatible with hypothesis '{hypothesis.value}'.\n"
                f"Valid codes: {', '.join(valid_codes)}"
            )

        return criteria_list
