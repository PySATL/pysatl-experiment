"""Stable sample-series identifiers built from configured distribution parameters."""

from collections.abc import Mapping
from math import isfinite


def _number(value: float) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError("Generator parameters must be finite numbers")
    return str(float(value) if value != 0 else 0.0)


def make_generator_code(distribution_type: str, parameters: Mapping[str, float | list[float]]) -> str:
    """Encode sorted named parameters, retaining ranges instead of sampled values.

    Parameters must include the generator's defaults. Numeric values are normalized
    so that integer and floating-point spellings identify the same series.
    """
    if not distribution_type or not distribution_type.strip():
        raise ValueError("distribution_type must be nonempty")
    parts = [distribution_type]
    for name, value in sorted(parameters.items()):
        if isinstance(value, list):
            if len(value) != 2:
                raise ValueError(f"{name}: parameter range must contain two bounds")
            lower, upper = (_number(bound) for bound in value)
            if value[0] > value[1]:
                raise ValueError(f"{name}: range lower bound must not exceed upper bound")
            encoded = f"[{lower},{upper}]"
        else:
            encoded = _number(value)
        parts.extend((name, encoded))
    return "_".join(parts)
