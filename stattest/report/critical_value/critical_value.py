from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from matplotlib import pyplot as plt

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.report_mode.report_mode import ReportMode
from stattest.report.common.utils import convert_html_to_pdf


class CriticalValueReportBuilder:
    """
    Standard critical value report builder.
    """

    def __init__(
            self,
            criteria_config: list[CriterionConfig],
            sample_sizes: list[int],
            significance_levels: list[float],
            cv_values: list[float],
            results_path: Path,
            with_chart: ReportMode,
    ):
        self.criteria_config = criteria_config
        self.sizes = sample_sizes
        self.significance_levels = significance_levels
        self.cv_values = cv_values
        self.results_path = results_path
        self.with_chart = with_chart

        template_dir = Path(__file__).parents[1] / "report_templates/critical_values"
        self.pdf_path = self.results_path / "critical_values_report.pdf"

        self.template_env = Environment(loader=FileSystemLoader(template_dir),
                                        autoescape=True)

    def build(self) -> None:
        """
        Build PDF file from critical value report builder.
        """

        with TemporaryDirectory(prefix="cv_charts_") as temp_dir:
            charts_dir = Path(temp_dir)

            html_content = self._generate_html(charts_dir)

            self.results_path.mkdir(parents=True, exist_ok=True)
            convert_html_to_pdf(html_content, self.pdf_path)

    def _generate_html(self, charts_dir: Path) -> str:
        """
        Generate HTML with tables and optional charts.

        :param charts_dir: chart image directory.

        :return: rendered HTML string with embedded chart paths.
        """

        tables = []
        for config in self.criteria_config:
            table_data = self._generate_table_data(config.criterion_code)
            chart_data = None
            if self.with_chart == ReportMode.WITH_CHART:
                try:
                    chart_data = self._generate_chart_data(config.criterion_code, charts_dir)
                except Exception as e:
                    print(f"Failed to generate chart for {config.criterion_code}: {e}")
                    chart_data = None

            tables.append({
                'title': f"Criterion: {config.criterion_code}",
                'levels': [f"α = {alpha}" for alpha in self.significance_levels],
                'rows': table_data['rows'],
                'chart': chart_data
            })

        html = self.template_env.get_template("cv_template.html").render(
            tables=tables,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d"),
        )
        return html

    def _generate_table_data(self, criterion_code: str) -> dict[str, object]:
        """
        Generate table data.

        :param criterion_code: the code of the criterion for which to generate the table data.

        :return: a dictionary containing a list of rows, where each row is a dict with
        'size' and 'values'.
        """

        values = next(
            values for cfg, values in zip(
                self.criteria_config,
                self._chunk_cv_values(),
                strict=True
            ) if cfg.criterion_code == criterion_code
        )

        values_2d = np.array(values).reshape(len(self.sizes), len(self.significance_levels))

        rows = []
        for i, size in enumerate(self.sizes):
            row = {
                'size': size,
                'values': [float(val) for val in values_2d[i]]
            }
            rows.append(row)

        return {'rows': rows}

    def _generate_chart_data(self, criterion_code: str, charts_dir: Path) -> str:
        """
        Generate a chart and save it as PNG file.

        :param criterion_code: the code of the criterion for which to generate the chart.
        :param charts_dir: chart image directory.

        :return: path to chart file.
        """

        chart_path = charts_dir / f"{criterion_code}.png"

        plt.figure(figsize=(8, 5), dpi=100)

        chunked_values = self._chunk_cv_values()

        idx = next(i for i, cfg in enumerate(self.criteria_config)
                   if cfg.criterion_code == criterion_code)
        values = chunked_values[idx]
        values_2d = np.array(values).reshape(len(self.sizes), len(self.significance_levels))

        for j, alpha in enumerate(self.significance_levels):
            cv_values = values_2d[:, j]
            plt.plot(
                self.sizes,
                cv_values,
                marker='o',
                linestyle='-',
                label=f"α = {alpha}"
            )

        plt.xlabel("Sample Size")
        plt.ylabel("Critical Value")
        plt.title(f"Critical Value vs Sample Size — {criterion_code}")
        plt.grid(True, linestyle='--', alpha=0.5)

        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize='small')

        plt.tight_layout(rect=(0, 0, 0.85, 1))

        plt.savefig(chart_path, format='png', dpi=150, bbox_inches='tight')
        plt.close()

        return str(chart_path.resolve().as_posix())

    def _chunk_cv_values(self) -> list[list[float]]:
        """
        Splits a flat cv_values list into parts according to the criteria.

        :return: a list of lists of critical values for each significance level.
        """

        chunk_size = len(self.sizes) * len(self.significance_levels)
        return [
            self.cv_values[i:i + chunk_size]
            for i in range(0, len(self.cv_values), chunk_size)
        ]
