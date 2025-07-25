import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from matplotlib import pyplot as plt

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.report_mode.report_mode import ReportMode
from stattest.report.common.utils import convert_html_to_pdf, get_criterion_names


class TimeComplexityReportBuilder:
    """
    Standard time complexity report builder.
    """

    def __init__(
        self,
        criteria_config: list[CriterionConfig],
        sample_sizes: list[int],
        times: dict[str, list[tuple[int, float]]],
        results_path: Path,
        with_chart: ReportMode,
    ):
        self.criteria_config = criteria_config
        self.sample_sizes = sample_sizes
        self.times = times
        self.results_path = results_path
        self.with_chart = with_chart

        template_dir = Path(__file__).parents[1] / "report_templates/time_complexity"
        self.template_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def build(self) -> None:
        """
        Build the time complexity report.
        """

        self.results_path.mkdir(parents=True, exist_ok=True)
        html_content = self._generate_html()
        pdf_path = self.results_path / "time_complexity_report.pdf"
        convert_html_to_pdf(html_content, pdf_path)

    def _generate_chart(self) -> str | None:
        """
        Generate a line chart of execution time vs sample size for all criteria.

        :return: data URL string or None if chart could not be generated.
        """

        buf = BytesIO()
        plt.figure(figsize=(10, 7))

        for criterion in self.times.keys():
            data = self.times[criterion]
            if not data:
                continue
            sizes, times_list = zip(*data, strict=True)
            sizes = np.array(sizes)
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
        Generate HTML report from processed data.
        """
        plot_data = None
        if self.with_chart == ReportMode.WITH_CHART:
            try:
                plot_data = self._generate_chart()
            except Exception as e:
                print(f"Failed to generate plot: {e}")
                plot_data = None

        return self.template_env.get_template("tc_template.html").render(
            criteria=get_criterion_names(self.criteria_config),
            report_data=self.times,
            sizes=self.sample_sizes,
            plot_image=plot_data,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d"),
        )
