import json
import os
from unittest.mock import Mock, patch

import pytest

from pysatl_experiment.persistence.model.time_complexity.time_complexity import TimeComplexityModel, TimeComplexityQuery
from pysatl_experiment.persistence.storage.time_complexity.sqlite.sqlite import SQLiteTimeComplexityStorage


# TODO: clearance


class TestSQLiteTimeComplexityStorage:
    """Test cases for SQLite time complexity storage"""

    @pytest.fixture
    def mock_connection(self):
        """Mock SQLite connection"""
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.closed = False
            yield mock_connect, mock_conn, mock_cursor

    @pytest.fixture
    def storage(self):
        """Create storage instance for testing"""
        return SQLiteTimeComplexityStorage(connection_string="test.db")

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return TimeComplexityModel(
            experiment_id=1,
            criterion_code="ks_test",
            criterion_parameters=[0.05, 0.1],
            sample_size=100,
            monte_carlo_count=1000,
            results_times=[1.2, 1.3, 1.1, 1.4],
        )

    @pytest.fixture
    def sample_query(self):
        """Sample query for testing"""
        return TimeComplexityQuery(
            criterion_code="ks_test", criterion_parameters=[0.05, 0.1], sample_size=100, monte_carlo_count=1000
        )

    def test_init(self, storage, mock_connection):
        """Test storage initialization"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        storage.init()

        # Verify connection was created
        mock_connect.assert_called_once_with("postgresql://test:test@localhost/test_db")
        # Verify table creation query was executed
        assert mock_cursor.execute.call_count == 1
        mock_conn.commit.assert_called_once()

    def test_init_with_custom_table_name(self, mock_connection):
        """Test storage initialization with custom table name"""
        storage = SQLiteTimeComplexityStorage(
            connection_string="postgresql://test:test@localhost/test_db", table_name="custom_table"
        )
        mock_connect, mock_conn, mock_cursor = mock_connection

        storage.init()

        # Verify table name is used in queries
        call_args = mock_cursor.execute.call_args[0][0]
        assert "custom_table" in call_args
        assert "CREATE TABLE IF NOT EXISTS custom_table" in call_args

    def test_init_rollback_on_error(self, mock_connection):
        """Test rollback on initialization error"""
        mock_connect, mock_conn, mock_cursor = mock_connection
        mock_cursor.execute.side_effect = Exception("Database error")
        storage = SQLiteTimeComplexityStorage("test_connection_string")

        with pytest.raises(Exception, match="Failed to initialize time complexity storage:"):
            storage.init()

        mock_conn.rollback.assert_called_once()

    def test_insert_data(self, storage, mock_connection, sample_data):
        """Test inserting data"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        storage.insert_data(sample_data)

        # Verify insert query was executed with correct parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]

        assert "INSERT INTO time_complexity" in call_args[0]
        assert call_args[1] == (
            sample_data.experiment_id,
            sample_data.criterion_code,
            json.dumps(sample_data.criterion_parameters),
            sample_data.sample_size,
            sample_data.monte_carlo_count,
            json.dumps(sample_data.results_times),
        )
        mock_conn.commit.assert_called_once()

    def test_insert_data_rollback_on_error(self, storage, mock_connection, sample_data):
        """Test rollback on insert error"""
        mock_connect, mock_conn, mock_cursor = mock_connection
        mock_cursor.execute.side_effect = Exception("Insert error")

        with pytest.raises(Exception, match="Failed to insert time complexity data:"):
            storage.insert_data(sample_data)

        mock_conn.rollback.assert_called_once()

    def test_get_data_found(self, storage, mock_connection, sample_query):
        """Test getting existing data"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        # Mock database result
        mock_result = {
            "experiment_id": 1,
            "criterion_code": "ks_test",
            "criterion_parameters": json.dumps([0.05, 0.1]),
            "sample_size": 100,
            "monte_carlo_count": 1000,
            "results_times": json.dumps([1.2, 1.3, 1.1, 1.4]),
        }
        mock_cursor.fetchone.return_value = mock_result

        result = storage.get_data(sample_query)

        # Verify query was executed with correct parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]

        assert "SELECT" in call_args[0]
        assert call_args[1] == (
            sample_query.criterion_code,
            json.dumps(sample_query.criterion_parameters),
            sample_query.sample_size,
            sample_query.monte_carlo_count,
        )

        # Verify result conversion
        assert result is not None
        assert result.experiment_id == 1
        assert result.criterion_code == "ks_test"
        assert result.criterion_parameters == [0.05, 0.1]
        assert result.sample_size == 100
        assert result.monte_carlo_count == 1000
        assert result.results_times == [1.2, 1.3, 1.1, 1.4]

    def test_get_data_not_found(self, storage, mock_connection, sample_query):
        """Test getting non-existent data"""
        mock_connect, mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None

        result = storage.get_data(sample_query)

        assert result is None
        mock_cursor.execute.assert_called_once()

    def test_get_data_error(self, storage, mock_connection, sample_query):
        """Test error during data retrieval"""
        mock_connect, mock_conn, mock_cursor = mock_connection
        mock_cursor.execute.side_effect = Exception("Query error")

        with pytest.raises(Exception, match="Failed to get time complexity data:"):
            storage.get_data(sample_query)

    def test_delete_data(self, storage, mock_connection, sample_query):
        """Test deleting data"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        storage.delete_data(sample_query)

        # Verify delete query was executed with correct parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]

        assert "DELETE FROM time_complexity" in call_args[0]
        assert call_args[1] == (
            sample_query.criterion_code,
            json.dumps(sample_query.criterion_parameters),
            sample_query.sample_size,
            sample_query.monte_carlo_count,
        )
        mock_conn.commit.assert_called_once()

    def test_delete_data_rollback_on_error(self, storage, mock_connection, sample_query):
        """Test rollback on delete error"""
        mock_connect, mock_conn, mock_cursor = mock_connection
        mock_cursor.execute.side_effect = Exception("Delete error")

        with pytest.raises(Exception, match="Failed to delete time complexity data:"):
            storage.delete_data(sample_query)

        mock_conn.rollback.assert_called_once()

    def test_close_connection(self, storage, mock_connection):
        """Test closing database connection"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        # First, establish a connection
        storage.init()
        storage.close()

        mock_conn.close.assert_called_once()

    def test_context_manager(self, mock_connection):
        """Test using storage as context manager"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        with SQLiteTimeComplexityStorage("test_connection_string") as storage:
            storage.init()

        mock_conn.close.assert_called_once()

    def test_connection_reuse(self, storage, mock_connection):
        """Test that connection is reused when not closed"""
        mock_connect, mock_conn, mock_cursor = mock_connection

        # First call
        storage.init()
        first_connection = storage._get_connection()

        # Second call should return same connection
        second_connection = storage._get_connection()

        assert first_connection is second_connection
        mock_connect.assert_called_once()

    def test_json_serialization(self, storage, sample_data):
        """Test JSON serialization of complex parameters"""
        # Test with various data types in parameters
        complex_data = TimeComplexityModel(
            experiment_id=2,
            criterion_code="complex_test",
            criterion_parameters=[0.05, 1.5e-10, -3.14],  # Various float formats
            sample_size=50,
            monte_carlo_count=500,
            results_times=[0.001, 0.002, 0.0015],  # Very small times
        )

        # This should not raise serialization errors
        json_params = json.dumps(complex_data.criterion_parameters)
        json_times = json.dumps(complex_data.results_times)

        # Verify round-trip serialization
        assert complex_data.criterion_parameters == json.loads(json_params)
        assert complex_data.results_times == json.loads(json_times)


# Integration tests (require actual SQLite database)
@pytest.mark.integration
class TestSQLiteTimeComplexityStorageIntegration:
    """Integration tests with real SQLite database"""

    @pytest.fixture
    def integration_storage(self):
        """Create storage instance for integration testing"""
        # Use environment variable for connection string
        connection_string = os.getenv("TEST_POSTGRESQL_CONNECTION_STRING", "postgresql://test:test@localhost/test_db")

        storage = SQLiteTimeComplexityStorage(connection_string=connection_string, table_name="test_time_complexity")

        # Clean up before test
        storage.init()
        with storage._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DELETE FROM {storage.table_name}")
            conn.commit()
        yield storage

        # Clean up after test
        with storage._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {storage.table_name}")
            conn.commit()
        storage.close()

    def test_integration_crud_operations(self, integration_storage):
        """Test full CRUD operations with real database"""
        # Create test data
        test_data = TimeComplexityModel(
            experiment_id=999,
            criterion_code="integration_test",
            criterion_parameters=[0.01, 0.02],
            sample_size=200,
            monte_carlo_count=2000,
            results_times=[2.1, 2.2, 2.3],
        )

        test_query = TimeComplexityQuery(
            criterion_code="integration_test",
            criterion_parameters=[0.01, 0.02],
            sample_size=200,
            monte_carlo_count=2000,
        )

        # Test insert
        integration_storage.insert_data(test_data)

        # Test get (should find the data)
        result = integration_storage.get_data(test_query)
        assert result is not None
        assert result.experiment_id == test_data.experiment_id
        assert result.criterion_code == test_data.criterion_code
        assert result.criterion_parameters == test_data.criterion_parameters
        assert result.sample_size == test_data.sample_size
        assert result.monte_carlo_count == test_data.monte_carlo_count
        assert result.results_times == test_data.results_times

        # Test delete
        integration_storage.delete_data(test_query)

        # Test get after delete (should not find the data)
        result = integration_storage.get_data(test_query)
        assert result is None

    def test_integration_unique_constraint(self, integration_storage):
        """Test unique constraint enforcement"""
        data1 = TimeComplexityModel(
            experiment_id=1,
            criterion_code="unique_test",
            criterion_parameters=[1.0],
            sample_size=100,
            monte_carlo_count=1000,
            results_times=[1.0],
        )

        # Same unique key, different results
        data2 = TimeComplexityModel(
            experiment_id=1,
            criterion_code="unique_test",
            criterion_parameters=[1.0],
            sample_size=100,
            monte_carlo_count=1000,
            results_times=[2.0],  # Different results
        )

        # Insert first record
        integration_storage.insert_data(data1)

        # Insert second record with same unique key - should update existing
        integration_storage.insert_data(data2)

        # Should get the updated record
        query = TimeComplexityQuery(
            criterion_code="unique_test", criterion_parameters=[1.0], sample_size=100, monte_carlo_count=1000
        )

        result = integration_storage.get_data(query)
        assert result is not None
        assert result.results_times == [2.0]  # Should have updated results
