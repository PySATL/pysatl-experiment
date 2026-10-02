"""Build a time complexity PDF from prepared results and an explicit template."""

import base64
import logging
from datetime import date
from io import BytesIO

import numpy as np
from jinja2 import Environment, FileSystemLoader
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from typing_extensions import override

from pysatl_experiment.experiment_execution.step.report_step.abstract_report_builder import IReportBuilder
from pysatl_experiment.experiment_execution.step.report_step.report_context import ReportBuilderContext
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel
from pysatl_experiment.types import ReportMode
from pysatl_experiment.utils.report_utils import convert_html_to_pdf

from .time_complexity_report_series import TimeComplexityReportSeries
from .time_complexity_report_statistic import TimeComplexityReportStatistic


logger = logging.getLogger(__name__)


class TimeComplexityReportBuilder(IReportBuilder[ReportBuilderContext[TimeComplexityModel]]):
    """Calculate statistics and render a report without accessing storage."""

    @override
    def build(self, context: ReportBuilderContext[TimeComplexityModel]) -> None:
        """Render the selected template and save a PDF in the configured directory."""
        statistic = self._collect_statistics(context.data)
        html = self._generate_html(context, statistic)
        context.results_path.mkdir(parents=True, exist_ok=True)
        convert_html_to_pdf(html, context.results_path / f"{context.report_name}.pdf")

    @staticmethod
    def _collect_statistics(data: tuple[TimeComplexityModel, ...]) -> TimeComplexityReportStatistic:
        """Compute means per size without merging different criterion parameters."""
        statistic = TimeComplexityReportStatistic()
        for result in data:
            if not result.results_times:
                raise ValueError(f"Empty timing measurements for {result}")
            statistic.add_criterion_statistic(
                TimeComplexityReportSeries.from_result(result),
                result.sample_size,
                float(np.mean(result.results_times)),
            )
        return statistic

    @staticmethod
    def _generate_chart(statistic: TimeComplexityReportStatistic) -> str:
        """Render the series to an in-memory PNG using a noninteractive canvas."""
        figure = Figure(figsize=(10, 7))
        FigureCanvasAgg(figure)
        axes = figure.subplots()
        for series, points in statistic.items():
            if not points:
                continue
            sizes, times = zip(*points, strict=True)
            axes.plot(sizes, np.array(times) * 1000, marker="o", linestyle="-", label=series.label)
        axes.set_xlabel("Sample Size")
        axes.set_ylabel("Time (ms)")
        axes.set_title("Time Complexity of Criteria")
        axes.grid(True, which="both", linestyle="--", linewidth=0.5)
        axes.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize="small")
        axes.minorticks_on()
        figure.tight_layout()
        with BytesIO() as buffer:
            figure.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def _generate_html(
        self,
        context: ReportBuilderContext[TimeComplexityModel],
        statistic: TimeComplexityReportStatistic,
    ) -> str:
        """Render a caller-selected template with data, statistics and optional chart."""
        plot_data = None
        if context.report_mode == ReportMode.WITH_CHART and statistic.values:
            try:
                plot_data = self._generate_chart(statistic)
            except Exception:
                logger.warning("Failed to generate time complexity chart", exc_info=True)
        environment = Environment(loader=FileSystemLoader(context.template_path.parent), autoescape=True)
        return environment.get_template(context.template_path.name).render(
            report_name=context.report_name,
            data=context.data,
            report_data=statistic.as_dict(),
            sizes=sorted({row.sample_size for row in context.data}),
            plot_image=plot_data,
            timestamp=date.today().isoformat(),
        )
