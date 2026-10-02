"""Critical-value calculation belongs to the builder, which consumes raw distributions."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from pysatl_experiment.experiment_execution.step.report_step import ReportBuilderContext
from pysatl_experiment.experiment_execution.step.report_step.critical_value import critical_value_report_builder
from pysatl_experiment.experiment_execution.step.report_step.critical_value.critical_value_report_builder import (
    CriticalValueReportBuilder,
)
from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionModel
from pysatl_experiment.types import ReportMode
from pysatl_experiment.utils.report_utils import get_report_template_dir


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    criterion = SimpleNamespace(
        criterion_code="KS", criterion=SimpleNamespace(parameters={}), statistics_class_object=Mock()
    )
    calculator = Mock()
    calculator.calculate.side_effect = lambda distribution, alpha: max(distribution) + alpha
    factory = Mock()
    factory.get_critical_value_calculator.return_value = calculator
    monkeypatch.setattr(
        critical_value_report_builder.AbstractAlternativeFactory, "get_concrete_factory", Mock(return_value=factory)
    )
    builder = CriticalValueReportBuilder([criterion], [20, 10], [0.05, 0.1])
    row = LimitDistributionModel("experiment", "KS", {}, 10, 2, [1.0, 2.0])
    context = ReportBuilderContext(
        "critical",
        ReportMode.WITHOUT_CHART,
        tmp_path / "reports",
        get_report_template_dir() / "cv_template.html",
        (replace(row, sample_size=20, results_statistics=[3.0, 4.0]), row),
    )
    return builder, context, calculator


def test_builder_calculates_values_in_criterion_size_level_order(prepared, monkeypatch):
    builder, context, calculator = prepared
    convert = Mock()
    monkeypatch.setattr(critical_value_report_builder, "convert_html_to_pdf", convert)
    builder.build(context)
    assert calculator.calculate.call_args_list == [
        call([1.0, 2.0], 0.05),
        call([1.0, 2.0], 0.1),
        call([3.0, 4.0], 0.05),
        call([3.0, 4.0], 0.1),
    ]
    assert builder._generate_table_data("KS")["rows"] == [
        {"size": 10, "values": [2.05, 2.1]},
        {"size": 20, "values": [4.05, 4.1]},
    ]
    assert convert.call_args.args[1] == context.results_path / "critical.pdf"


@pytest.mark.parametrize("mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
def test_build_writes_pdf_and_respects_chart_mode(prepared, mode, monkeypatch):
    builder, context, _ = prepared
    chart = Mock(wraps=builder._generate_chart_data)
    monkeypatch.setattr(builder, "_generate_chart_data", chart)
    builder.build(replace(context, report_mode=mode))
    assert (context.results_path / "critical.pdf").read_bytes().startswith(b"%PDF-")
    assert chart.call_count == (1 if mode == ReportMode.WITH_CHART else 0)


def test_custom_template_and_repeated_build_use_new_context(prepared, tmp_path, monkeypatch):
    builder, context, _ = prepared
    template = tmp_path / "custom.html"
    template.write_text('{{ report_name }}:{{ tables[0].rows[0]["values"][0] }}')
    convert = Mock()
    monkeypatch.setattr(critical_value_report_builder, "convert_html_to_pdf", convert)
    builder.build(replace(context, template_path=template))
    builder.build(
        replace(
            context,
            template_path=template,
            report_name="second",
            data=tuple(replace(row, results_statistics=[5.0]) for row in context.data),
        )
    )
    assert convert.call_args_list[0].args[0] == "critical:2.05"
    assert convert.call_args_list[1].args[0] == "second:5.05"


@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_ambiguous_or_missing_distribution_fails_before_output(prepared, change):
    builder, context, _ = prepared
    data = context.data[:1] if change == "missing" else (*context.data, context.data[0])
    with pytest.raises(ValueError, match="Expected one limit distribution"):
        builder.build(replace(context, data=data))
    assert not context.results_path.exists()


def test_chart_is_a_real_png(prepared, tmp_path):
    builder, context, _ = prepared
    builder.build(context)
    path = builder._generate_chart_data("KS", tmp_path)
    assert Path(path).read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a"))
