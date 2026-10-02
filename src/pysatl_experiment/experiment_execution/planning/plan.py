"""Generic task plan with no dependencies on concrete experiment steps."""

from dataclasses import dataclass
from typing import Generic, TypeVar


GenerationTaskT = TypeVar("GenerationTaskT")
ExecutionTaskT = TypeVar("ExecutionTaskT")


@dataclass(frozen=True)
class ExperimentTaskPlan(Generic[GenerationTaskT, ExecutionTaskT]):
    """Prepared tasks; None disables an already completed step."""

    generation: list[GenerationTaskT] | None
    execution: list[ExecutionTaskT] | None
