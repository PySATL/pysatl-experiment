"""Tests for power report builder."""

import tempfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.alternative import Alternative
from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder import PowerReportBuilder


BUILDER_PATH = "pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder"


def make_alternative(distribution_type: DistributionType) -> Alternative:
    """Build an alternative double exposing the attributes used by the template."""
    alternative = MagicMock()
    alternative.distribution_type = distribution_type
    alternative.generator_name = distribution_type.value
    alternative.parameters = {"mean": 0, "std": 1}
    return cast(Alternative, alternative)


class TestPowerReportBuilder:
    def test_init_stores_attributes_correctly(
        self, mock_criterion_config, mock_alternative, power_data, results_path, with_chart
    ):
        criteria = [mock_criterion_config, MagicMock(criterion_code="AD_")]
        sample_sizes = [10, 20]
        alternatives = [mock_alternative]
        significance_levels = [0.05, 0.01]

        builder = PowerReportBuilder(
            report_name="test",
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
        assert builder.pdf_path == results_path / "test.pdf"

    def test_generate_table_data_has_correct_structure_and_values(
        self, mock_criterion_config, mock_alternative, power_data, results_path
    ):
        mock_criterion_config_ad = MagicMock()
        mock_criterion_config_ad.criterion_code = "AD_"

        builder = PowerReportBuilder(
            report_name="test",
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

    @patch("pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder.plt.savefig")
    @patch("pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder.plt.close")
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
            report_name="test",
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
    @patch("pysatl_experiment.experiment_execution.step.report_step.power.power_report_builder.convert_html_to_pdf")
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
            report_name="test",
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

    # Checks that build renders a table per alternative/level pair with the stored power values.
    @patch(f"{BUILDER_PATH}.convert_html_to_pdf")
    def test_build_without_chart_renders_power_tables(
        self, mock_convert, mock_criterion_config, power_data, results_path
    ) -> None:
        criteria = [mock_criterion_config, MagicMock(criterion_code="AD_")]
        alternatives = [make_alternative(DistributionType.NORMAL), make_alternative(DistributionType.UNIFORM)]
        builder = PowerReportBuilder(
            report_name="test",
            criteria_config=criteria,
            sample_sizes=[10, 20],
            alternatives=alternatives,
            significance_levels=[0.05, 0.01],
            power_result=power_data,
            results_path=results_path,
            with_chart=ReportMode.WITHOUT_CHART,
        )

        builder.build()

        html = mock_convert.call_args.args[0]

        assert mock_convert.call_args.args[1] == results_path / "test.pdf"
        assert "Power Report" in html
        # Table header row is emitted once per alternative/level combination.
        assert html.count("<td>Test</td>") == 4
        # Criterion codes are rendered both as row labels and as short names in the cells.
        assert "<td>KS</td>" in html
        assert "<td>AD</td>" in html
        # Power values are formatted with three decimals.
        assert "<td>0.667</td>" in html
        assert "<td>0.000</td>" in html
        # Both alternatives are captioned, and no chart is embedded.
        assert "Alternative: normal" in html
        assert "Alternative: uniform" in html
        assert "<img" not in html

    # Checks that build embeds the generated chart image when charts are requested.
    @patch(f"{BUILDER_PATH}.plt.close")
    @patch(f"{BUILDER_PATH}.plt.savefig")
    @patch(f"{BUILDER_PATH}.convert_html_to_pdf")
    def test_build_with_chart_embeds_chart_image(
        self, mock_convert, mock_savefig, mock_close, mock_criterion_config, power_data, results_path
    ) -> None:
        alternative = make_alternative(DistributionType.NORMAL)
        builder = PowerReportBuilder(
            report_name="test",
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            alternatives=[alternative],
            significance_levels=[0.05],
            power_result=power_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        builder.build()

        html = mock_convert.call_args.args[0]

        mock_savefig.assert_called_once()
        assert html.count("<img") == 1
        assert 'alt="Power vs Sample Size"' in html
        assert "DistributionType.NORMAL_0.05.png" in html
        assert "<td>0.667</td>" in html

    # Checks that a failing chart generation is reported and leaves the table chart-free.
    @patch(f"{BUILDER_PATH}.convert_html_to_pdf")
    def test_build_handles_chart_generation_failure(
        self, mock_convert, mock_criterion_config, power_data, results_path, capsys
    ) -> None:
        alternative = make_alternative(DistributionType.NORMAL)
        builder = PowerReportBuilder(
            report_name="test",
            criteria_config=[mock_criterion_config],
            sample_sizes=[10],
            alternatives=[alternative],
            significance_levels=[0.05],
            power_result=power_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        with patch.object(builder, "_generate_chart_data", side_effect=RuntimeError("no matplotlib")):
            builder.build()

        html = mock_convert.call_args.args[0]
        captured = capsys.readouterr()

        assert "<img" not in html
        assert "<td>0.667</td>" in html
        assert "Failed to generate chart for DistributionType.NORMAL" in captured.out
        assert "no matplotlib" in captured.out

    # Checks that the rendered report carries the generation date as the timestamp.
    @patch(f"{BUILDER_PATH}.convert_html_to_pdf")
    def test_build_renders_current_timestamp(
        self, mock_convert, mock_criterion_config, mock_alternative, power_data, results_path
    ) -> None:
        builder = PowerReportBuilder(
            report_name="test",
            criteria_config=[mock_criterion_config],
            sample_sizes=[10],
            alternatives=[mock_alternative],
            significance_levels=[0.05],
            power_result=power_data,
            results_path=results_path,
            with_chart=ReportMode.WITHOUT_CHART,
        )

        builder.build()

        html = mock_convert.call_args.args[0]

        assert pd.Timestamp.now().strftime("%Y-%m-%d") in html
