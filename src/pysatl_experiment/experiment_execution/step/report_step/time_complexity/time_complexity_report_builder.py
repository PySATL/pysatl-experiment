"""
Time complexity report generation.

This module provides functionality for generating PDF reports
containing execution time measurements of statistical criteria.

Reports may include both tabular data and graphical visualizations
of execution time versus sample size.
"""

import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from matplotlib import pyplot as plt

from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_statistic import (
    TimeComplexityReportStatistic,
)
from pysatl_experiment.utils.report_utils import convert_html_to_pdf, get_report_template_dir


class TimeComplexityReportBuilder:
    """
    Builder for time complexity reports.

    The builder produces PDF reports containing execution time
    measurements for statistical criteria across different
    sample sizes.

    Charts may optionally be embedded directly into the report.
    """

    def __init__(
        self,
        report_name: str,
        sample_sizes: list[int],
        statistic: TimeComplexityReportStatistic,
        results_path: Path,
        report_mode: ReportMode,
    ):
        """
        Initialize time complexity report builder.

        Parameters
        ----------
        report_name : str
            Name of the generated report.
        sample_sizes : list[int]
            Evaluated sample sizes.
        statistic : TimeComplexityReportStatistic
            Execution time statistics grouped by criterion code.
        results_path : Path
            Output directory.
        report_mode : ReportMode
            Determines whether charts should be generated.
        """
        self.report_name = report_name
        self.sample_sizes = sample_sizes
        self.statistic = statistic
        self.results_path = results_path
        self.report_mode = report_mode

        self.template_env = Environment(loader=FileSystemLoader(get_report_template_dir()), autoescape=True)

    def build(self) -> None:
        """
        Generate and save the time complexity report.

        Notes
        -----
        The report is rendered from a Jinja2 template and exported as PDF.
        """
        self.results_path.mkdir(parents=True, exist_ok=True)
        html_content = self._generate_html()
        pdf_path = self.results_path / f"{self.report_name}.pdf"
        convert_html_to_pdf(html_content, pdf_path)

    def _generate_chart(self) -> str | None:
        """
        Generate execution time chart.

        Returns
        -------
        str | None
            Base64-encoded image embedded as a data URL,
            or None if chart generation fails.

        Notes
        -----
        The chart displays execution time as a function
        of sample size for all configured criteria.
        """
        buf = BytesIO()
        plt.figure(figsize=(10, 7))

        for criterion, data in self.statistic.items():
            if not data:
                continue
            sizes, times_list = zip(*data, strict=True)
            sizes = tuple(np.array(sizes))
            times_ms = np.array(times_list) * 1000

            plt.plot(sizes, times_ms, marker="o", linestyle="-", label=criterion)

        plt.xlabel("Sample Size")
        plt.ylabel("Time (ms)")
        plt.title("Time Complexity of Criteria")
        plt.grid(True, which="both", linestyle="--", linewidth=0.5)
        plt.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize="medium",
            frameon=True,
            fancybox=False,
            shadow=False,
            borderaxespad=0.0,
            handlelength=1.5,
            columnspacing=1.0,
        )

        plt.minorticks_on()
        plt.tick_params(which="minor", width=0.5, length=2, color="gray")
        plt.tick_params(which="major", length=6, width=1)
        plt.tight_layout(rect=(0, 0, 0.85, 1))

        plt.savefig(buf, format="png", dpi=150)
        plt.close()

        buf.seek(0)
        image_data = buf.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        buf.close()

        return f"data:image/png;base64,{image_base64}"

    def _generate_html(self) -> str:
        """
        Generate HTML representation of the report.

        Returns
        -------
        str
            Rendered HTML document ready for PDF conversion.
        """
        plot_data = None
        if self.report_mode == ReportMode.WITH_CHART:
            try:
                plot_data = self._generate_chart()
            except Exception as e:
                print(f"Failed to generate plot: {e}")
                plot_data = None

        return self.template_env.get_template("tc_template.html").render(
            report_data=self.statistic.as_dict(),
            sizes=self.sample_sizes,
            plot_image=plot_data,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d"),
        )
