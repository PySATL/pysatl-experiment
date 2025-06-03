from typing import Protocol


class IReportBuilder(Protocol):
    """
    Report builder interface.
    """

    def build(self) -> None:
        """
        Build file.
        """
        pass
