"""
Migrate the ``experiments`` table from boolean flags to step statuses.

Databases created before the step-status model store per-step completion
as boolean columns (``is_generation_done``, ``is_execution_done``,
``is_report_building_done``). The current schema tracks lifecycle statuses
(``generation_status``, ``execution_status``, ``report_building_status``)
with values ``pending`` / ``running`` / ``done`` / ``failed``.

This migration is idempotent:

1. Adds the status columns when they are missing.
2. Backfills ``done`` for steps whose boolean flag was set.
3. Drops the boolean columns once the backfill is applied.

Requires SQLite >= 3.35 (``DROP COLUMN`` support).

Usage
-----
``python -m pysatl_experiment.persistence.migrations.migrate_step_statuses <db_path>``
"""

import argparse
import sqlite3
from collections.abc import Sequence


_STEPS = ("generation", "execution", "report_building")


def migrate_step_statuses(db_path: str) -> None:
    """
    Migrate one SQLite database file to the step-status schema.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.
    """
    connection = sqlite3.connect(db_path)
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(experiments)")}
        if not columns:
            # No experiments table: nothing to migrate.
            return

        for step in _STEPS:
            status_column = f"{step}_status"
            flag_column = f"is_{step}_done"

            if status_column not in columns:
                connection.execute(
                    f"ALTER TABLE experiments ADD COLUMN {status_column} TEXT NOT NULL DEFAULT 'pending'"
                )

            if flag_column in columns:
                connection.execute(
                    f"UPDATE experiments SET {status_column} = 'done' "
                    f"WHERE {flag_column} = 1 AND {status_column} != 'done'"
                )
                connection.execute(f"ALTER TABLE experiments DROP COLUMN {flag_column}")

        connection.commit()
    finally:
        connection.close()


def main(argv: Sequence[str] | None = None) -> None:
    """
    Run the migration from the command line.

    Parameters
    ----------
    argv : Sequence[str] | None, optional
        Command-line arguments; defaults to ``sys.argv``.
    """
    parser = argparse.ArgumentParser(description="Migrate experiments table to step statuses.")
    parser.add_argument("db_path", help="Path to the SQLite database file.")
    args = parser.parse_args(argv)

    migrate_step_statuses(args.db_path)


if __name__ == "__main__":
    main()
