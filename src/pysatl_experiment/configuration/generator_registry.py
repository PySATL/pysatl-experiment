"""
Central registry for random-value-sample generators.

This is the single place that discovers concrete ``AbstractRVSGenerator``
subclasses and maps between generator names and distribution types. Both the
CLI validation layer and the experiment factories rely on it, so the discovery
and mapping logic lives in one place instead of being duplicated.
"""

import importlib

from pysatl_criterion import DistributionType
from pysatl_criterion.generator.model import AbstractRVSGenerator


_GENERATORS_MODULE = "pysatl_criterion.generator.generators"


def get_generator_classes() -> list[type[AbstractRVSGenerator]]:
    """Return all concrete (non-abstract) RVS generator subclasses."""
    importlib.import_module(_GENERATORS_MODULE)
    return sorted(
        (cls for cls in AbstractRVSGenerator.__subclasses__() if not getattr(cls, "__abstractmethods__", None)),
        key=lambda cls: cls.__name__,
    )


def generator_name_to_distribution() -> dict[str, DistributionType]:
    """
    Map generator names (and distribution values) to their DistributionType.

    Both the generator class name and the distribution value are accepted as
    keys and resolve to the same :class:`DistributionType`.
    """
    mapping: dict[str, DistributionType] = {}
    for cls in get_generator_classes():
        try:
            distribution_type = cls.distribution_type()
        except (AttributeError, NotImplementedError):
            continue
        mapping[cls.__name__.upper()] = distribution_type
        mapping[distribution_type.value.upper()] = distribution_type
    return mapping


def to_code(distribution_type: DistributionType | str) -> str:
    """
    Return the canonical storage-safe code for a distribution.

    Normalizes any representation to a single lowercase value::

        DistributionType.NORMAL   -> "normal"
        "DistributionType.NORMAL" -> "normal"
        "NORMAL"                  -> "normal"
        "normal"                  -> "normal"
    """
    if isinstance(distribution_type, DistributionType):
        return distribution_type.value
    code = str(distribution_type)
    if "." in code:
        code = code.split(".")[-1]
    return code.lower()
