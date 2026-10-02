"""
Statistical power report generation.

This module provides a report builder capable of generating PDF reports
containing power estimates for statistical criteria under various
alternative hypotheses and significance levels.

Charts may optionally be included in the report.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from pysatl_experiment.experiment_execution.configured_criterion import ConfiguredCriterion
from pysatl_experiment.experiment_execution.step.report_step.abstract_report_builder import IReportBuilder
from pysatl_experiment.experiment_execution.step.report_step.report_context import ReportBuilderContext
from pysatl_experiment.persistence.models.power import PowerModel
from pysatl_experiment.types import Alternative, ReportMode
from pysatl_experiment.utils.report_utils import convert_html_to_pdf, get_criterion_names


class PowerReportBuilder(IReportBuilder[ReportBuilderContext[PowerModel]]):
    """
    Builder for statistical power reports.

    The report contains power tables and optional charts showing
    the relationship between statistical power and sample size.

    Reports are rendered from HTML templates and exported as PDF.
    """

    def __init__(
        self,
        criteria_config: list[ConfiguredCriterion],
        sample_sizes: list[int],
        significance_levels: list[float],
        alternatives: list[Alternative],
    ) -> None:
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.sample_sizes = sorted(sample_sizes)
        self.alternatives = alternatives

    def build(self, context: ReportBuilderContext[PowerModel]) -> None:
        """Prepare statistics from loaded results and render the selected template."""
        self.report_name = context.report_name
        self.results_path = context.results_path
        self.with_chart = context.report_mode
        self.pdf_path = context.results_path / f"{context.report_name}.pdf"
        self.template_name = context.template_path.name
        self.template_env = Environment(loader=FileSystemLoader(context.template_path.parent), autoescape=True)
        self.power_result: dict[str, dict[tuple[str, float], dict[int, list[bool]]]] = {}
        for result in context.data:
            criterion_data = self.power_result.setdefault(result.criterion_code, {})
            series = criterion_data.setdefault((result.alternative_code, result.significance_level), {})
            series[result.sample_size] = result.results_criteria
        with tempfile.TemporaryDirectory(prefix="power_charts_") as temp_dir:
            charts_dir = Path(temp_dir) / "charts"

            html_content = self._generate_html(charts_dir)

            self.results_path.mkdir(parents=True, exist_ok=True)
            convert_html_to_pdf(html_content, self.pdf_path)

    def _generate_html(self, charts_dir: Path) -> str:
        """
        Generate HTML report content.

        Parameters
        ----------
        charts_dir : Path
            Directory containing generated charts.

        Returns
        -------
        str
            Rendered HTML document.
        """
        tables = []
        for alternative in self.alternatives:
            for significance_level in self.significance_levels:
                table_data = self._generate_table_data(alternative, significance_level)
                chart_data = None
                if self.with_chart == ReportMode.WITH_CHART:
                    try:
                        chart_data = self._generate_chart_data(alternative, significance_level, charts_dir)
                    except Exception as e:
                        print(
                            f"Failed to generate chart for {alternative.distribution_type}, α={significance_level}: {e}"
                        )
                        chart_data = None
                tables.append(
                    {
                        "alternative": alternative,
                        "significance_level": significance_level,
                        "table": table_data,
                        "chart": chart_data,
                    }
                )

        html = self.template_env.get_template(self.template_name).render(
            report_name=self.report_name,
            tables=tables,
            criteria=get_criterion_names(self.criteria_config),
            sample_sizes=self.sample_sizes,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d"),
        )
        return html

    def _generate_table_data(
        self,
        alternative: Alternative,
        significance_level: float,
    ) -> dict[int, dict[str, float]]:
        """
        Generate power table data.

        Parameters
        ----------
        alternative : Alternative
            Alternative hypothesis.
        significance_level : float
            Significance level.

        Returns
        -------
        dict[int, dict[str, float]]
            Power values grouped by sample size
            and criterion.
        """
        table_data = {}
        for size in self.sample_sizes:
            row_data: dict[str, float] = {}

            for config in self.criteria_config:
                key = (alternative.distribution_type, significance_level)
                results = self.power_result[config.criterion_code].get(key, {}).get(size, [])
                power = float(np.mean(results)) if results else 0.0
                short_criterion_name = config.criterion_code.partition("_")[0]
                row_data[short_criterion_name] = round(power, 3)

            table_data[size] = row_data

        return table_data

    def _generate_chart_data(
        self,
        alternative: Alternative,
        significance_level: float,
        charts_dir: Path,
    ) -> str:
        """
        Generate power chart.

        Parameters
        ----------
        alternative : Alternative
            Alternative hypothesis.
        significance_level : float
            Significance level.
        charts_dir : Path
            Directory for chart files.

        Returns
        -------
        str
            Absolute path to generated chart image.
        """
        charts_dir.mkdir(parents=True, exist_ok=True)

        chart_path = charts_dir / f"{alternative.distribution_type}_{significance_level}.png"

        figure = Figure(figsize=(10, 6), dpi=100)
        FigureCanvasAgg(figure)
        axes = figure.subplots()

        for config in self.criteria_config:
            sizes = []
            powers = []
            key = (alternative.distribution_type, significance_level)
            for size in self.sample_sizes:
                results = self.power_result[config.criterion_code].get(key, {}).get(size, [])
                if results:
                    sizes.append(size)
                    powers.append(np.mean(results))
            if sizes:
                axes.plot(sizes, powers, marker="o", linestyle="-", label=config.criterion_code)

        axes.set_xlabel("Sample size")
        axes.set_ylabel("Power")
        axes.set_title(f"Power vs Sample Size — {alternative.distribution_type}, α={significance_level}")
        axes.grid(True, linestyle="--", alpha=0.5)
        axes.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="small")
        figure.tight_layout(rect=(0, 0, 0.85, 1))

        figure.savefig(chart_path, format="png", dpi=100, bbox_inches="tight")

        return str(chart_path.resolve().as_posix())
