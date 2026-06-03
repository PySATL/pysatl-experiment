"""Experiment execution mode definitions."""

from enum import Enum


class RunMode(Enum):
    """Experiment execution modes."""

    REUSE = "reuse"
    OVERWRITE = "overwrite"

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
