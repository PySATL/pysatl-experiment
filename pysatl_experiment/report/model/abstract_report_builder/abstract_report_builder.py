"""
Abstract report builder interface.

This module defines the common contract implemented by all report
builders responsible for generating report files.
"""

from abc import ABC, abstractmethod


class IReportBuilder(ABC):
    """
    Abstract interface for report builders.

    Implementations are responsible for generating reports
    in a specific format and saving them to disk.
    """

    @abstractmethod
    def build(self) -> None:
        """
        Generate and save the report.

        Notes
        -----
        Concrete implementations define the report format,
        content generation process, and output destination.
        """
        pass
