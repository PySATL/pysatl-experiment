from enum import Enum


class StepType(Enum):
    """
    Step type (standard or custom).
    """

    STANDARD = "standard"
    CUSTOM = "custom"

    @classmethod
    def list(cls):
        """
        Collect all enum values.

        @return: enum values
        """
        return [member.value for member in cls]
