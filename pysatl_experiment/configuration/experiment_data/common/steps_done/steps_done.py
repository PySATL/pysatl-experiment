from dataclasses import dataclass


@dataclass
class StepsDone:
    is_generation_step_done: bool
    is_execution_step_done: bool
    is_report_building_step_done: bool
