"""Power builders calculate statistics from raw results and honor output settings."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.step.report_step import ReportBuilderContext
from pysatl_experiment.experiment_execution.step.report_step.power import power_report_builder
from pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder import PowerReportBuilder
from pysatl_experiment.persistence.models.power import PowerModel
from pysatl_experiment.types import ReportMode
from pysatl_experiment.utils.report_utils import get_report_template_dir


@pytest.fixture
def prepared(tmp_path):
    criterion = SimpleNamespace(criterion_code="KS_normal")
    alternative = SimpleNamespace(distribution_type="normal", parameters=[0, 1])
    builder = PowerReportBuilder([criterion], [20, 10], [0.05], [alternative])
    row = PowerModel("experiment", "KS_normal", {}, 10, "normal", [0, 1], 3, 0.05, [True, False, True])
    context = ReportBuilderContext(
        "power",
        ReportMode.WITHOUT_CHART,
        tmp_path / "reports",
        get_report_template_dir() / "power_template.html",
        (row, replace(row, sample_size=20, results_criteria=[False, False, True])),
    )
    return builder, context


def test_build_calculates_power_from_loaded_results(prepared, monkeypatch):
    builder, context = prepared
    convert = Mock()
    monkeypatch.setattr(power_report_builder, "convert_html_to_pdf", convert)
    builder.build(context)
    table = builder._generate_table_data(builder.alternatives[0], 0.05)
    assert table == {10: {"KS": 0.667}, 20: {"KS": 0.333}}
    convert.assert_called_once()
    assert convert.call_args.args[1] == context.results_path / "power.pdf"


@pytest.mark.parametrize("mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
def test_build_writes_pdf_and_respects_chart_mode(prepared, mode, monkeypatch):
    builder, context = prepared
    chart = Mock(wraps=builder._generate_chart_data)
    monkeypatch.setattr(builder, "_generate_chart_data", chart)
    builder.build(replace(context, report_mode=mode))
    assert (context.results_path / "power.pdf").read_bytes().startswith(b"%PDF-")
    assert chart.call_count == (1 if mode == ReportMode.WITH_CHART else 0)


def test_custom_template_and_repeated_build_use_new_context(prepared, tmp_path, monkeypatch):
    builder, context = prepared
    template = tmp_path / "custom.html"
    template.write_text('{{ report_name }}:{{ tables[0].table[10]["KS"] }}')
    convert = Mock()
    monkeypatch.setattr(power_report_builder, "convert_html_to_pdf", convert)
    builder.build(replace(context, template_path=template))
    second = replace(
        context,
        report_name="second",
        template_path=template,
        data=tuple(replace(row, results_criteria=[False]) for row in context.data),
    )
    builder.build(second)
    assert convert.call_args_list[0].args[0] == "power:0.667"
    assert convert.call_args_list[1].args[0] == "second:0.0"
    assert convert.call_args_list[1].args[1] == context.results_path / "second.pdf"


def test_chart_is_a_real_png(prepared, tmp_path):
    builder, context = prepared
    builder.build(context)
    path = builder._generate_chart_data(builder.alternatives[0], 0.05, tmp_path)
    assert Path(path).read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a"))
