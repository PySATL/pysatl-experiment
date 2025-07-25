from enum import Enum


class ReportMode(Enum):
    """
    Report mode (build report with chart or without chart).
    """

    WITH_CHART = "with-chart"
    WITHOUT_CHART = "without-chart"
