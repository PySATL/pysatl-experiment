"""
Garbage collector tuning helpers.

This module reduces the frequency of garbage collector passes for
allocation-heavy experiment runs (sample generation, large result
lists, report rendering).
"""

import gc
import logging
import platform


logger = logging.getLogger(__name__)


def gc_set_threshold() -> None:
    """
    Reduce the number of garbage collector runs to improve performance.

    Applies relaxed generation thresholds recommended for allocation-heavy
    workloads.

    Notes
    -----
    Only the frequency of collector runs is reduced: the garbage collector
    stays enabled, so cyclic garbage is still collected. Thresholds are
    changed on CPython only; other implementations keep their defaults.
    """
    if platform.python_implementation() == "CPython":
        gc.set_threshold(50_000, 500, 1000)
        logger.debug("GC thresholds adjusted to %s to reduce GC runs", gc.get_threshold())
    else:
        logger.debug("GC threshold tuning skipped: non-CPython implementation")
