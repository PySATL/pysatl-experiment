"""The common step accepts any iterable and finishes reading before rendering."""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.step.report_step import ReportBuildingStep, ReportStepContext
from pysatl_experiment.persistence.query_results import QueryResults
from pysatl_experiment.types import ReportMode


@pytest.fixture
def context(tmp_path):
    return ReportStepContext("report", ReportMode.WITHOUT_CHART, tmp_path / "output", tmp_path / "custom.html")


@pytest.mark.parametrize("rows", [(), (1, 2, 3)])
def test_step_only_requires_iterable_and_passes_complete_context(context, rows):
    builder = Mock()
    step = ReportBuildingStep(context, iter(rows), builder)
    step.run()
    builder.build.assert_called_once()
    prepared = builder.build.call_args.args[0]
    assert prepared.data == rows
    assert prepared.report_name == context.report_name
    assert prepared.report_mode == context.report_mode
    assert prepared.results_path == context.results_path == step.results_path
    assert prepared.template_path == context.template_path
    assert not context.results_path.exists()


def test_late_iteration_failure_never_calls_builder(context):
    def rows():
        yield 1
        raise RuntimeError("read failed")

    builder = Mock()
    with pytest.raises(RuntimeError, match="read failed"):
        ReportBuildingStep(context, rows(), builder).run()
    builder.build.assert_not_called()
    assert not context.results_path.exists()


def test_query_source_is_repeatable_and_reads_current_results(context):
    storage = Mock()
    storage.get_data.side_effect = [1, 2, 3, 4]
    builder = Mock()
    source = QueryResults(storage, ["first", "second"])
    step = ReportBuildingStep(context, source, builder)
    step.run()
    step.run()
    assert [call.args[0].data for call in builder.build.call_args_list] == [(1, 2), (3, 4)]
    assert [call.args[0] for call in storage.get_data.call_args_list] == ["first", "second"] * 2


def test_missing_query_result_prevents_building(context):
    storage = Mock()
    storage.get_data.side_effect = [1, None]
    builder = Mock()
    with pytest.raises(ValueError, match="Missing report result: second"):
        ReportBuildingStep(context, QueryResults(storage, ["first", "second"]), builder).run()
    builder.build.assert_not_called()


def test_empty_query_source_does_not_read_storage(context):
    storage = Mock()
    builder = Mock()
    ReportBuildingStep(context, QueryResults(storage, ()), builder).run()
    storage.get_data.assert_not_called()
    assert builder.build.call_args.args[0].data == ()


def test_context_validates_report_name(context):
    with pytest.raises(ValueError, match="report_name"):
        replace(context, report_name="")
