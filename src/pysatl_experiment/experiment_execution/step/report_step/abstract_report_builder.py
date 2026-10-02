"""
Abstract report builder interface.

This module defines the common contract implemented by all report
builders responsible for generating report files.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


ContextT = TypeVar("ContextT")


class IReportBuilder(ABC, Generic[ContextT]):
    """
    Abstract interface for report builders.

    Implementations are responsible for generating reports
    in a specific format and saving them to disk.
    """

    @abstractmethod
    def build(self, context: ContextT) -> None:
        """
        Generate and save the report from prepared data and output settings.

        Notes
        -----
        Concrete implementations define the report format,
        content generation process, and output destination.
        """
        pass
