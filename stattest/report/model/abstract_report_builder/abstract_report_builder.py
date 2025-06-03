from typing import Protocol


class IReportBuilder(Protocol):
    """
    Report builder interface.
    """

    def process(self) -> None:
        """
        Process data.
        """
        pass

    def build(self) -> None:
        """
        Build file.
        """
        pass
