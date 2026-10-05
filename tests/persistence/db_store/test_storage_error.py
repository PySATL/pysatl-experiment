"""Tests for storage error wrapping during engine creation."""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

from pysatl_experiment.exceptions import OperationalException, StorageError
from pysatl_experiment.persistence.db_store.db_init import init_db


# Checks that StorageError stays compatible with the operational exception hierarchy.
def test_storage_error_is_an_operational_exception() -> None:
    assert issubclass(StorageError, OperationalException)


# Checks that driver-level failures raised while creating the engine surface as StorageError.
def test_init_db_wraps_driver_errors_into_storage_error() -> None:
    driver_errors = (
        OperationalError("SELECT 1", {}, Exception("connection lost")),
        ProgrammingError("SELECT 1", {}, Exception("missing table")),
        IntegrityError("INSERT INTO t", {}, Exception("duplicate key")),
    )

    for driver_error in driver_errors:
        with patch("pysatl_experiment.persistence.db_store.db_init.create_engine", side_effect=driver_error):
            with pytest.raises(StorageError, match="Storage error while creating the engine"):
                init_db("sqlite://")


# Checks that unrelated exceptions are not swallowed by the storage wrapper.
def test_init_db_propagates_unrelated_engine_errors() -> None:
    with patch("pysatl_experiment.persistence.db_store.db_init.create_engine", side_effect=ValueError("boom")):
        with pytest.raises(ValueError, match="boom"):
            init_db("sqlite://")
