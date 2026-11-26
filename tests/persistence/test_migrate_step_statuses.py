"""Tests for the step status database migration."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from pysatl_experiment.persistence.migrations.migrate_step_statuses import migrate_step_statuses


def _create_legacy_db(db_path: Path) -> None:
    """Create a database with the pre-status boolean flag schema."""
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "CREATE TABLE experiments ("
            "id INTEGER PRIMARY KEY, "
            "is_generation_done INTEGER DEFAULT 0, "
            "is_execution_done INTEGER DEFAULT 0, "
            "is_report_building_done INTEGER DEFAULT 0)"
        )
        connection.execute(
            "INSERT INTO experiments (id, is_generation_done, is_execution_done, is_report_building_done) "
            "VALUES (1, 1, 0, 1)"
        )
        connection.execute(
            "INSERT INTO experiments (id, is_generation_done, is_execution_done, is_report_building_done) "
            "VALUES (2, 0, 0, 0)"
        )
        connection.commit()
    finally:
        connection.close()


def _columns(db_path: Path) -> set[str]:
    connection = sqlite3.connect(db_path)
    try:
        return {row[1] for row in connection.execute("PRAGMA table_info(experiments)")}
    finally:
        connection.close()


def _rows(db_path: Path) -> list[tuple]:
    connection = sqlite3.connect(db_path)
    try:
        return list(
            connection.execute(
                "SELECT id, generation_status, execution_status, report_building_status, "
                "tasks_failed, tasks_total FROM experiments ORDER BY id"
            )
        )
    finally:
        connection.close()


# Checks that boolean flags are migrated to statuses and dropped afterwards.
def test_migration_backfills_statuses_and_drops_flags(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    _create_legacy_db(db_path)

    migrate_step_statuses(str(db_path))

    columns = _columns(db_path)
    assert "generation_status" in columns
    assert "execution_status" in columns
    assert "report_building_status" in columns
    assert "tasks_failed" in columns
    assert "tasks_total" in columns
    assert "is_generation_done" not in columns
    assert "is_execution_done" not in columns
    assert "is_report_building_done" not in columns

    assert _rows(db_path) == [
        (1, "done", "pending", "done", None, None),
        (2, "pending", "pending", "pending", None, None),
    ]


# Checks that a repeated migration run keeps the migrated data intact.
def test_migration_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    _create_legacy_db(db_path)

    migrate_step_statuses(str(db_path))
    migrate_step_statuses(str(db_path))

    assert _rows(db_path) == [
        (1, "done", "pending", "done", None, None),
        (2, "pending", "pending", "pending", None, None),
    ]


# Checks that the migration leaves non-status column data untouched.
def test_migration_keeps_other_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "CREATE TABLE experiments (id INTEGER PRIMARY KEY, hypothesis TEXT, is_generation_done INTEGER DEFAULT 0)"
        )
        connection.execute("INSERT INTO experiments (id, hypothesis, is_generation_done) VALUES (1, 'normal', 1)")
        connection.commit()
    finally:
        connection.close()

    migrate_step_statuses(str(db_path))

    connection = sqlite3.connect(db_path)
    try:
        rows = list(connection.execute("SELECT id, hypothesis, generation_status FROM experiments"))
    finally:
        connection.close()

    assert rows == [(1, "normal", "done")]


# Checks that a database without the experiments table is left alone.
def test_migration_without_experiments_table_is_noop(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("CREATE TABLE other (id INTEGER PRIMARY KEY)")
        connection.commit()
    finally:
        connection.close()

    migrate_step_statuses(str(db_path))

    connection = sqlite3.connect(db_path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        connection.close()

    assert tables == {"other"}


# Checks that a database already on the new schema is not modified.
def test_migration_on_current_schema_is_noop(tmp_path: Path) -> None:
    db_path = tmp_path / "current.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "CREATE TABLE experiments ("
            "id INTEGER PRIMARY KEY, "
            "generation_status TEXT NOT NULL DEFAULT 'pending', "
            "execution_status TEXT NOT NULL DEFAULT 'pending', "
            "report_building_status TEXT NOT NULL DEFAULT 'pending', "
            "tasks_failed INTEGER, "
            "tasks_total INTEGER)"
        )
        connection.execute(
            "INSERT INTO experiments (id, generation_status, execution_status, report_building_status, "
            "tasks_failed, tasks_total) VALUES (1, 'running', 'failed', 'pending', 3, 10)"
        )
        connection.commit()
    finally:
        connection.close()

    migrate_step_statuses(str(db_path))

    assert _rows(db_path) == [(1, "running", "failed", "pending", 3, 10)]
