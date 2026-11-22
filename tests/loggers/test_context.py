"""Tests for the experiment context logging adapter."""

import logging

from pysatl_experiment.loggers.context import ExperimentContextAdapter


def make_adapter(**extra: object) -> ExperimentContextAdapter:
    """Build an adapter over a stub logger with the given base context."""
    return ExperimentContextAdapter(logging.getLogger("test.context"), dict(extra))


# Checks that the base context is prepended to the message as a key=value prefix.
def test_process_prefixes_message_with_base_context() -> None:
    adapter = make_adapter(experiment_id=42)

    msg, kwargs = adapter.process("hello", {})

    assert msg == "[experiment_id=42] hello"
    assert kwargs["extra"] == {"experiment_id": 42}


# Checks that per-call extra is merged with the base context.
def test_process_merges_per_call_extra() -> None:
    adapter = make_adapter(experiment_id=42)

    msg, kwargs = adapter.process("hello", {"extra": {"step": "generation"}})

    assert msg == "[experiment_id=42, step=generation] hello"
    assert kwargs["extra"] == {"experiment_id": 42, "step": "generation"}


# Checks that per-call values override base context values.
def test_process_per_call_extra_overrides_base() -> None:
    adapter = make_adapter(experiment_id=42, step="generation")

    _, kwargs = adapter.process("hello", {"extra": {"step": "execution"}})

    assert kwargs["extra"] == {"experiment_id": 42, "step": "execution"}


# Checks that an empty context leaves the message untouched.
def test_process_without_context_keeps_message() -> None:
    adapter = make_adapter()

    msg, kwargs = adapter.process("hello", {})

    assert msg == "hello"
    assert kwargs["extra"] == {}


# Checks that other keyword arguments (e.g. exc_info) pass through unchanged.
def test_process_preserves_other_kwargs() -> None:
    adapter = make_adapter(experiment_id=42)

    _, kwargs = adapter.process("hello", {"exc_info": True, "stacklevel": 2})

    assert kwargs["exc_info"] is True
    assert kwargs["stacklevel"] == 2
    assert kwargs["extra"] == {"experiment_id": 42}


# Checks that context lands on the emitted record attributes end to end.
def test_adapter_attaches_context_to_records(caplog) -> None:
    adapter = make_adapter(experiment_id=42)

    with caplog.at_level(logging.INFO, logger="test.context"):
        adapter.info("ctx probe", extra={"step": "generation"})

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.message == "[experiment_id=42, step=generation] ctx probe"
    # Context fields are attached dynamically via the extra mechanism.
    assert record.experiment_id == 42  # type: ignore[attr-defined]
    assert record.step == "generation"  # type: ignore[attr-defined]
