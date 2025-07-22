from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.report.common.utils import convert_html_to_pdf


class TimeComplexityReportBuilder:
    """
    Standard time complexity report builder.
    """

    def __init__(
            self,
            criteria_config: list[CriterionConfig],
            sample_sizes: list[int],
            times: Dict[str, List[Tuple[int, float]]],
            results_path: Path,

    ):
        self.criteria_config = criteria_config
        self.sample_sizes = sample_sizes
        self.times = times
        self.results_path = results_path

        template_dir = Path(__file__).parents[1] / "report_templates/time_complexity"
        self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def build(self) -> None:
        """
        Build the time complexity report.
        """

        self.results_path.mkdir(parents=True, exist_ok=True)
        html_content = self._generate_html()
        pdf_path = self.results_path / "time_complexity_report.pdf"
        convert_html_to_pdf(html_content, pdf_path)

    """def _generate_chart(self) -> Path:
        
        chart_file = self.charts_path / "time_complexity_chart.png"
        plt.figure(figsize=(8, 6))

        for criterion in self.times.keys():
            sizes, times_list = zip(*self.times[criterion])
            sizes = np.array(sizes)
            times_list = np.array(times_list) * 1000

            plt.plot(sizes, times_list, marker='o', linestyle='-', label=criterion)

        plt.xlabel('Sample Size')
        plt.ylabel('Time (ms)')
        plt.title('Time Complexity of Criteria')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend()

        plt.minorticks_on()

        plt.tick_params(which='minor', width=0.5, length=2, color='gray')
        plt.tick_params(which='major', length=6, width=1)

        plt.tight_layout()

        plt.savefig(chart_file, format='png', dpi=100)
        plt.close()

        return chart_file"""

    def _get_criterion_names(self) -> List[str]:
        """
        Return list of criterion names for reporting.
        """
        return [c.criterion_code.partition('_')[0] for c in self.criteria_config]

    def _generate_html(self) -> str:
        """
        Generate HTML report from processed data.

        :returns: HTML report string.
        """

        return self.template_env.get_template("tc_table_template.html").render(
            criteria=self._get_criterion_names(),
            report_data=self.times,
            sizes=self.sample_sizes,
            #chart_path=chart_path,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d")
        )

