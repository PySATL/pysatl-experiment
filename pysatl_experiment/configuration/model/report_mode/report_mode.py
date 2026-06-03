"""Report generation mode definitions."""

from enum import Enum


class ReportMode(Enum):
    """Report generation modes."""

    WITH_CHART = "with-chart"
    WITHOUT_CHART = "without-chart"

    @classmethod
    def list(cls):
        """
        Return all enum values.

        Returns
        -------
        list[str]
            Available enum values.
        """
        return [member.value for member in cls]
