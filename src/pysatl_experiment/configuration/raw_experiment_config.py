"""Unvalidated JSON configuration, before defaults and domain conversion."""

from copy import deepcopy
from typing import Any


_MISSING = object()


class RawExperimentConfig:
    """Keep JSON values and unknown keys intact, including absent and null fields.

    Step values remain dictionaries: their schema belongs to the selected
    experiment, not to this transport container. Missing attributes return None;
    ``to_dict`` still distinguishes missing keys from explicit JSON nulls.
    """

    def __init__(self, data: Any = _MISSING, **values: Any) -> None:
        if data is not _MISSING and values:
            raise TypeError("Pass either a document or keyword fields")
        self._values = deepcopy(values if data is _MISSING else data)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "RawExperimentConfig":
        """Copy a decoded JSON object without validating its values."""
        return cls(values)

    def to_data(self) -> Any:
        """Return an independent copy, including an invalid root value."""
        return deepcopy(self._values)

    def to_dict(self) -> dict[str, Any]:
        """Copy an object document; use to_data for arbitrary JSON roots."""
        if not isinstance(self._values, dict):
            raise TypeError("The raw document is not an object")
        return self.to_data()

    def has_field(self, name: str) -> bool:
        """Distinguish an absent field from an explicit null."""
        return isinstance(self._values, dict) and name in self._values

    def get(self, name: str) -> Any:
        """Copy a field value without exposing mutable source data."""
        if not isinstance(self._values, dict):
            return None
        return deepcopy(self._values.get(name))

    @property
    def experiment_name(self) -> Any:
        """Return the unvalidated experiment name."""
        return self.get("experiment_name")

    @property
    def storage_connection(self) -> Any:
        """Return the unvalidated storage connection."""
        return self.get("storage_connection")

    @property
    def experiment_type(self) -> Any:
        """Return the unvalidated experiment discriminator."""
        return self.get("experiment_type")

    @property
    def run_mode(self) -> Any:
        """Return the unvalidated run mode."""
        return self.get("run_mode")

    @property
    def generate(self) -> Any:
        """Return the unvalidated generation section."""
        return self.get("generate")

    @property
    def execute(self) -> Any:
        """Return the unvalidated execution section."""
        return self.get("execute")

    @property
    def report(self) -> Any:
        """Return the unvalidated report section."""
        return self.get("report")
