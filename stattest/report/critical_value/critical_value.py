from pathlib import Path
from typing import Literal, List, Dict

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from stattest.configuration.criteria_config.criteria_config import CriterionConfig

TableType = Literal['main', 'transposed', 'stats']


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
    ):
        self.criteria_config = criteria_config
        self.sizes = sample_sizes
        self.significance_levels = significance_levels
        self.cv_values = cv_values
        self.results_path = results_path
        template_dir = Path(__file__).parents[1] / "report_templates/critical_values"
        self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def build(self) -> None:
        """
        Build PDF file from critical value report builder.
        """

        self.results_path.mkdir(parents=True, exist_ok=True)

        tables = []
        for criteria_config in self.criteria_config:
            table_html = self._generate_table(criteria_config.criterion_code)
            tables.append({
                'title': f"Criterion: {criteria_config.criterion_code}",
                'content': table_html
            })

        html_content = self._render_html_template(tables)

        pdf_path = self.results_path / "critical_values_report.pdf"
        self._convert_html_to_pdf(html_content, pdf_path)

    # add more table generators
    def _generate_table(self, criterion_code: str) -> str:
        values = next(
            values for cfg, values in zip(
                self.criteria_config,
                self._chunk_cv_values()
            ) if cfg.criterion_code == criterion_code
        )

        df = pd.DataFrame(
            data=np.array(values).reshape(
                len(self.sizes),
                len(self.significance_levels)
            ),
            index=pd.Index(self.sizes),
            columns=[f"α = {alpha}" for alpha in self.significance_levels]
        )

        return df.to_html()

    def _convert_html_to_pdf(self, html: str, output_path: Path) -> None:
        """
        Convert HTML to PDF
        """

        with open(output_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(
                src=html,
                dest=pdf_file,
            )

        if pisa_status.err:
            raise RuntimeError(f"PDF generation failed: {pisa_status.err}")

    def _render_html_template(self, tables: List[Dict[str, str]]) -> str:
        """Renders HTML template with tables"""
        template = self.template_env.get_template("cv_tables_report_template.html")
        return template.render(
            tables=tables,
            timestamp=pd.Timestamp.now().strftime("%Y-%m-%d"),
            criteria_count=len(self.criteria_config),
            sample_sizes=self.sizes,
            significance_levels=self.significance_levels
        )

    def _chunk_cv_values(self) -> List[List[float]]:
        """Разбивает плоский список cv_values на части по критериям"""

        chunk_size = len(self.sizes) * len(self.significance_levels)
        return [
            self.cv_values[i:i + chunk_size]
            for i in range(0, len(self.cv_values), chunk_size)
        ]
