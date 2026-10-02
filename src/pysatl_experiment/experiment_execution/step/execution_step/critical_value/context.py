"""Execution settings without storage dependencies."""

from dataclasses import dataclass

from .task_spec import CriticalValueTask


@dataclass(frozen=True, slots=True)
class CriticalValueExecutionContext:
    """Prepared tasks and scheduling settings for one experiment."""

    experiment_name: str
    parallel_workers: int
    tasks: tuple[CriticalValueTask, ...]
    write_batch_size: int = 20

    def __post_init__(self) -> None:
        """Reject invalid scheduling and tasks belonging to another experiment."""
        if not isinstance(self.experiment_name, str) or not self.experiment_name.strip():
            raise ValueError("experiment_name must be a nonempty string")
        if (
            isinstance(self.parallel_workers, bool)
            or not isinstance(self.parallel_workers, int)
            or self.parallel_workers < 1
        ):
            raise ValueError("parallel_workers must be a positive integer")
        object.__setattr__(self, "tasks", tuple(self.tasks))
        if (
            isinstance(self.write_batch_size, bool)
            or not isinstance(self.write_batch_size, int)
            or self.write_batch_size <= 0
        ):
            raise ValueError("write_batch_size must be a positive integer")
        if any(task.sample_set.experiment_name != self.experiment_name for task in self.tasks):
            raise ValueError("All tasks must belong to the context experiment")
