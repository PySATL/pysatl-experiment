"""Task failure policy definitions."""

from enum import Enum


class TaskFailurePolicy(Enum):
    """Policies for handling individual task failures during parallel execution."""

    FAIL_FAST = "fail_fast"
    ISOLATE = "isolate"

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
