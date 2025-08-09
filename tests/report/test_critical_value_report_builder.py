from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.report.critical_value.critical_value import CriticalValueReportBuilder


class TestCriticalValueReportBuilder:
    @patch("pysatl_experiment.report.critical_value.critical_value.plt")
    def test_chunk_cv_values_splits_correctly(self, mock_criterion_config, cv_values):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config, MagicMock(criterion_code="AD_")],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=cv_values,
            results_path=MagicMock(),
            with_chart=ReportMode.WITH_CHART,
        )
        result = builder._chunk_cv_values()
        assert len(result) == 2
        assert all(len(chunk) == 4 for chunk in result)

    @patch("pysatl_experiment.report.critical_value.critical_value.plt")
    def test_chunk_cv_values_empty(self, mock_criterion_config):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=[],
            results_path=MagicMock(),
            with_chart=ReportMode.WITH_CHART,
        )
        assert builder._chunk_cv_values() == []

    @pytest.mark.parametrize("chart_mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
    @patch("pysatl_experiment.report.critical_value.critical_value.convert_html_to_pdf")
    def test_build_calls_convert(self, mock_convert, mock_criterion_config, cv_values, chart_mode, results_path):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config, MagicMock(criterion_code="AD_")],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=cv_values,
            results_path=results_path,
            with_chart=chart_mode,
        )
        builder.build()
        mock_convert.assert_called_once()

    @patch("pysatl_experiment.report.critical_value.critical_value.plt")
    def test_build_with_chart_calls_savefig(self, mock_plt, mock_criterion_config, cv_values, results_path):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config, MagicMock(criterion_code="AD_")],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=cv_values,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )
        builder.build()
        mock_plt.savefig.assert_called()

    @patch("pysatl_experiment.report.critical_value.critical_value.plt")
    def test_build_no_chart_skips_plot(self, mock_plt, mock_criterion_config, cv_values, results_path):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config, MagicMock(criterion_code="AD_")],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=cv_values,
            results_path=results_path,
            with_chart=ReportMode.WITHOUT_CHART,
        )
        builder.build()
        mock_plt.savefig.assert_not_called()

    def test_generate_table_data_has_correct_rows(self, mock_criterion_config, cv_values, results_path):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=cv_values,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )
        data = builder._generate_table_data("KS_")
        assert len(data["rows"]) == 2

    def test_generate_table_data_has_correct_values(self, mock_criterion_config, cv_values, results_path):
        builder = CriticalValueReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            significance_levels=[0.05, 0.01],
            cv_values=cv_values,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )
        data = builder._generate_table_data("KS_")
        assert len(data["rows"][0]["values"]) == 2
