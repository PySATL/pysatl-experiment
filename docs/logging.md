# Logging

PySATL Experiment uses the standard Python `logging` module as its logging backend, with a preconfigured console handler for human-readable output and an optional JSON-formatted rotating file handler for machine processing.

## Quick Start

Logging is configured automatically when you run an experiment:

```bash
# Default verbosity (WARNING)
experiment build-and-run my_experiment

# Verbose output
experiment build-and-run my_experiment --log-level DEBUG

# Additionally write JSON logs to a rotating file
experiment build-and-run my_experiment --log-level INFO --log-file experiment.log
```

| Option | Default | Description |
|---|---|---|
| `--log-level` | `WARNING` | Minimum level for emitted records (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `--log-file` | _(none)_ | Path to a log file. Enables a `RotatingFileHandler` (10 MB × 5 backups, UTF-8). |

## Output Destinations

### Console

Console output is rendered by a Rich-based handler and stays human-readable:

```text
2026-11-22 01:30:44,189 - pysatl_experiment.experiment_execution.experiment - INFO - [experiment_id=42, step=generation] Running generation step...
```

### Log file (JSON lines)

Every line in the log file is a self-contained JSON object:

```json
{"timestamp": "2026-11-22T01:30:44.189Z", "level": "INFO", "logger": "pysatl_experiment.experiment_execution.experiment", "message": "[experiment_id=42, step=generation] Running generation step...", "experiment_id": 42, "step": "generation"}
```

Standard fields: `timestamp`, `level`, `logger`, `message`. Additional fields:

- `exc_info` — full traceback text when the record carries exception information;
- `stack_info` — stack information when present;
- **context fields** — any attributes attached via `extra` (see below), e.g. `experiment_id`, `step`, `worker_id`.

## Experiment Context

The experiment runner attaches context to every record it emits via `ExperimentContextAdapter`:

- `experiment_id` — the running experiment's identifier;
- `step` — the pipeline step (`generation`, `execution`, `report_building`).

The context appears twice: as a `[key=value, ...]` prefix in the message (visible in console output regardless of formatting) and as structured fields in JSON logs (suitable for filtering in log aggregation pipelines).

## Logging From Your Code

Use a module-level logger — it will be picked up by the central configuration:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing batch %d", batch_number)
logger.exception("Failed to generate chart")
```

Guidelines:

- Do **not** call `logging.basicConfig` or add handlers yourself — `setup_logging()` owns the configuration.
- Use `logger.exception(...)` inside `except` blocks to preserve tracebacks.
- Attach structured context through `extra` instead of embedding values into the message when the data is useful for filtering:

```python
from pysatl_experiment.loggers.context import ExperimentContextAdapter

log = ExperimentContextAdapter(logger, {"experiment_id": experiment_id})
log.info("Running generation step...", extra={"step": "generation"})
```

## Verbosity Details

- The requested level is applied both to handlers and to the root logger, so `--log-level DEBUG` actually lets `DEBUG` records through.
- Noisy third-party loggers (`matplotlib`, `PIL`, `numexpr`) are pinned to `WARNING` and are not affected by `--log-level`.
- Loggers created at import time stay enabled (`disable_existing_loggers: False`).

## Uncaught Exceptions

The CLI installs a `sys.excepthook` that logs uncaught exceptions at `CRITICAL` level with a full traceback, so crashes are recorded in the log file instead of only appearing on stderr. `KeyboardInterrupt` keeps its standard behavior.

## Custom Configuration

Advanced users can supply a full [`dictConfig`](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema) schema via the `log_config` key of the experiment configuration. When `--log-file` is passed, the rotating JSON file handler is added on top of that configuration.

## Parallel Execution

The setup is thread-safe by construction (stdlib logging guarantee). For multiprocess execution (`Scheduler` / `ProcessPoolExecutor`), logging is forwarded through a `QueueHandler`/`QueueListener` pair (`pysatl_experiment.loggers.multiprocessing`):

- In the parent process, `WorkerLogListener` owns a shared queue and re-emits every incoming record through the parent's configured handlers (rich console and/or JSON file), so handlers stay single-process.
- In each worker process, `configure_worker_logging` (passed to `Scheduler` as `worker_initializer`) replaces the root handlers with a single `QueueHandler` and applies the parent's root level, so `--log-level DEBUG` also affects workers.

Execution steps based on `MultithreadingExecutionStep` get this wiring automatically.

Records emitted in a worker are stamped with a `worker_id` field (the worker's PID; exported to JSON logs like other context fields). A caller-supplied `worker_id` (e.g. a logical index passed via `extra`) is never overwritten by the automatic stamp.
