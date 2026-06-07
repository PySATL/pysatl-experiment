"""
Statistical power report generation.

This module provides a report builder capable of generating PDF reports
containing power estimates for statistical criteria under various
alternative hypotheses and significance levels.

Charts may optionally be included in the report.
"""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from pysatl_experiment.configuration.criteria_config import CriterionConfig
from pysatl_experiment.configuration.model.alternative import Alternative
from pysatl_experiment.configuration.model.report_mode import ReportMode
from pysatl_experiment.report.common.utils import convert_html_to_pdf, get_criterion_names


class PowerReportBuilder:
    """
    Builder for statistical power reports.

    The report contains power tables and optional charts showing
    the relationship between statistical power and sample size.

    Reports are rendered from HTML templates and exported as PDF.
    """

    def __init__(
        self,
        report_name: str,
        criteria_config: list[CriterionConfig],
        sample_sizes: list[int],
        alternatives: list[Alternative],
        significance_levels: list[float],
        power_result: dict[str, dict[tuple[str, float], dict[int, list[bool]]]],
        results_path: Path,
        with_chart: ReportMode,
    ):
        """
        Initialize power report builder.

        Parameters
        ----------
        report_name : str
            Name of the generated report.
        criteria_config : list[CriterionConfig]
            Criteria included in the report.
        sample_sizes : list[int]
            Evaluated sample sizes.
        alternatives : list[Alternative]
            Alternative hypotheses.
        significance_levels : list[float]
            Significance levels.
        power_result : dict
            Computed power results.
        results_path : Path
            Output directory.
        with_chart : ReportMode
            Determines whether charts should be generated.
        """
        self.criteria_config = criteria_config
        self.sample_sizes = sample_sizes
        self.alternatives = alternatives
        self.significance_levels = significance_levels
        self.power_result = power_result
        self.results_path = results_path
        self.with_chart = with_chart

        template_dir = Path(__file__).parents[1] / "report_templates/power"
        self.pdf_path = self.results_path / f"{report_name}.pdf"

        self.template_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def build(self) -> None:
        """
        Generate and save the power report.

        Notes
        -----
        Temporary chart files are created during report generation
        and deleted automatically afterward.
        """
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
                        print(f"Failed to generate chart for {alternative.generator_name}, α={significance_level}: {e}")
                        chart_data = None
                tables.append(
                    {
                        "alternative": alternative,
                        "significance_level": significance_level,
                        "table": table_data,
                        "chart": chart_data,
                    }
                )

        html = self.template_env.get_template("power_template.html").render(
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
                key = (alternative.generator_name, significance_level)
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

        chart_path = charts_dir / f"{alternative.generator_name}_{significance_level}.png"

        plt.figure(figsize=(10, 6), dpi=100)

        for config in self.criteria_config:
            sizes = []
            powers = []
            key = (alternative.generator_name, significance_level)
            for size in self.sample_sizes:
                results = self.power_result[config.criterion_code].get(key, {}).get(size, [])
                if results:
                    sizes.append(size)
                    powers.append(np.mean(results))
            if sizes:
                plt.plot(sizes, powers, marker="o", linestyle="-", label=config.criterion_code)

        plt.xlabel("Sample size")
        plt.ylabel("Power")
        plt.title(f"Power vs Sample Size — {alternative.generator_name}, α={significance_level}")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="small")
        plt.tight_layout(rect=(0, 0, 0.85, 1))

        plt.savefig(chart_path, format="png", dpi=100, bbox_inches="tight")
        plt.close()

        return str(chart_path.resolve().as_posix())
