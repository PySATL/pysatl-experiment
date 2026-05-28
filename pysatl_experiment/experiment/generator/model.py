"""Abstract interface for random value sample generators."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractRVSGenerator(ABC):
    """Base interface for all random value sample generators.

    Generator implementations are responsible for:

    - generating random samples from a probability distribution,
    - providing a unique generator identifier,
    - storing distribution parameters.

    Notes
    -----
    All concrete generators must implement ``code`` and ``generate``.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize generator base class."""
        super().__init__()

    @abstractmethod
    def code(self) -> str:
        """Return unique generator code.

        Returns
        -------
        str
            Generator identifier containing distribution name
            and parameter values.
        """
        raise NotImplementedError

    @staticmethod
    def _convert_to_code(items: list[Any]) -> str:
        """Convert generator parameters into string identifier.

        Parameters
        ----------
        items : list[Any]
            Generator metadata and parameters.

        Returns
        -------
        str
            Joined string representation of parameters.
        """
        return "_".join(str(x) for x in items)

    @staticmethod
    @abstractmethod
    def generate(size: int):
        """Generate random sample.

        Parameters
        ----------
        size : int
            Sample size.

        Returns
        -------
        Any
            Generated random sample.
        """
        raise NotImplementedError
