"""Report steps load complete selections through paginated storage contracts."""

from dataclasses import asdict, replace
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.step.report_step import ReportBuildingStep, ReportStepContext
from pysatl_experiment.experiment_execution.step.report_step.abstract_report_builder import IReportBuilder
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel, TimeComplexityQuery
from pysatl_experiment.persistence.sqlalchemy.time_complexity import AlchemyTimeComplexityStorage
from pysatl_experiment.persistence.time_complexity_results import TimeComplexityResults
from pysatl_experiment.types import ReportMode


def timing(**changes):
    row = TimeComplexityModel("experiment", "KS", {"zeta": 2.0, "alpha": 1.0}, 10, 2, [0.1, 0.2], "normal")
    return replace(row, **changes)


def query(row):
    values = asdict(row)
    values.pop("results_times")
    return TimeComplexityQuery(**values)


@pytest.fixture
def context(tmp_path):
    return ReportStepContext(
        report_name="timing",
        report_mode=ReportMode.WITHOUT_CHART,
        results_path=tmp_path / "reports",
        template_path=tmp_path / "template.html",
    )


@pytest.fixture
def storage():
    result = AlchemyTimeComplexityStorage("sqlite:///:memory:")
    result.init()
    return result


def test_step_pages_filters_and_passes_loaded_data_to_injected_builder(context, storage):
    first = timing()
    second = timing(criterion_parameters={"alpha": 3.0})
    third = timing(generator_code="laplace")
    requested = (first, second, third)
    unrelated = [
        timing(experiment_name="other"),
        timing(sample_size=20),
        timing(samples_count=3),
        timing(criterion_code="AD"),
        timing(generator_code="other"),
    ]
    storage.bulk_insert([*unrelated, third, second, first])
    expected = [query(row) for row in requested]
    expected[0] = replace(expected[0], criterion_parameters={"alpha": 1, "zeta": 2})
    observed = Mock(wraps=storage)
    source = TimeComplexityResults(observed, "experiment", reversed(expected), read_batch_size=2)
    builder = Mock(spec=IReportBuilder)
    step = ReportBuildingStep(context, source, builder)
    step.run()
    builder.build.assert_called_once()
    prepared = builder.build.call_args.args[0]
    assert prepared.report_name == context.report_name
    assert prepared.report_mode == context.report_mode
    assert prepared.template_path == context.template_path
    assert prepared.results_path == context.results_path
    assert len(prepared.data) == 3
    assert list(prepared.data) == sorted(requested, key=source._result_key)
    assert observed.read_bulk.call_count >= 3
    assert all(call.kwargs["batch_size"] == 2 for call in observed.read_bulk.call_args_list)
    assert all(call.args[0].experiment_name == "experiment" for call in observed.read_bulk.call_args_list)
    observed.get_data.assert_not_called()
    assert not context.results_path.exists()


def test_missing_result_prevents_building_and_identifies_selection(context, storage):
    storage.bulk_insert([timing()])
    missing = query(timing(generator_code="missing-series", sample_size=20))
    source = TimeComplexityResults(storage, "experiment", (query(timing()), missing))
    builder = Mock(spec=IReportBuilder)
    with pytest.raises(ValueError, match="Missing time complexity results") as error:
        ReportBuildingStep(context, source, builder).run()
    assert "missing-series" in str(error.value) and "sample_size=20" in str(error.value)
    builder.build.assert_not_called()
    assert not context.results_path.exists()


def test_empty_selection_does_not_read_storage(context):
    storage = Mock()
    builder = Mock(spec=IReportBuilder)
    ReportBuildingStep(context, TimeComplexityResults(storage, "experiment", ()), builder).run()
    storage.read_bulk.assert_not_called()
    assert builder.build.call_args.args[0].data == ()


def test_storage_failure_propagates_before_building(context):
    storage = Mock()
    storage.read_bulk.side_effect = RuntimeError("Read failed")
    source = TimeComplexityResults(storage, "experiment", (query(timing()),))
    builder = Mock(spec=IReportBuilder)
    with pytest.raises(RuntimeError, match="Read failed"):
        ReportBuildingStep(context, source, builder).run()
    builder.build.assert_not_called()


@pytest.mark.parametrize("size", [0, -1, True, 1.5])
def test_context_rejects_invalid_page_size(context, size):
    with pytest.raises(ValueError, match="read_batch_size"):
        TimeComplexityResults(Mock(), "experiment", (), read_batch_size=size)


def test_context_rejects_queries_for_other_experiments(context):
    with pytest.raises(ValueError, match="belong"):
        TimeComplexityResults(Mock(), "experiment", (query(timing(experiment_name="other")),))


def test_duplicate_selected_result_prevents_building(context):
    from pysatl_experiment.persistence.models.bulk import BulkBatch

    storage = Mock()
    storage.read_bulk.return_value = BulkBatch(items=[timing(), timing()], next_after_id=None)
    source = TimeComplexityResults(storage, "experiment", (query(timing()),))
    builder = Mock()
    with pytest.raises(ValueError, match="Duplicate time complexity result"):
        ReportBuildingStep(context, source, builder).run()
    builder.build.assert_not_called()


def test_timing_source_reloads_results_on_each_run(context, storage):
    storage.bulk_insert([timing()])
    source = TimeComplexityResults(storage, "experiment", (query(timing()),))
    builder = Mock()
    step = ReportBuildingStep(context, source, builder)
    step.run()
    storage.bulk_insert([timing(results_times=[1.0, 2.0])])
    step.run()
    assert builder.build.call_args_list[0].args[0].data[0].results_times == [0.1, 0.2]
    assert builder.build.call_args_list[1].args[0].data[0].results_times == [1.0, 2.0]
