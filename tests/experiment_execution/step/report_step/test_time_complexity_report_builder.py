"""Prepared report contexts render templates and PDFs without storage access."""

import base64
from dataclasses import replace
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.step.report_step import ReportBuilderContext
from pysatl_experiment.experiment_execution.step.report_step.time_complexity import (
    time_complexity_report_builder,
)
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder import (
    TimeComplexityReportBuilder,
)
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_series import (
    TimeComplexityReportSeries,
)
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel
from pysatl_experiment.types import ReportMode
from pysatl_experiment.utils.report_utils import get_report_template_dir


@pytest.fixture
def context(tmp_path):
    row = TimeComplexityModel("experiment", "KS", {"location": 1, "scale": 2}, 10, 2, [0.001, 0.003], "normal")
    return ReportBuilderContext(
        report_name="timing",
        report_mode=ReportMode.WITHOUT_CHART,
        results_path=tmp_path / "reports",
        template_path=get_report_template_dir() / "tc_template.html",
        data=(row,),
    )


def test_statistics_keep_source_parameters_and_repetition_count_separate(context):
    first = context.data[0]
    second_size = replace(
        first, criterion_parameters={"scale": 2.0, "location": 1.0}, sample_size=20, results_times=[0.004, 0.006]
    )
    different_parameters = replace(first, criterion_parameters={"location": 2, "scale": 2})
    different_source = replace(first, generator_code="laplace")
    different_count = replace(first, samples_count=3, results_times=[0.001, 0.002, 0.003])
    rows = (different_count, second_size, different_parameters, different_source, first)
    statistic = TimeComplexityReportBuilder()._collect_statistics(rows)
    assert len(statistic.values) == 4
    points = statistic.values[TimeComplexityReportSeries.from_result(first)]
    assert [size for size, _ in points] == [10, 20]
    assert [mean for _, mean in points] == pytest.approx([0.002, 0.005])
    assert list(statistic.as_dict()) == sorted(statistic.values)
    assert len({series.label for series in statistic.values}) == 4


def test_generate_chart_returns_actual_png(context):
    builder = TimeComplexityReportBuilder()
    image = builder._generate_chart(builder._collect_statistics(context.data))
    assert image.startswith("data:image/png;base64,")
    assert base64.b64decode(image.partition(",")[2]).startswith(bytes.fromhex("89504e470d0a1a0a"))


@pytest.mark.parametrize("mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
def test_selected_template_receives_loaded_data_and_optional_chart(context, tmp_path, monkeypatch, mode):
    (tmp_path / "title.html").write_text("<h1>{{ report_name }}</h1>")
    template = tmp_path / "custom.html"
    template.write_text(
        '<html>{% include "title.html" %}{{ data[0].generator_code }};'
        '{{ sizes | join(",") }};{{ plot_image or "no chart" }}</html>'
    )
    context = replace(context, template_path=template, report_mode=mode, report_name="<custom>")
    builder = TimeComplexityReportBuilder()
    chart = Mock(return_value="data:image/png;base64,chart")
    monkeypatch.setattr(builder, "_generate_chart", chart)
    html = builder._generate_html(context, builder._collect_statistics(context.data))
    assert "<h1>&lt;custom&gt;</h1>normal;10;" in html
    if mode == ReportMode.WITH_CHART:
        chart.assert_called_once()
        assert "data:image/png;base64,chart" in html
    else:
        chart.assert_not_called()
        assert "no chart" in html


def test_chart_failure_preserves_table_report(context, monkeypatch, caplog):
    builder = TimeComplexityReportBuilder()
    monkeypatch.setattr(builder, "_generate_chart", Mock(side_effect=RuntimeError("chart failed")))
    html = builder._generate_html(
        replace(context, report_mode=ReportMode.WITH_CHART), builder._collect_statistics(context.data)
    )
    assert "2.00 ms" in html
    assert "<img" not in html
    assert "Failed to generate time complexity chart" in caplog.text


@pytest.mark.parametrize("mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
def test_build_writes_real_pdf(context, mode):
    context = replace(context, report_mode=mode)
    TimeComplexityReportBuilder().build(context)
    pdf = context.results_path / "timing.pdf"
    assert pdf.read_bytes().startswith(b"%PDF-")


def test_builder_can_be_reused_without_retaining_previous_report(context, monkeypatch):
    outputs = []
    monkeypatch.setattr(
        time_complexity_report_builder, "convert_html_to_pdf", lambda html, path: outputs.append((html, path))
    )
    builder = TimeComplexityReportBuilder()
    builder.build(context)
    builder.build(replace(context, report_name="second", data=(replace(context.data[0], generator_code="laplace"),)))
    assert "normal" in outputs[0][0] and "laplace" not in outputs[0][0]
    assert "laplace" in outputs[1][0] and "normal" not in outputs[1][0]
    assert outputs[1][1] == context.results_path / "second.pdf"


def test_empty_measurements_and_pdf_failures_are_reported(context, monkeypatch):
    builder = TimeComplexityReportBuilder()
    with pytest.raises(ValueError, match="Empty timing measurements"):
        builder.build(replace(context, data=(replace(context.data[0], results_times=[]),)))
    monkeypatch.setattr(
        time_complexity_report_builder, "convert_html_to_pdf", Mock(side_effect=RuntimeError("PDF failed"))
    )
    with pytest.raises(RuntimeError, match="PDF failed"):
        builder.build(context)
