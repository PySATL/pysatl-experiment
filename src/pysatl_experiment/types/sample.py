"""A sample of numeric observations, independent of storage and execution."""

from dataclasses import dataclass


@dataclass(slots=True)
class Sample:
    """Wrap a list of observations without copying or converting its values."""

    values: list[float]

    @property
    def size(self) -> int:
        """Return the current number of observations."""
        return len(self.values)
