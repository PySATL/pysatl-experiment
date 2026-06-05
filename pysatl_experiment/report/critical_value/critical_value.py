"""
Critical value report generation.

This module provides a report builder that generates PDF reports
containing critical values of statistical criteria for different
sample sizes and significance levels.

Optional visualizations may be included as charts.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from matplotlib import pyplot as plt

from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.report.common.utils import convert_html_to_pdf


class CriticalValueReportBuilder:
    """
    Builder for critical value reports.

    The builder generates tabular representations of critical values
    and optionally includes charts illustrating how critical values
    change with sample size.

    Reports are rendered from Jinja2 templates and exported as PDF.
    """

    def __init__(
        self,
        report_name: str,
        criteria_config: list[CriterionConfig],
        sample_sizes: list[int],
        significance_levels: list[float],
        cv_values: list[float | tuple[float, float]],
        results_path: Path,
        with_chart: ReportMode,
    ):
        """
        Initialize report builder.

        Parameters
        ----------
        criteria_config : list[CriterionConfig]
            Criteria included in the report.
        sample_sizes : list[int]
            Evaluated sample sizes.
        significance_levels : list[float]
            Significance levels.
        cv_values : list[float | tuple[float, float]]
            Computed critical values.
        results_path : Path
            Directory for report output.
        with_chart : ReportMode
            Determines whether charts should be included.
        """
        self.report_name = report_name
        self.criteria_config = criteria_config
        self.sizes = sample_sizes
        self.significance_levels = significance_levels
        self.cv_values = cv_values
        self.results_path = results_path
        self.with_chart = with_chart
        template_dir = Path(__file__).parents[1] / "report_templates/critical_values"
        self.pdf_path = self.results_path / f"{report_name}.pdf"

        self.template_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def build(self) -> None:
        """
        Generate and save the critical value report.

        Notes
        -----
        Temporary chart files are created during report generation
        and removed automatically afterward.
        """
        with TemporaryDirectory(prefix="cv_charts_") as temp_dir:
            charts_dir = Path(temp_dir)

            html_content = self._generate_html(charts_dir)

            self.results_path.mkdir(parents=True, exist_ok=True)
            convert_html_to_pdf(html_content, self.pdf_path)

    def _generate_html(self, charts_dir: Path) -> str:
        """
        Generate HTML representation of the report.

        Parameters
        ----------
        charts_dir : Path
            Directory containing generated chart images.

        Returns
        -------
        str
            Rendered HTML document.
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

            tables.append(
                {
                    "title": f"Criterion: {config.criterion_code}",
                    "levels": [f"α = {alpha}" for alpha in self.significance_levels],
                    "rows": table_data["rows"],
                    "chart": chart_data,
                }
            )

        html = self.template_env.get_template("cv_template.html").render(
            tables=tables,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d"),
        )
        return html

    def _generate_table_data(self, criterion_code: str) -> dict[str, object]:
        """
        Generate table data for a criterion.

        Parameters
        ----------
        criterion_code : str
            Criterion identifier.

        Returns
        -------
        dict[str, object]
            Structure containing rows and values
            used for template rendering.
        """
        values = next(
            values
            for cfg, values in zip(self.criteria_config, self._chunk_cv_values(), strict=True)
            if cfg.criterion_code == criterion_code
        )

        values_2d = np.array(values).reshape(len(self.sizes), len(self.significance_levels))

        rows = []
        for i, size in enumerate(self.sizes):
            row = {"size": size, "values": [float(val) for val in values_2d[i]]}
            rows.append(row)

        return {"rows": rows}

    def _generate_chart_data(self, criterion_code: str, charts_dir: Path) -> str:
        """
        Generate chart for a criterion.

        Parameters
        ----------
        criterion_code : str
            Criterion identifier.
        charts_dir : Path
            Directory for chart images.

        Returns
        -------
        str
        """
        chart_path = charts_dir / f"{criterion_code}.png"

        plt.figure(figsize=(8, 5), dpi=100)

        chunked_values = self._chunk_cv_values()

        idx = next(i for i, cfg in enumerate(self.criteria_config) if cfg.criterion_code == criterion_code)
        values = chunked_values[idx]
        values_2d = np.array(values).reshape(len(self.sizes), len(self.significance_levels))

        for j, alpha in enumerate(self.significance_levels):
            cv_values = values_2d[:, j]
            plt.plot(self.sizes, cv_values, marker="o", linestyle="-", label=f"α = {alpha}")

        plt.xlabel("Sample Size")
        plt.ylabel("Critical Value")
        plt.title(f"Critical Value vs Sample Size — {criterion_code}")
        plt.grid(True, linestyle="--", alpha=0.5)

        plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize="small")

        plt.tight_layout(rect=(0, 0, 0.85, 1))

        plt.savefig(chart_path, format="png", dpi=150, bbox_inches="tight")
        plt.close()

        return str(chart_path.resolve().as_posix())

    def _chunk_cv_values(self) -> list[list[float | tuple[float, float]]]:
        """
        Split critical value sequence into criterion-specific groups.

        Returns
        -------
        list[list[float | tuple[float, float]]]
            Critical values grouped by criterion.
        """
        chunk_size = len(self.sizes) * len(self.significance_levels)
        return [self.cv_values[i : i + chunk_size] for i in range(0, len(self.cv_values), chunk_size)]
