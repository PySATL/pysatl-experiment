"""Tests for report generation utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.configuration.criteria_config import CriterionConfig
from pysatl_experiment.utils.report_utils import convert_html_to_pdf, get_criterion_names, get_report_template_dir


# Checks that well-formed HTML is rendered into a non-empty PDF file.
def test_convert_html_to_pdf_writes_non_empty_pdf(tmp_path: Path) -> None:
    output_path = tmp_path / "report.pdf"

    convert_html_to_pdf("<html><body><h1>Report</h1><p>Body</p></body></html>", output_path)

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")


# Checks that overwriting an existing target file succeeds.
def test_convert_html_to_pdf_overwrites_existing_file(tmp_path: Path) -> None:
    output_path = tmp_path / "report.pdf"
    output_path.write_bytes(b"stale content")

    convert_html_to_pdf("<html><body><p>Fresh</p></body></html>", output_path)

    assert output_path.read_bytes().startswith(b"%PDF")


# Checks that a renderer error is surfaced as a RuntimeError.
@patch("pysatl_experiment.utils.report_utils.pisa.CreatePDF")
def test_convert_html_to_pdf_raises_on_renderer_error(create_pdf: MagicMock, tmp_path: Path) -> None:
    create_pdf.return_value = MagicMock(err=1)

    with pytest.raises(RuntimeError, match="PDF generation failed: 1"):
        convert_html_to_pdf("<html></html>", tmp_path / "broken.pdf")


# Checks that criterion names are reduced to the prefix before the first underscore.
@pytest.mark.parametrize(
    ("criterion_code", "expected"),
    [
        pytest.param("KS", "KS", id="without-separator"),
        pytest.param("KS_A", "KS", id="single-separator"),
        pytest.param("KS_A_B", "KS", id="multiple-separators"),
        pytest.param("MIXED_case", "MIXED", id="mixed-case-preserved"),
        pytest.param("", "", id="empty-code"),
    ],
)
def test_get_criterion_names_extracts_code_prefix(criterion_code: str, expected: str) -> None:
    config = CriterionConfig(
        criterion=MagicMock(),
        criterion_code=criterion_code,
        statistics_class_object=MagicMock(),
    )

    assert get_criterion_names([config]) == [expected]


# Checks that criterion names keep the input order across several configurations.
def test_get_criterion_names_preserves_order() -> None:
    configs = [
        CriterionConfig(criterion=MagicMock(), criterion_code=code, statistics_class_object=MagicMock())
        for code in ("KS_A", "AD_B", "TT_C")
    ]

    assert get_criterion_names(configs) == ["KS", "AD", "TT"]


# Checks that an empty configuration list yields an empty name list.
def test_get_criterion_names_handles_empty_list() -> None:
    assert get_criterion_names([]) == []


# Checks that the template directory resolves to an existing absolute path.
def test_get_report_template_dir_resolves_existing_directory() -> None:
    template_dir = get_report_template_dir()

    assert template_dir.is_absolute()
    assert template_dir.is_dir()
    assert template_dir.name == "report_templates"
