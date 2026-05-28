"""Experiment step type definitions."""

from enum import Enum


class StepType(Enum):  # TODO: notes here and everywhere in models??
    """Available implementation types for experiment steps."""

    STANDARD = "standard"
    CUSTOM = "custom"

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
