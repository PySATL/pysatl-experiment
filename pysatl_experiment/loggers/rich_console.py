"""
Rich console utilities for terminal output configuration.

This module provides helper functions for creating and configuring
Rich-based console instances used in logging and CLI output.

The module is primarily used by the logging subsystem to ensure
consistent colored output across different execution environments.

Notes
-----
Console width detection is environment-aware and falls back to a
safe default when terminal size cannot be determined.
"""

import sys
from shutil import get_terminal_size

from rich.console import Console


def console_width() -> int | None:
    """
    Determine appropriate console width for Rich output.

    The function attempts to detect the current terminal width and
    applies environment-specific overrides for testing and notebook
    environments.

    Returns
    -------
    int | None
        Console width in characters, or ``None`` if Rich should use
        automatic width detection.

    Notes
    -----
    The function is designed to prevent line wrapping issues in CI
    environments and notebooks.
    """
    if any(module in ["pytest", "ipykernel"] for module in sys.modules):
        return 200

    width, _ = get_terminal_size((1, 24))
    # Fall back to 200 if terminal size is not available.
    # This is determined by assuming an insane width of 1char, which is unlikely.
    w = None if width > 1 else 200
    return w


def get_rich_console(**kwargs) -> Console:
    """
    Create a configured Rich Console instance.

    This factory function creates a Rich Console with a predefined
    width configuration suitable for logging and CLI output.

    Parameters
    ----------
    **kwargs
        Additional keyword arguments passed directly to
        ``rich.console.Console``.

    Returns
    -------
    Console
        Configured Rich Console instance.

    Notes
    -----
    If no width is provided explicitly, the function uses the value
    returned by ``console_width()``.
    """
    kwargs["width"] = kwargs.get("width", console_width())
    return Console(**kwargs)


# TODO: make default width configurable via application settings
# TODO: improve code by removing magical numbers
