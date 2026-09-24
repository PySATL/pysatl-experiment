"""Shared numeric parameter type.

Interim module: the codebase mixes two representations of numeric parameters —
``dict[str, float]`` (keyword-style) and ``list[float]`` (positional-style).
This module is the single source of truth for the interim union type.
"""

from typing import TypeAlias


# TODO: interim type — the codebase mixes dict[str, float] (kwargs-style) and
#  list[float] (positional-style) parameter representations. Migrate to the
#  canonical list[float].
NumericParameters: TypeAlias = dict[str, float] | list[float]
