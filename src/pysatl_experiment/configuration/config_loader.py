"""Read configuration documents without validating their contents."""

import json
from pathlib import Path

from .raw_experiment_config import RawExperimentConfig
from .validation.config_errors import ConfigReadError


def read_raw_experiment_config(path: str | Path) -> RawExperimentConfig:
    """Read any JSON root, reporting syntax errors with line and column."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigReadError(f"{source}:{error.lineno}:{error.colno}: invalid JSON: {error.msg}") from error
    except (OSError, UnicodeError) as error:
        raise ConfigReadError(f"Cannot read {source}: {error}") from error
    return RawExperimentConfig(data)
