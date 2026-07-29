"""Common utilities for CLI commands and experiment management."""

from typing import cast, overload

from pysatl_criterion import DistributionType
from pysatl_criterion.utils.statistic import get_available_criteria


# TODO: Split utilities into dedicated modules?


@overload
def get_statistics_short_codes_for_hypothesis(hypothesis: str) -> list[str]: ...


@overload
def get_statistics_short_codes_for_hypothesis(hypothesis: list[str]) -> dict[str, list[str]]: ...


@overload
def get_statistics_short_codes_for_hypothesis(hypothesis: None) -> dict[str, list[str]]: ...


def get_statistics_short_codes_for_hypothesis(hypothesis: str | list[str] | None) -> list[str] | dict[str, list[str]]:
    """
    Get short codes of registered goodness-of-fit statistics.

    Parameters
    ----------
    hypothesis : str
        Hypothesis identifier.

    Returns
    -------
    list[str]
        List of short statistic codes (e.g., ``["KS", "AD"]``).
    """
    if hypothesis is None or isinstance(hypothesis, list):
        return {member.value: get_statistics_short_codes_for_hypothesis(member.value) for member in DistributionType}

    valid_criteria_types = get_available_criteria(DistributionType(hypothesis))

    valid_criteria_codes = [
        cls.short_code() for cls in valid_criteria_types if not getattr(cls, "__abstractmethods__", None)
    ]

    return valid_criteria_codes


def criteria_from_codes(codes: list[str]) -> list[dict]:
    """
    Convert criterion short codes into criterion data    dictionaries.

    Parameters
    ----------
    codes : list[str]
        List of criterion short codes (e.g., ``["KS", "AD"]``).

    Returns
    -------
    list[dict]
        List of dictionaries, each containing ``"criterion_code"`` and an
        empty ``"parameters"`` list.
    """
    criteria_data = []
    for code in codes:
        criterion = {"criterion_code": code, "parameters": []}
        criteria_data.append(criterion)

    return criteria_data
