"""Scheduler preserves task context and result types."""

from mypy import api


SOURCE = """
from collections.abc import Iterator
from concurrent.futures import Future
from dataclasses import dataclass
from pysatl_experiment.parallel import Scheduler

@dataclass
class Context:
    value: int = 0

def compute(context: Context) -> str:
    return str(context.value)

def incompatible(context: int) -> str:
    return str(context)

with Scheduler(2, Context) as scheduler:
    future: Future[str] = scheduler.submit(compute)
    results: list[str] = scheduler.run([compute])
    iterator: Iterator[str] = scheduler.iterate_results([compute])
"""


def test_scheduler_checks_context_and_result_types(tmp_path):
    path = tmp_path / "scheduler_usage.py"
    args = ["--follow-imports=silent", "--cache-dir", str(tmp_path / "cache"), str(path)]
    path.write_text(SOURCE)
    stdout, stderr, status = api.run(args)
    assert status == 0, stdout + stderr

    path.write_text(SOURCE.replace("scheduler.submit(compute)", "scheduler.submit(incompatible)"))
    stdout, stderr, status = api.run(args)
    assert status == 1, stdout + stderr
    assert "arg-type" in stdout

    path.write_text(SOURCE.replace("results: list[str]", "results: list[int]"))
    stdout, stderr, status = api.run(args)
    assert status == 1, stdout + stderr
