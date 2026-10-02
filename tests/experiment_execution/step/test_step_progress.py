"""Progress stays active during final saving and renders console snapshots."""

from io import StringIO

import pytest
from rich.console import Console
from rich.progress import Progress

from pysatl_experiment.experiment_execution.step import progress as module


@pytest.mark.parametrize("terminal", [False, True])
def test_display_updates_before_exit_and_waits_for_save(terminal, monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    output = StringIO()
    console = Console(file=output, width=200, force_terminal=terminal, force_interactive=terminal)
    monkeypatch.setattr(module, "get_rich_console", lambda **kwargs: console)
    clock = [0.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        module, "Progress", lambda *args, **kwargs: Progress(*args, get_time=lambda: clock[0], **kwargs)
    )
    with module.StepProgress(2, description="Computing", processed_label="Tasks") as display:
        assert "Tasks: 0/2" in output.getvalue()
        clock[0] = 2.0
        display.processed(2)
        assert "Saving results" in output.getvalue()
        assert "Done" not in output.getvalue()
        task = display.progress.tasks[0]
        assert task.fields["state"] == "running"
        clock[0] = 5.0
        # The timer includes saving, even though the computation bar is at 100%.
        assert str(display.progress.columns[-1].render(task)) == "0:00:05"
        display.saved(2)
    assert "Done" in output.getvalue()
    assert "Saved: 2/2" in output.getvalue()
    assert task.fields["state"] == "done"
    assert not display.progress.live.is_started
    if not terminal:
        assert "\x1b" not in output.getvalue()


def test_plain_output_throttles_updates_but_keeps_initial_and_final_states(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    output = StringIO()
    monkeypatch.setattr(
        module, "get_rich_console", lambda **kwargs: Console(file=output, width=200, force_terminal=False)
    )
    clock = [0.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])
    with module.StepProgress(5, description="Computing", processed_label="Tasks") as display:
        initial = output.getvalue()
        display.processed(1)
        display.saved(1)
        assert output.getvalue() == initial
        clock[0] = 1.0
        display.processed(1)
        assert "Tasks: 2/5" in output.getvalue()
        display.processed(3)
        display.saved(4)
    assert "Tasks: 0/5" in output.getvalue()
    assert "Saving results" in output.getvalue()
    assert "Saved: 5/5" in output.getvalue()


def test_keyboard_interrupt_closes_display_without_success(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    output = StringIO()
    monkeypatch.setattr(
        module, "get_rich_console", lambda **kwargs: Console(file=output, width=200, force_terminal=True)
    )
    with (
        pytest.raises(KeyboardInterrupt),
        module.StepProgress(2, description="Computing", processed_label="Tasks") as display,
    ):
        display.processed(1)
        raise KeyboardInterrupt
    assert "Interrupted" in output.getvalue()
    assert "Done" not in output.getvalue()
    assert not display.progress.live.is_started
