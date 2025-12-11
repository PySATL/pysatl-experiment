from enum import Enum


class RunMode(Enum):
    """
    Run mode (use existing data in DB or overwrite).
    """

    REUSE = "reuse"
    OVERWRITE = "overwrite"

    @classmethod
    def list(cls):
        """
        Collect all enum values.

        @return: enum values
        """
        return [member.value for member in cls]
