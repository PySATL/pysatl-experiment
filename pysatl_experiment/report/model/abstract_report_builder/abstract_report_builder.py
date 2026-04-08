from abc import ABC, abstractmethod


class IReportBuilder(ABC):
    """
    Report builder interface.
    """

    @abstractmethod
    def build(self) -> None:
        """
        Build file.
        """
        pass
