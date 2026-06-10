"""
Utility functions for report generation.

This module provides helper functions used across report builders,
including PDF generation from HTML templates and extraction of
human-readable criterion names from configuration objects.
"""

from pathlib import Path

from xhtml2pdf import pisa

from pysatl_experiment.configuration.criteria_config import CriterionConfig


def convert_html_to_pdf(html: str, output_path: Path) -> None:
    """
    Convert HTML content into a PDF document.

    Parameters
    ----------
    html : str
        Rendered HTML content to convert.
    output_path : Path
        Destination path of the generated PDF file.

    Raises
    ------
    RuntimeError
        If PDF generation fails.

    Notes
    -----
    PDF rendering is performed using the ``xhtml2pdf`` library.
    Existing files at the target location are overwritten.
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
    Extract simplified criterion names from configuration objects.

    Parameters
    ----------
    criteria_config : list[CriterionConfig]
        Criterion configurations.

    Returns
    -------
    list[str]
        Criterion names obtained from the prefix of
        ``criterion_code`` before the first underscore.
    """
    return [c.criterion_code.partition("_")[0] for c in criteria_config]
