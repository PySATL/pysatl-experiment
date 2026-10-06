"""Tests for the statistical criterion validation schema."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError
from pysatl_criterion import DistributionType

from pysatl_experiment.cli.validation.schemas.criteria import CriteriaConfig, Criterion


# Checks that a criterion code is normalized to uppercase.
@pytest.mark.parametrize(
    ("raw_code", "expected"),
    [
        pytest.param("ks", "KS", id="lowercase"),
        pytest.param("Ks", "KS", id="mixed-case"),
        pytest.param("KS", "KS", id="already-upper"),
    ],
)
def test_criterion_code_is_uppercased(raw_code: str, expected: str) -> None:
    assert Criterion(criterion_code=raw_code).criterion_code == expected


# Checks that the parameters field defaults to an empty list.
def test_criterion_parameters_default_to_empty_list() -> None:
    assert Criterion(criterion_code="KS").parameters == []


# Checks that the parameters default is not shared between instances.
def test_criterion_parameters_default_is_not_shared() -> None:
    first = Criterion(criterion_code="KS")
    second = Criterion(criterion_code="AD")

    first.parameters.append(1.0)

    assert second.parameters == []


# Checks that explicit criterion parameters are preserved.
def test_criterion_keeps_explicit_parameters() -> None:
    assert Criterion(criterion_code="KS", parameters=[0.5, 1.0]).parameters == [0.5, 1.0]


# Checks that a criterion code is required.
def test_criterion_code_is_required() -> None:
    with pytest.raises(ValidationError):
        Criterion()  # type: ignore[call-arg]


# Checks that criteria compatible with the hypothesis are accepted.
@patch(
    "pysatl_experiment.cli.validation.schemas.criteria.get_statistics_short_codes_for_hypothesis",
    return_value=["KS", "AD"],
)
def test_criteria_config_accepts_compatible_criteria(get_codes) -> None:
    config = CriteriaConfig(
        hypothesis=DistributionType.NORMAL,
        criteria=[Criterion(criterion_code="ks"), Criterion(criterion_code="AD")],
    )

    assert [criterion.criterion_code for criterion in config.criteria] == ["KS", "AD"]
    get_codes.assert_called_once_with(DistributionType.NORMAL.value)


# Checks that a criterion incompatible with the hypothesis is rejected.
@patch(
    "pysatl_experiment.cli.validation.schemas.criteria.get_statistics_short_codes_for_hypothesis",
    return_value=["KS"],
)
def test_criteria_config_rejects_incompatible_criterion(get_codes) -> None:
    with pytest.raises(ValidationError, match="are incompatible with hypothesis"):
        CriteriaConfig(hypothesis=DistributionType.NORMAL, criteria=[Criterion(criterion_code="TT")])


# Checks that a hypothesis without any known codes is reported clearly.
@patch(
    "pysatl_experiment.cli.validation.schemas.criteria.get_statistics_short_codes_for_hypothesis",
    return_value=[],
)
def test_criteria_config_rejects_hypothesis_without_codes(get_codes) -> None:
    with pytest.raises(ValidationError, match="No matching values were found for hypothesis"):
        CriteriaConfig(hypothesis=DistributionType.NORMAL, criteria=[Criterion(criterion_code="KS")])


# Checks that validation is skipped when the hypothesis was not supplied.
def test_criteria_validator_skips_check_without_hypothesis() -> None:
    with pytest.raises(ValidationError):
        CriteriaConfig.model_validate({"criteria": [{"criterion_code": "ANY"}]})
