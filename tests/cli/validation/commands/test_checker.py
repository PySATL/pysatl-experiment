"""Tests for the SQLite critical value checker."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from pysatl_experiment.cli.validation.commands.checker import SQLiteCriticalValueChecker


@pytest.fixture
def sqlite_url(tmp_path: Path) -> str:
    """Create a temporary SQLite database with an empty limit_distributions table."""
    db_path = tmp_path / "critical_values.sqlite"
    url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE limit_distributions (criterion_code TEXT, sample_size INTEGER)"))
    engine.dispose()
    return url


def _insert(url: str, criterion_code: str, sample_size: int) -> None:
    """Insert a single critical-value row into the temporary database."""
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO limit_distributions (criterion_code, sample_size) VALUES (:code, :size)"),
            {"code": criterion_code, "size": sample_size},
        )
    engine.dispose()


# Checks that a valid connection string is stored and a live engine is opened.
def test_init_connects_and_stores_engine(sqlite_url: str) -> None:
    checker = SQLiteCriticalValueChecker(sqlite_url)

    assert checker.connection_string == sqlite_url
    assert checker.engine is not None


# Checks check_exists returns True for a stored (criterion, sample size) pair.
def test_check_exists_true_for_present_row(sqlite_url: str) -> None:
    _insert(sqlite_url, "KS_NORMALITY_GOODNESS_OF_FIT", 100)
    checker = SQLiteCriticalValueChecker(sqlite_url)

    assert checker.check_exists("KS_NORMALITY_GOODNESS_OF_FIT", 100) is True


# Checks check_exists returns False when no matching row exists.
def test_check_exists_false_for_absent_row(sqlite_url: str) -> None:
    _insert(sqlite_url, "KS", 100)
    checker = SQLiteCriticalValueChecker(sqlite_url)

    assert checker.check_exists("KS", 200) is False


# Checks that the sample size participates in the lookup key.
def test_check_exists_distinguishes_sample_size(sqlite_url: str) -> None:
    _insert(sqlite_url, "AD", 50)
    checker = SQLiteCriticalValueChecker(sqlite_url)

    assert checker.check_exists("AD", 50) is True
    assert checker.check_exists("AD", 51) is False


# Checks check_exists returns False when no engine was ever established.
def test_check_exists_false_without_engine(sqlite_url: str) -> None:
    checker = SQLiteCriticalValueChecker(sqlite_url)
    checker.engine = None

    assert checker.check_exists("KS", 100) is False


# Checks that an unusable connection string is surfaced as a ConnectionError.
@pytest.mark.parametrize("connection_string", ["invalid://", "sqlite:////no_such_dir_zzz/db.sqlite"])
def test_init_raises_connection_error(connection_string: str) -> None:
    with pytest.raises(ConnectionError):
        SQLiteCriticalValueChecker(connection_string)
