import pytest

from stattest.experiment.report import PdfPowerReportBuilder
from stattest.resolvers.builder_resolver import BuilderResolver


@pytest.mark.parametrize(
    ("name", "expected"),
    [("PdfPowerReportBuilder", PdfPowerReportBuilder)],
)
def test_load_without_params(name, expected):
    builder = BuilderResolver.load(name)

    assert builder is not None
