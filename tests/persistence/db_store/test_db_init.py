"""Tests for database initialization and session-scoping utilities."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool

from pysatl_experiment.exceptions import OperationalException
from pysatl_experiment.persistence.db_store import db_init as db_init_module
from pysatl_experiment.persistence.db_store.db_init import get_request_or_thread_id, init_db


# Checks that the legacy three-slash SQLite URL is rejected with actionable guidance.
def test_init_db_rejects_legacy_in_memory_sqlite_url() -> None:
    with pytest.raises(OperationalException, match=r"For in-memory database, please use `sqlite://`"):
        init_db("sqlite:///")


# Checks that unparsable or unknown-dialect URLs are reported as invalid.
@pytest.mark.parametrize(
    "db_url",
    [
        pytest.param("", id="empty-url"),
        pytest.param("   ", id="blank-url"),
        pytest.param("no_such_dialect://host/db", id="unknown-dialect"),
    ],
)
def test_init_db_raises_for_invalid_url(db_url: str) -> None:
    with pytest.raises(OperationalException, match="is no valid database URL!"):
        init_db(db_url)


# Checks that the in-memory SQLite URL is configured with a StaticPool.
def test_init_db_uses_static_pool_for_in_memory_sqlite() -> None:
    engine = init_db("sqlite://")

    assert isinstance(engine, Engine)
    assert isinstance(engine.pool, StaticPool)
    assert engine.url.get_backend_name() == "sqlite"


# Checks that file-based SQLite engines can be shared across threads.
def test_init_db_disables_same_thread_check_for_file_sqlite(tmp_path: Path) -> None:
    engine = init_db(f"sqlite:///{tmp_path / 'db.sqlite'}")

    assert not isinstance(engine.pool, StaticPool)
    with ThreadPoolExecutor(max_workers=1) as executor:
        databases = list(executor.map(lambda _: engine.connect().exec_driver_sql("SELECT 1").scalar(), range(2)))

    assert databases == [1, 1]


# Checks that non-``sqlite://`` URLs keep the default connection checks.
def test_init_db_keeps_same_thread_check_for_non_sqlite_urls() -> None:
    engine = init_db("sqlite+pysqlite://")

    assert engine.dialect.name == "sqlite"
    assert engine.dialect.create_connect_args(engine.url)[1]["check_same_thread"] is True


# Checks that the request identifier falls back to the current thread identifier.
def test_get_request_or_thread_id_falls_back_to_thread_id() -> None:
    db_init_module._request_id_ctx_var.set(None)

    request_id = get_request_or_thread_id()

    assert isinstance(request_id, str)
    assert request_id.isdigit()


# Checks that a request identifier stored in the context takes precedence.
def test_get_request_or_thread_id_prefers_request_context() -> None:
    token = db_init_module._request_id_ctx_var.set("request-42")

    try:
        assert get_request_or_thread_id() == "request-42"
    finally:
        db_init_module._request_id_ctx_var.reset(token)
