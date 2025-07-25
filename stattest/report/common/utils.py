from pathlib import Path

from xhtml2pdf import pisa

from stattest.configuration.criteria_config.criteria_config import CriterionConfig


def convert_html_to_pdf(html: str, output_path: Path) -> None:
    """
    Convert HTML to PDF.

    :param html: HTML to convert.
    :param output_path: path to output PDF.
    """

    with output_path.open("w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(
            src=html,
            dest=pdf_file,
        )

    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")


def get_criterion_names(criteria_config: list[CriterionConfig]) -> list[str]:
    """
    Extract simplified criterion names.

    :param criteria_config: list of criteria configs.

    :return: list of criterion names.
    """

    return [c.criterion_code.partition("_")[0] for c in criteria_config]
