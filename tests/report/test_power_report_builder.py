import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.report.power.power import PowerReportBuilder


class TestPowerReportBuilder:
    def test_init_stores_attributes_correctly(
        self, mock_criterion_config, mock_alternative, power_data, results_path, with_chart
    ):
        criteria = [mock_criterion_config, MagicMock(criterion_code="AD_")]
        sample_sizes = [10, 20]
        alternatives = [mock_alternative]
        significance_levels = [0.05, 0.01]

        builder = PowerReportBuilder(
            criteria_config=criteria,
            sample_sizes=sample_sizes,
            alternatives=alternatives,
            significance_levels=significance_levels,
            power_result=power_data,
            results_path=results_path,
            with_chart=with_chart,
        )

        assert builder.criteria_config == criteria
        assert builder.sample_sizes == sample_sizes
        assert builder.alternatives == alternatives
        assert builder.significance_levels == significance_levels
        assert builder.power_result == power_data
        assert builder.results_path == results_path
        assert builder.with_chart == with_chart
        assert builder.pdf_path == results_path / "power_report.pdf"

    def test_generate_table_data_has_correct_structure_and_values(
        self, mock_criterion_config, mock_alternative, power_data, results_path
    ):
        mock_criterion_config_ad = MagicMock()
        mock_criterion_config_ad.criterion_code = "AD_"

        builder = PowerReportBuilder(
            criteria_config=[mock_criterion_config, mock_criterion_config_ad],
            sample_sizes=[10, 20],
            alternatives=[mock_alternative],
            significance_levels=[0.05],
            power_result=power_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        table_data = builder._generate_table_data(mock_alternative, 0.05)

        assert len(table_data) == 2
        assert 10 in table_data
        assert 20 in table_data

        row_size_10 = table_data[10]

        assert "KS" in row_size_10
        assert "AD" in row_size_10

        assert row_size_10["KS"] == pytest.approx(2 / 3, 0.01)
        assert row_size_10["AD"] == pytest.approx(0.0, 0.01)

        row_size_20 = table_data[20]

        assert "KS" in row_size_20
        assert "AD" in row_size_20

        assert row_size_20["KS"] == pytest.approx(2 / 3, 0.01)
        assert row_size_20["AD"] == pytest.approx(1 / 3, 0.01)

    @patch("pysatl_experiment.report.power.power.plt.savefig")
    @patch("pysatl_experiment.report.power.power.plt.close")
    def test_generate_chart_data_creates_file_and_returns_path(
        self,
        mock_close,
        mock_savefig,
        mock_criterion_config,
        mock_alternative,
        power_data,
        results_path,
    ):
        builder = PowerReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            alternatives=[mock_alternative],
            significance_levels=[0.05],
            power_result=power_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            charts_dir = Path(temp_dir)
            chart_path = charts_dir / "test_chart.png"

            with (
                patch.object(Path, "resolve", return_value=chart_path),
                patch.object(Path, "as_posix", return_value=str(chart_path)),
            ):
                result_path = builder._generate_chart_data(mock_alternative, 0.05, charts_dir)

                mock_savefig.assert_called_once()
                assert isinstance(result_path, str)
                assert result_path == str(chart_path)

    @pytest.mark.parametrize("chart_mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
    @patch("pysatl_experiment.report.power.power.convert_html_to_pdf")
    def test_build_calls_convert_html_to_pdf(
        self,
        mock_convert,
        mock_criterion_config,
        mock_alternative,
        power_data,
        chart_mode,
        results_path,
    ):
        builder = PowerReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10],
            alternatives=[mock_alternative],
            significance_levels=[0.05],
            power_result=power_data,
            results_path=results_path,
            with_chart=chart_mode,
        )

        with patch.object(builder, "_generate_html", return_value="<html></html>"):
            builder.build()

        mock_convert.assert_called_once()
