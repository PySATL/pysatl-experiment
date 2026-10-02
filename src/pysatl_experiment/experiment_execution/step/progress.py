"""Parent-process progress with live terminal and plain console output."""

from datetime import timedelta
from time import monotonic
from types import TracebackType
from typing import Literal

from rich.console import RenderableType
from rich.progress import BarColumn, Progress, ProgressColumn, Task, TaskProgressColumn, TextColumn
from rich.spinner import Spinner
from rich.text import Text

from pysatl_experiment.loggers.rich_console import get_rich_console


class _StatusColumn(ProgressColumn):
    """Keep animating through persistence, even after computations reach 100%."""

    def __init__(self) -> None:
        super().__init__()
        self.spinner = Spinner("dots")

    def render(self, task: Task) -> RenderableType:
        state = task.fields["state"]
        if state == "running":
            return self.spinner.render(task.get_time())
        return Text("✓" if state == "done" else "✗")


class _ElapsedColumn(ProgressColumn):
    """Include final persistence in the elapsed time."""

    def render(self, task: Task) -> Text:
        return Text(str(timedelta(seconds=max(0, int(task.elapsed or 0)))))


class StepProgress:
    """Track computation and persistence separately, including final saving.

    Noninteractive consoles receive snapshots at most once a second, plus
    the initial, saving and final states. No terminal control codes are forced.
    """

    def __init__(
        self,
        total: int,
        *,
        description: str,
        processed_label: str,
        advance_on: Literal["processed", "saved"] = "processed",
    ) -> None:
        self.console = get_rich_console(stderr=True)
        self.interactive = self.console.is_interactive
        self.advance_on = advance_on
        self.total = total
        self.processed_count = 0
        self.saved_count = 0
        self.description = description
        self.last_snapshot = 0.0
        self.progress = Progress(
            _StatusColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn(f"{processed_label}: {{task.fields[processed]}}/{{task.total:.0f}}"),
            TextColumn("Saved: {task.fields[saved]}/{task.total:.0f}"),
            _ElapsedColumn(),
            console=self.console,
            disable=not self.interactive,
        )
        self.task_id = self.progress.add_task(description, total=total, processed=0, saved=0, state="running")

    def __enter__(self) -> "StepProgress":
        """Show the initial state before any tasks are submitted."""
        self.progress.start()
        self._refresh(force=True)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Show success only after the caller has finished saving results."""
        try:
            self.progress.update(
                self.task_id,
                description="Done" if exc_type is None else "Interrupted",
                state="done" if exc_type is None else "interrupted",
            )
            self.progress.stop_task(self.task_id)
            self._refresh(force=True)
        finally:
            self.progress.stop()

    def processed(self, count: int) -> None:
        """Record results received from workers."""
        self.processed_count += count
        saving = self.processed_count == self.total
        self.progress.update(
            self.task_id,
            processed=self.processed_count,
            completed=self.processed_count if self.advance_on == "processed" else self.saved_count,
            description="Saving results" if saving else self.description,
        )
        self._refresh(force=saving)

    def saved(self, count: int) -> None:
        """Record results only after their storage operation succeeds."""
        self.saved_count += count
        self.progress.update(
            self.task_id,
            saved=self.saved_count,
            completed=self.saved_count if self.advance_on == "saved" else self.processed_count,
        )
        self._refresh()

    def _refresh(self, *, force: bool = False) -> None:
        if self.interactive:
            if force:
                self.progress.refresh()
            return
        now = monotonic()
        if force or now - self.last_snapshot >= 1.0:
            self.console.print(self.progress.get_renderable())
            self.console.file.flush()
            self.last_snapshot = now
