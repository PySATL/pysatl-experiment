"""Tests for report template directory resolution."""

from pathlib import Path

import pytest

from pysatl_experiment.utils.report_utils import get_report_template_dir


# Checks that the template directory does not depend on the current working directory.
def test_get_report_template_dir_is_independent_of_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    template_dir = get_report_template_dir()

    assert template_dir.is_absolute()
    assert template_dir.is_dir()
    assert template_dir.name == "report_templates"


# Checks that all bundled report templates are discoverable from any working directory.
def test_get_report_template_dir_contains_bundled_templates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    template_dir = get_report_template_dir()

    assert {path.name for path in template_dir.glob("*.html")} >= {
        "cv_template.html",
        "power_template.html",
        "tc_template.html",
    }
