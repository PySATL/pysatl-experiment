"""Tests for Rich console creation and width detection."""

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from pysatl_experiment.loggers import rich_console
from pysatl_experiment.loggers.rich_console import console_width, get_rich_console


def make_module_mapping(*names: str) -> MagicMock:
    """Build a sys.modules double that contains only the given module names."""
    return MagicMock(modules=dict.fromkeys(names))


# Checks that pytest runs always receive the fixed wide console width.
def test_console_width_returns_200_under_pytest() -> None:
    with patch.object(rich_console, "get_terminal_size") as get_terminal_size:
        width = console_width()

    assert width == 200
    get_terminal_size.assert_not_called()


# Checks that notebook environments also receive the fixed wide console width.
def test_console_width_returns_200_under_ipykernel() -> None:
    with (
        patch.object(rich_console, "sys", make_module_mapping("ipykernel")),
        patch.object(
            rich_console,
            "get_terminal_size",
        ) as get_terminal_size,
    ):
        width = console_width()

    assert width == 200
    get_terminal_size.assert_not_called()


# Checks that a real terminal size lets Rich detect the width on its own.
@pytest.mark.parametrize("terminal_size", [(2, 24), (80, 24), (120, 40)])
def test_console_width_defers_to_rich_for_real_terminal_sizes(terminal_size: tuple[int, int]) -> None:
    with (
        patch.object(rich_console, "sys", MagicMock(modules={})),
        patch.object(
            rich_console,
            "get_terminal_size",
            return_value=terminal_size,
        ) as get_terminal_size,
    ):
        width = console_width()

    assert width is None
    get_terminal_size.assert_called_once_with((1, 24))


# Checks that degenerate terminal widths fall back to the fixed console width.
@pytest.mark.parametrize("terminal_size", [(1, 24), (0, 24), (-1, 24)])
def test_console_width_falls_back_for_degenerate_terminal_widths(terminal_size: tuple[int, int]) -> None:
    with (
        patch.object(rich_console, "sys", MagicMock(modules={})),
        patch.object(
            rich_console,
            "get_terminal_size",
            return_value=terminal_size,
        ),
    ):
        width = console_width()

    assert width == 200


# Checks that the factory returns a Rich Console instance.
def test_get_rich_console_returns_console_instance() -> None:
    assert isinstance(get_rich_console(width=42), Console)


# Checks that the factory applies the width reported by the detection helper.
def test_get_rich_console_uses_detected_width() -> None:
    with patch.object(rich_console, "console_width", return_value=200) as console_width_mock:
        console = get_rich_console()

    console_width_mock.assert_called_once_with()
    assert console.width == 200


# Checks that an explicit width wins over the width reported by the detection helper.
def test_get_rich_console_prefers_explicit_width() -> None:
    with patch.object(rich_console, "console_width", return_value=200):
        console = get_rich_console(width=42)

    assert console.width == 42


# Checks that a detected None width leaves Rich in automatic sizing mode.
def test_get_rich_console_accepts_none_width() -> None:
    with patch.object(rich_console, "console_width", return_value=None):
        console = get_rich_console()

    assert console._width is None


# Checks that remaining keyword arguments are forwarded to the Rich Console.
def test_get_rich_console_forwards_extra_kwargs() -> None:
    stream = StringIO()

    console = get_rich_console(width=42, file=stream, no_color=True, force_terminal=False)

    assert console.file is stream
    assert console.no_color is True
    assert console.width == 42


# Checks that the produced console writes rendered output to the provided stream.
def test_get_rich_console_writes_to_provided_stream() -> None:
    stream = StringIO()
    console = get_rich_console(width=42, file=stream, no_color=True, force_terminal=False)

    console.print("hello")

    assert stream.getvalue().strip() == "hello"
