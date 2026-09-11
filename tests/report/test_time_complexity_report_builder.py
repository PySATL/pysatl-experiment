"""Tests for time complexity report builder."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder import (
    TimeComplexityReportBuilder,
)


class TestTimeComplexityReportBuilder:
    def test_init_stores_attributes_correctly(self, time_data, results_path, with_chart):
        sample_sizes = [10, 20, 30]

        builder = TimeComplexityReportBuilder(
            report_name="test",
            sample_sizes=sample_sizes,
            statistic=time_data,
            results_path=results_path,
            report_mode=with_chart,
        )

        assert builder.sample_sizes == sample_sizes
        assert builder.statistic == time_data
        assert builder.results_path == results_path
        assert builder.report_mode == with_chart
        assert builder.template_env is not None

    @patch(
        "pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder."
        "plt.savefig"
    )
    @patch(
        "pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder."
        "plt.close"
    )
    def test_generate_chart_creates_and_encodes_image(self, mock_plt_close, mock_plt_savefig, time_data, results_path):
        builder = TimeComplexityReportBuilder(
            report_name="test",
            sample_sizes=[10, 20],
            statistic=time_data,
            results_path=results_path,
            report_mode=ReportMode.WITH_CHART,
        )

        fake_image_data = b"fake_png_image_data"
        mock_buf_instance = MagicMock(spec=BytesIO)
        mock_buf_instance.getvalue.return_value = fake_image_data

        with patch(
            "pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder."
            "BytesIO"
        ) as mock_bytes_io:
            mock_bytes_io.return_value = mock_buf_instance

            with patch(
                "pysatl_experiment.experiment_execution.step.report_step.time_complexity."
                "time_complexity_report_builder.base64"
            ) as mock_base64:
                mock_base64.b64encode.return_value.decode.return_value = "encoded_fake_data"

                result = builder._generate_chart()

                mock_plt_savefig.assert_called_once_with(mock_buf_instance, format="png", dpi=150)
                mock_plt_close.assert_called_once()
                mock_buf_instance.seek.assert_called_once_with(0)
                mock_buf_instance.read.assert_called_once()

                mock_base64.b64encode.assert_called_once_with(mock_buf_instance.read.return_value)
                mock_base64.b64encode.return_value.decode.assert_called_once_with("utf-8")

                assert result == "data:image/png;base64,encoded_fake_data"

    def test_generate_html_includes_chart_when_with_chart(self, time_data, results_path):
        builder = TimeComplexityReportBuilder(
            report_name="test",
            sample_sizes=[10, 20],
            statistic=time_data,
            results_path=results_path,
            report_mode=ReportMode.WITH_CHART,
        )

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>With Chart</html>"
        with (
            patch.object(builder.template_env, "get_template", return_value=mock_template),
            patch.object(builder, "_generate_chart", return_value="fake_data_url") as mock_gen_chart,
        ):
            html_content = builder._generate_html()

            mock_gen_chart.assert_called_once()
            mock_template.render.assert_called_once()
            render_kwargs = mock_template.render.call_args[1]
            assert "plot_image" in render_kwargs
            assert render_kwargs["plot_image"] == "fake_data_url"
            assert render_kwargs["report_data"] == time_data.as_dict()
            assert html_content == "<html>With Chart</html>"

    def test_generate_html_excludes_chart_when_without_chart(self, time_data, results_path):
        builder = TimeComplexityReportBuilder(
            report_name="test",
            sample_sizes=[10, 20],
            statistic=time_data,
            results_path=results_path,
            report_mode=ReportMode.WITHOUT_CHART,
        )

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Without Chart</html>"
        with (
            patch.object(builder.template_env, "get_template", return_value=mock_template),
            patch.object(builder, "_generate_chart") as mock_gen_chart,
        ):
            html_content = builder._generate_html()

            mock_gen_chart.assert_not_called()
            mock_template.render.assert_called_once()
            render_kwargs = mock_template.render.call_args[1]
            assert "plot_image" in render_kwargs
            assert render_kwargs["plot_image"] is None
            assert render_kwargs["report_data"] == time_data.as_dict()
            assert html_content == "<html>Without Chart</html>"

    def test_generate_html_handles_chart_generation_failure(self, time_data, results_path):
        builder = TimeComplexityReportBuilder(
            report_name="test",
            sample_sizes=[10, 20],
            statistic=time_data,
            results_path=results_path,
            report_mode=ReportMode.WITH_CHART,
        )

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Chart Failed</html>"
        with (
            patch.object(builder.template_env, "get_template", return_value=mock_template),
            patch.object(builder, "_generate_chart", side_effect=Exception("Chart gen failed")),
        ):
            html_content = builder._generate_html()

            mock_template.render.assert_called_once()
            render_kwargs = mock_template.render.call_args[1]
            assert "plot_image" in render_kwargs
            assert render_kwargs["plot_image"] is None
            assert render_kwargs["report_data"] == time_data.as_dict()
            assert html_content == "<html>Chart Failed</html>"

    @pytest.mark.parametrize("chart_mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
    @patch(
        "pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder."
        "convert_html_to_pdf"
    )
    def test_build_creates_pdf_file(self, mock_convert, chart_mode, time_data, results_path):
        builder = TimeComplexityReportBuilder(
            report_name="test",
            sample_sizes=[10],
            statistic=time_data,
            results_path=results_path,
            report_mode=chart_mode,
        )

        with patch.object(builder, "_generate_html", return_value="<html>Content</html>") as mock_gen_html:
            builder.build()

            mock_gen_html.assert_called_once()
            mock_convert.assert_called_once_with("<html>Content</html>", results_path / "test.pdf")
            assert (results_path / "time_complexity_report.pdf").parent.exists()
