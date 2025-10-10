import json
from unittest.mock import MagicMock, patch

import psycopg2
import pytest

from pysatl_experiment.persistence.model.experiment.experiment import ExperimentModel, ExperimentQuery
from pysatl_experiment.persistence.storage.experiment.sqlite.sqlite import SQLiteExperimentStorage


TABLE_NAME = "experiments"


class TestSQLiteExperimentStorage:
    @pytest.fixture
    def storage(self):
        return SQLiteExperimentStorage(connection_string="postgresql://test:test@localhost/test")

    @pytest.fixture
    def sample_experiment_model(self):  # TODO: check for format
        return ExperimentModel(
            experiment_type="statistical_test",
            storage_connection="test.db",
            run_mode="sequential",
            report_mode="detailed",
            hypothesis="Test hypothesis",
            generator_type="monte_carlo",
            executor_type="multiprocessing",
            report_builder_type="html",
            sample_sizes=[100, 200, 300],
            monte_carlo_count=1000,
            criteria=["t_test", "mann_whitney"],
            alternatives=["two_sided", "greater"],
            significance_levels=[0.01, 0.05, 0.1],
            is_generation_done=False,
            is_execution_done=False,
            is_report_building_done=False,
        )

    @pytest.fixture
    def sample_experiment_query(self):  # TODO: check for format
        return ExperimentQuery(
            experiment_type="statistical_test",
            storage_connection="test.db",
            run_mode="sequential",
            hypothesis="Test hypothesis",
            generator_type="monte_carlo",
            executor_type="multiprocessing",
            report_builder_type="html",
            sample_sizes=[100, 200, 300],
            monte_carlo_count=1000,
            criteria=["t_test", "mann_whitney"],
            alternatives=["two_sided", "greater"],
            significance_levels=[0.01, 0.05, 0.1],
            report_mode="detailed",
        )

    def test_initialization(self, storage):
        assert storage.connection_string == "test.db"
        assert storage.table_name == TABLE_NAME
        assert not storage._initialized

    @patch("psycopg2.connect")
    def test_init_success(self, mock_connect, storage):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage.init()

        assert storage._initialized
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("psycopg2.connect")
    def test_init_already_initialized(self, mock_connect, storage):
        storage._initialized = True
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn

        storage.init()

        mock_conn.cursor.assert_not_called()

    @patch("psycopg2.connect")
    def test_init_failure(self, mock_connect, storage):
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            storage.init()

    @patch("psycopg2.connect")
    def test_insert_success(self, mock_connect, storage, sample_experiment_model):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage._initialized = True
        storage.insert_data(sample_experiment_model)

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("psycopg2.connect")
    def test_insert_auto_init(self, mock_connect, storage, sample_experiment_model):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage.insert_data(sample_experiment_model)

        # Must be 2 counts
        assert mock_cursor.execute.call_count == 2
        assert storage._initialized

    @patch("psycopg2.connect")
    def test_get_success(self, mock_connect, storage, sample_experiment_query):  # TODO: check for actual ones
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock query result
        mock_result = {
            "experiment_type": "statistical_test",
            "storage_connection": "postgresql://storage",
            "run_mode": "sequential",
            "report_mode": "detailed",
            "hypothesis": "Test hypothesis",
            "generator_type": "monte_carlo",
            "executor_type": "multiprocessing",
            "report_builder_type": "html",
            "sample_sizes": json.dumps([100, 200, 300]),
            "monte_carlo_count": 1000,
            "criteria": json.dumps(["t_test", "mann_whitney"]),
            "alternatives": json.dumps(["two_sided", "greater"]),
            "significance_levels": json.dumps([0.01, 0.05, 0.1]),
            "is_generation_done": False,
            "is_execution_done": False,
            "is_report_building_done": False,
        }
        mock_cursor.fetchone.return_value = mock_result

        storage._initialized = True
        result = storage.get_data(sample_experiment_query)

        assert result is not None
        assert result.experiment_type == sample_experiment_query.experiment_type
        mock_cursor.execute.assert_called_once()

    @patch("psycopg2.connect")
    def test_get_not_found(self, mock_connect, storage, sample_experiment_query):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None

        storage._initialized = True
        result = storage.get_data(sample_experiment_query)

        assert result is None

    @patch("psycopg2.connect")
    def test_delete_success(self, mock_connect, storage, sample_experiment_query):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage._initialized = True
        storage.delete_data(sample_experiment_query)

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    # TODO: do some proper test environment?

    @patch("psycopg2.connect")
    def test_get_experiment_id_success(self, mock_connect, storage, sample_experiment_query):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = (123,)

        storage._initialized = True
        result = storage.get_experiment_id(sample_experiment_query)

        assert result == 123

    @patch("psycopg2.connect")
    def test_set_generation_done(self, mock_connect, storage):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage._initialized = True
        storage.set_generation_done(123)

        mock_cursor.execute.assert_called_once()
        assert "is_generation_done" in mock_cursor.execute.call_args[0][0]
        mock_conn.commit.assert_called_once()

    @patch("psycopg2.connect")
    def test_set_execution_done(self, mock_connect, storage):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage._initialized = True
        storage.set_execution_done(123)

        mock_cursor.execute.assert_called_once()
        assert "is_execution_done" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_set_report_building_done(self, mock_connect, storage):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage._initialized = True
        storage.set_report_building_done(123)

        mock_cursor.execute.assert_called_once()
        assert "is_report_building_done" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_error_handling(self, mock_connect, storage, sample_experiment_model):
        mock_connect.side_effect = psycopg2.Error("Database error")

        storage._initialized = True

        with pytest.raises(psycopg2.Error, match="Database error"):
            storage.insert_data(sample_experiment_model)

    # TODO: logger tests


# Integration tests
@pytest.mark.integration
class TestSQLiteExperimentStorageIntegration:
    @pytest.fixture
    def integration_storage(self):
        # Should use real DB
        storage = SQLiteExperimentStorage(connection_string="postgresql://test:test@localhost/test_db")

        # Clearing before test
        with storage._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {storage.table_name}")
                conn.commit()

        yield storage

        # Clearing after test
        with storage._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {storage.table_name}")
                conn.commit()

    def test_integration_crud_operations(self, integration_storage, sample_experiment_model, sample_experiment_query):
        # Create
        integration_storage.insert_data(sample_experiment_model)

        # Read
        result = integration_storage.get_data(sample_experiment_query)
        assert result is not None
        assert result.experiment_type == sample_experiment_model.experiment_type

        # Get ID
        experiment_id = integration_storage.get_experiment_id(sample_experiment_query)
        assert experiment_id is not None

        # Update status
        integration_storage.set_generation_done(experiment_id)

        # Verify update
        experiment_data = integration_storage.get_data(sample_experiment_query)
        assert experiment_data.is_generation_done is True

        # Delete
        integration_storage.delete_data(sample_experiment_query)

        # Verify deletion
        result_after_delete = integration_storage.get_data(sample_experiment_query)
        assert result_after_delete is None


# TODO: big integration tests with CLI in different file
