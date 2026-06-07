"""
Criterion configuration and validation utilities.

This module defines statistical criteria and validates their compatibility
with a given hypothesis.
"""

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from pysatl_experiment.cli.commands.common import get_statistics_short_codes_for_hypothesis
from pysatl_experiment.configuration.model.hypothesis import Hypothesis


class Criterion(BaseModel):
    """
    Single statistical criterion definition.

    A criterion represents a statistical test identified by a unique code
    and optional parameters.

    Attributes
    ----------
    criterion_code : str
        Identifier of the criterion (automatically converted to uppercase).
    parameters : list
        Optional parameters for the criterion.

    Notes
    -----
    Criterion codes are normalized to uppercase during validation.
    """

    criterion_code: str
    parameters: list = Field(default_factory=list)

    @field_validator("criterion_code", mode="before")
    @classmethod
    def code_to_upper(cls, v: str) -> str:
        """
        Normalize criterion code to uppercase.

        Parameters
        ----------
        v : str
            Input criterion code.

        Returns
        -------
        str
            Uppercased criterion code.
        """
        return v.upper()


class CriteriaConfig(BaseModel):
    """
    Container for a set of statistical criteria.

    Validates that all criteria are compatible with the selected hypothesis.
    Compatibility is determined dynamically via supported criterion codes.

    Attributes
    ----------
    hypothesis : Hypothesis
        Statistical hypothesis defining allowed criteria.
    criteria : list[Criterion]
        List of statistical criteria used in the experiment.

    Raises
    ------
    ValueError
        If any criterion is incompatible with the hypothesis or no valid
        criteria exist for the hypothesis.
    """

    hypothesis: Hypothesis
    criteria: list[Criterion]

    @field_validator("criteria")
    @classmethod
    def criteria_must_be_compatible_with_hypothesis(
        cls, criteria_list: list[Criterion], info: ValidationInfo
    ) -> list[Criterion]:
        """
        Validate compatibility between criteria and hypothesis.

        Ensures that all provided criteria are supported by the selected
        statistical hypothesis.

        Parameters
        ----------
        criteria_list : list[Criterion]
            List of criteria to validate.
        info : ValidationInfo
            Pydantic validation context containing hypothesis.

        Returns
        -------
        list[Criterion]
            Validated list of criteria.

        Raises
        ------
        ValueError
            If incompatible criteria are found or hypothesis has no valid codes.
        """
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
