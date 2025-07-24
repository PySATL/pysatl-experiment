import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from stattest.configuration.model.report_mode.report_mode import ReportMode
from stattest.report.time_complexity.time_complexity import TimeComplexityReportBuilder


class TestTimeComplexityReportBuilder:
    def test_init_stores_attributes_correctly(
            self, mock_criterion_config, time_data, results_path, with_chart
    ):
        criteria = [mock_criterion_config]
        sample_sizes = [10, 20, 30]

        builder = TimeComplexityReportBuilder(
            criteria_config=criteria,
            sample_sizes=sample_sizes,
            times=time_data,
            results_path=results_path,
            with_chart=with_chart,
        )

        assert builder.criteria_config == criteria
        assert builder.sample_sizes == sample_sizes
        assert builder.times == time_data
        assert builder.results_path == results_path
        assert builder.with_chart == with_chart
        assert builder.template_env is not None

    @patch("stattest.report.time_complexity.time_complexity.plt.savefig")
    @patch("stattest.report.time_complexity.time_complexity.plt.close")
    def test_generate_chart_creates_and_encodes_image(
            self, mock_plt_close, mock_plt_savefig, mock_criterion_config, time_data, results_path
    ):
        builder = TimeComplexityReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            times=time_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        fake_image_data = b"fake_png_image_data"
        mock_buf_instance = MagicMock(spec=BytesIO)
        mock_buf_instance.getvalue.return_value = fake_image_data

        with patch("stattest.report.time_complexity.time_complexity.BytesIO") as mock_bytes_io:
            mock_bytes_io.return_value = mock_buf_instance

            with patch("stattest.report.time_complexity.time_complexity.base64") as mock_base64:
                mock_base64.b64encode.return_value.decode.return_value = "encoded_fake_data"

                result = builder._generate_chart()

                mock_plt_savefig.assert_called_once_with(mock_buf_instance, format='png', dpi=150)
                mock_plt_close.assert_called_once()
                mock_buf_instance.seek.assert_called_once_with(0)
                mock_buf_instance.read.assert_called_once()

                mock_base64.b64encode.assert_called_once_with(mock_buf_instance.read.return_value)
                mock_base64.b64encode.return_value.decode.assert_called_once_with('utf-8')

                assert result == "data:image/png;base64,encoded_fake_data"

    def test_generate_html_includes_chart_when_with_chart(
            self, mock_criterion_config, time_data, results_path
    ):
        builder = TimeComplexityReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            times=time_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>With Chart</html>"
        with patch.object(builder.template_env, 'get_template', return_value=mock_template), \
                patch.object(builder, '_generate_chart', return_value="fake_data_url") as mock_gen_chart:
            html_content = builder._generate_html()

            mock_gen_chart.assert_called_once()
            mock_template.render.assert_called_once()
            render_kwargs = mock_template.render.call_args[1]
            assert "plot_image" in render_kwargs
            assert render_kwargs["plot_image"] == "fake_data_url"
            assert html_content == "<html>With Chart</html>"

    def test_generate_html_excludes_chart_when_without_chart(
            self, mock_criterion_config, time_data, results_path
    ):
        builder = TimeComplexityReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            times=time_data,
            results_path=results_path,
            with_chart=ReportMode.WITHOUT_CHART,
        )

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Without Chart</html>"
        with patch.object(builder.template_env, 'get_template', return_value=mock_template), \
                patch.object(builder, '_generate_chart') as mock_gen_chart:  # Не должен быть вызван

            html_content = builder._generate_html()

            mock_gen_chart.assert_not_called()
            mock_template.render.assert_called_once()
            render_kwargs = mock_template.render.call_args[1]
            assert "plot_image" in render_kwargs
            assert render_kwargs["plot_image"] is None
            assert html_content == "<html>Without Chart</html>"

    def test_generate_html_handles_chart_generation_failure(
            self, mock_criterion_config, time_data, results_path, capsys
    ):
        builder = TimeComplexityReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10, 20],
            times=time_data,
            results_path=results_path,
            with_chart=ReportMode.WITH_CHART,
        )

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Chart Failed</html>"
        with patch.object(builder.template_env, 'get_template', return_value=mock_template), \
                patch.object(builder, '_generate_chart', side_effect=Exception("Chart gen failed")):
            html_content = builder._generate_html()

            mock_template.render.assert_called_once()
            render_kwargs = mock_template.render.call_args[1]
            assert "plot_image" in render_kwargs
            assert render_kwargs["plot_image"] is None
            assert html_content == "<html>Chart Failed</html>"

    @pytest.mark.parametrize("chart_mode", [ReportMode.WITH_CHART, ReportMode.WITHOUT_CHART])
    @patch("stattest.report.time_complexity.time_complexity.convert_html_to_pdf")
    def test_build_creates_pdf_file(
            self, mock_convert, chart_mode, mock_criterion_config, time_data, results_path
    ):
        builder = TimeComplexityReportBuilder(
            criteria_config=[mock_criterion_config],
            sample_sizes=[10],
            times=time_data,
            results_path=results_path,
            with_chart=chart_mode,
        )

        with patch.object(builder, '_generate_html', return_value="<html>Content</html>") as mock_gen_html:
            builder.build()

            mock_gen_html.assert_called_once()
            mock_convert.assert_called_once_with("<html>Content</html>", results_path / "time_complexity_report.pdf")
            assert (results_path / "time_complexity_report.pdf").parent.exists()
