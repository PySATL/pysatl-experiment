from pathlib import Path
from xhtml2pdf import pisa


def convert_html_to_pdf(html: str, output_path: Path) -> None:
    """
    Convert HTML to PDF

    :param html: HTML to convert
    :param output_path: Path to output PDF
    """

    with open(output_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(
            src=html,
            dest=pdf_file,
        )

    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")