"""Tests for the JSON log record formatter."""

import json
import logging
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from pysatl_experiment.loggers.json_formatter import JsonFormatter


DEFAULT_FMT_DICT = {
    "timestamp": "asctime",
    "level": "levelname",
    "logger": "name",
    "message": "message",
}

TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def make_record(**overrides: object) -> logging.LogRecord:
    """Build a log record with sensible defaults, applying the overrides last."""
    values: dict[str, object] = {
        "name": "test_logger",
        "level": logging.INFO,
        "pathname": __file__,
        "lineno": 7,
        "msg": "hello %s",
        "args": ("world",),
        "exc_info": None,
    }
    values.update(overrides)

    return logging.LogRecord(**values)  # type: ignore[arg-type]


def make_raises():
    """Capture a real exception triplet for exception related tests."""
    try:
        raise ValueError("boom")
    except ValueError:
        return sys.exc_info()


# Checks that the formatter subclasses the standard logging formatter.
def test_formatter_extends_logging_formatter() -> None:
    assert issubclass(JsonFormatter, logging.Formatter)
    assert isinstance(JsonFormatter(), logging.Formatter)


# Checks that the default field mapping matches the documented schema.
def test_default_fmt_dict_matches_documented_schema() -> None:
    assert JsonFormatter().fmt_dict == DEFAULT_FMT_DICT


# Checks that a caller supplied field mapping is stored as-is, including an empty one.
@pytest.mark.parametrize(
    "fmt_dict",
    [
        {},
        {"message": "message"},
        {"time": "asctime", "text": "msg"},
        {"level": "levelname", "path": "pathname", "line": "lineno"},
    ],
)
def test_custom_fmt_dict_is_stored_as_is(fmt_dict: dict[str, str]) -> None:
    formatter = JsonFormatter(fmt_dict)

    assert formatter.fmt_dict is fmt_dict


# Checks that the default timestamp formats and a disabled datefmt are stored.
def test_default_time_formats_are_stored() -> None:
    formatter = JsonFormatter()

    assert formatter.default_time_format == "%Y-%m-%dT%H:%M:%S"
    assert formatter.default_msec_format == "%s.%03dZ"
    assert formatter.datefmt is None


# Checks that custom timestamp formats are honoured by the formatter.
@pytest.mark.parametrize(
    ("time_format", "msec_format"),
    [("%Y", ""), ("%H:%M:%S", "%s.%03d+00:00"), ("%d-%m-%Y", "%sZ")],
)
def test_custom_time_formats_are_stored(time_format: str, msec_format: str) -> None:
    formatter = JsonFormatter(time_format=time_format, msec_format=msec_format)

    assert formatter.default_time_format == time_format
    assert formatter.default_msec_format == msec_format


# Checks that timestamp generation is requested when asctime is mapped.
def test_uses_time_is_true_for_asctime_mapping() -> None:
    assert JsonFormatter().usesTime() is True
    assert JsonFormatter({"time": "asctime"}).usesTime() is True


# Checks that timestamp generation is skipped when asctime is not mapped.
@pytest.mark.parametrize("fmt_dict", [{}, {"message": "message"}, {"level": "levelname", "logger": "name"}])
def test_uses_time_is_false_without_asctime_mapping(fmt_dict: dict[str, str]) -> None:
    assert JsonFormatter(fmt_dict).usesTime() is False


# Checks that the string based formatting hook is intentionally disabled.
def test_format_message_raises_not_implemented_error() -> None:
    with pytest.raises(NotImplementedError):
        JsonFormatter().formatMessage(make_record())


# Checks that the record dictionary maps configured keys onto record attributes.
def test_format_message_dict_maps_configured_fields() -> None:
    record = make_record(msg="payload")
    record.custom_value = "extra"  # type: ignore[attr-defined]
    formatter = JsonFormatter({"text": "msg", "extra": "custom_value", "level": "levelname"})

    assert formatter.format_message_dict(record) == {
        "text": "payload",
        "extra": "extra",
        "level": "INFO",
    }


# Checks that unknown record attributes raise a KeyError.
def test_format_message_dict_raises_key_error_for_unknown_attribute() -> None:
    formatter = JsonFormatter({"missing": "does_not_exist"})

    with pytest.raises(KeyError, match="does_not_exist"):
        formatter.format_message_dict(make_record())


# Checks that formatting produces valid JSON with the default schema fields.
def test_format_returns_json_with_default_fields() -> None:
    payload = json.loads(JsonFormatter().format(make_record()))

    assert set(payload) == set(DEFAULT_FMT_DICT)
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test_logger"
    assert payload["message"] == "hello world"


# Checks that the default timestamp uses the configured date and millisecond formats.
def test_format_timestamp_uses_default_format() -> None:
    payload = json.loads(JsonFormatter().format(make_record()))

    assert TIMESTAMP_PATTERN.match(payload["timestamp"])


# Checks that a custom timestamp template is applied to the emitted value.
def test_format_timestamp_honours_custom_formats() -> None:
    formatter = JsonFormatter(time_format="%Y", msec_format="%s-%03d-ms")
    payload = json.loads(formatter.format(make_record()))

    assert re.fullmatch(r"\d{4}-\d{3}-ms", payload["timestamp"])


# Checks that the millisecond suffix is omitted when the template is empty.
def test_format_timestamp_without_millisecond_template() -> None:
    formatter = JsonFormatter(time_format="%Y-%m-%d", msec_format="")
    payload = json.loads(formatter.format(make_record()))

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", payload["timestamp"])


# Checks that no timestamp field is added when asctime is not part of the schema.
def test_format_skips_timestamp_when_not_mapped() -> None:
    record = make_record()
    payload = json.loads(JsonFormatter({"message": "message"}).format(record))

    assert payload == {"message": "hello world"}
    assert not hasattr(record, "asctime")


# Checks that exception details are rendered into the exc_info field.
def test_format_includes_exception_info() -> None:
    record = make_record(exc_info=make_raises())

    payload = json.loads(JsonFormatter().format(record))

    assert "ValueError: boom" in payload["exc_info"]
    assert record.exc_text == payload["exc_info"]


# Checks that an already cached traceback text is reused without re-formatting it.
def test_format_reuses_cached_exception_text() -> None:
    record = make_record(exc_info=make_raises())
    record.exc_text = "cached traceback"
    formatter = JsonFormatter()

    with patch.object(formatter, "formatException") as format_exception:
        payload = json.loads(formatter.format(record))

    format_exception.assert_not_called()
    assert payload["exc_info"] == "cached traceback"


# Checks that stack information is added to the payload when present.
def test_format_includes_stack_info() -> None:
    record = make_record()
    record.stack_info = "custom stack frame"

    payload = json.loads(JsonFormatter().format(record))

    assert "custom stack frame" in payload["stack_info"]


# Checks that exception and stack fields are absent for a plain record.
def test_format_omits_exception_and_stack_fields_when_absent() -> None:
    payload = json.loads(JsonFormatter().format(make_record()))

    assert "exc_info" not in payload
    assert "stack_info" not in payload


# Checks that non-serializable values fall back to their string representation.
def test_format_serializes_non_serializable_values_with_str_fallback() -> None:
    record = make_record()
    record.object_value = Path("some/dir")  # type: ignore[attr-defined]
    payload = json.loads(JsonFormatter({"value": "object_value"}).format(record))

    assert payload == {"value": str(Path("some/dir"))}


# Checks that the result is a single line JSON string.
def test_format_returns_single_line_string() -> None:
    result = JsonFormatter().format(make_record())

    assert isinstance(result, str)
    assert "\n" not in result
