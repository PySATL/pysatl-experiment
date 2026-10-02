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
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from pysatl_criterion.hypothesis_testing.alternative_factory.alternative_factories import AbstractAlternativeFactory

from pysatl_experiment.experiment_execution.configured_criterion import ConfiguredCriterion
from pysatl_experiment.experiment_execution.step.report_step.abstract_report_builder import IReportBuilder
from pysatl_experiment.experiment_execution.step.report_step.report_context import ReportBuilderContext
from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionModel
from pysatl_experiment.types import ReportMode
from pysatl_experiment.utils.report_utils import convert_html_to_pdf


class CriticalValueReportBuilder(IReportBuilder[ReportBuilderContext[LimitDistributionModel]]):
    """
    Builder for critical value reports.

    The builder generates tabular representations of critical values
    and optionally includes charts illustrating how critical values
    change with sample size.

    Reports are rendered from Jinja2 templates and exported as PDF.
    """

    def __init__(
        self,
        criteria_config: list[ConfiguredCriterion],
        sample_sizes: list[int],
        significance_levels: list[float],
    ) -> None:
        self.criteria_config = criteria_config
        self.significance_levels = significance_levels
        self.sizes = sorted(sample_sizes)

    def build(self, context: ReportBuilderContext[LimitDistributionModel]) -> None:
        """Prepare statistics from loaded results and render the selected template."""
        self.report_name = context.report_name
        self.results_path = context.results_path
        self.with_chart = context.report_mode
        self.pdf_path = context.results_path / f"{context.report_name}.pdf"
        self.template_name = context.template_path.name
        self.template_env = Environment(loader=FileSystemLoader(context.template_path.parent), autoescape=True)
        self.cv_values = []
        for config in self.criteria_config:
            factory = AbstractAlternativeFactory.get_concrete_factory(
                config.statistics_class_object.alternative().type()
            )
            calculator = factory.get_critical_value_calculator()
            for size in self.sizes:
                matches = [
                    row
                    for row in context.data
                    if row.criterion_code == config.criterion_code
                    and row.criterion_parameters == config.criterion.parameters
                    and row.sample_size == size
                ]
                if len(matches) != 1:
                    raise ValueError(f"Expected one limit distribution for {config.criterion_code}, size={size}")
                for alpha in self.significance_levels:
                    self.cv_values.append(calculator.calculate(matches[0].results_statistics, alpha))
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

        html = self.template_env.get_template(self.template_name).render(
            report_name=self.report_name,
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

        figure = Figure(figsize=(8, 5), dpi=100)
        FigureCanvasAgg(figure)
        axes = figure.subplots()

        chunked_values = self._chunk_cv_values()

        idx = next(i for i, cfg in enumerate(self.criteria_config) if cfg.criterion_code == criterion_code)
        values = chunked_values[idx]
        values_2d = np.array(values).reshape(len(self.sizes), len(self.significance_levels))

        for j, alpha in enumerate(self.significance_levels):
            cv_values = values_2d[:, j]
            axes.plot(self.sizes, cv_values, marker="o", linestyle="-", label=f"α = {alpha}")

        axes.set_xlabel("Sample Size")
        axes.set_ylabel("Critical Value")
        axes.set_title(f"Critical Value vs Sample Size — {criterion_code}")
        axes.grid(True, linestyle="--", alpha=0.5)

        axes.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize="small")

        figure.tight_layout(rect=(0, 0, 0.85, 1))

        figure.savefig(chart_path, format="png", dpi=150, bbox_inches="tight")

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
