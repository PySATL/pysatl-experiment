from unittest.mock import patch

import psycopg2
import pytest

from pysatl_experiment.exceptions import StorageError
from pysatl_experiment.persistence.model.power.power import PowerModel, PowerQuery
from pysatl_experiment.persistence.storage.power.sqlite.sqlite import SQLitePowerStorage


# TODO: clearance


# Temporary SQLite database fixture
@pytest.fixture(scope="function")
def temp_postgres_db():
    test_db_name = "test_power_db"
    original_connection_string = "test.db"

    # Creating test BD
    conn = psycopg2.connect(original_connection_string)
    conn.autocommit = True
    cursor = conn.cursor()

    # Ending all old connections
    cursor.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{test_db_name}'
        AND pid <> pg_backend_pid();
    """)

    cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name};")
    cursor.execute(f"CREATE DATABASE {test_db_name};")
    cursor.close()
    conn.close()

    # Return connection string for test BD
    test_connection_string = f"postgresql://user:password@localhost:5432/{test_db_name}"

    yield test_connection_string

    # Clearing after test
    conn = psycopg2.connect(original_connection_string)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE {test_db_name};")
    cursor.close()
    conn.close()


@pytest.fixture
def storage(temp_postgres_db):
    storage = SQLitePowerStorage(temp_postgres_db, "test_power_analysis")
    storage.init()
    return storage


@pytest.fixture
def sample_power_model():
    return PowerModel(
        experiment_id=1,
        criterion_code="ks_test",
        criterion_parameters=[0.5, 1.0],
        sample_size=100,
        alternative_code="normal_shift",
        alternative_parameters=[0.0, 1.0, 0.5],
        monte_carlo_count=1000,
        significance_level=0.05,
        results_criteria=[True] * 700 + [False] * 300,  # 70% power
    )


@pytest.fixture
def sample_power_query():
    return PowerQuery(
        criterion_code="ks_test",
        criterion_parameters=[0.5, 1.0],
        sample_size=100,
        alternative_code="normal_shift",
        alternative_parameters=[0.0, 1.0, 0.5],
        monte_carlo_count=1000,
        significance_level=0.05,
    )


@pytest.fixture
def multiple_power_models():
    base_params = {
        "criterion_parameters": [0.5, 1.0],
        "alternative_parameters": [0.0, 1.0],
        "monte_carlo_count": 1000,
        "significance_level": 0.05,
        "results_criteria": [True] * 600 + [False] * 400,  # 60% power
    }

    models = []
    for i in range(3):
        model = PowerModel(
            experiment_id=i + 1,
            criterion_code=f"test_{i}",
            sample_size=50 * (i + 1),
            alternative_code=f"alt_{i}",
            **base_params,
        )
        models.append(model)

    return models


class TestSQLitePowerStorage:
    def test_initialization(self, storage):
        assert storage is not None
        assert storage.table_name == "test_power_analysis"
        assert storage._initialized is True

    def test_table_creation(self, storage):
        # Check for database created
        with storage._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """,
                    (storage.table_name,),
                )
                result = cursor.fetchone()
                assert result[0] is True

    def test_insert_and_get_data(self, storage, sample_power_model, sample_power_query):
        # Insert
        storage.insert_data(sample_power_model)

        # Get
        result = storage.get_data(sample_power_query)

        # Check
        assert result is not None
        assert result.experiment_id == sample_power_model.experiment_id
        assert result.criterion_code == sample_power_model.criterion_code
        assert result.criterion_parameters == sample_power_model.criterion_parameters
        assert result.sample_size == sample_power_model.sample_size
        assert result.alternative_code == sample_power_model.alternative_code
        assert result.alternative_parameters == sample_power_model.alternative_parameters
        assert result.monte_carlo_count == sample_power_model.monte_carlo_count
        assert result.significance_level == sample_power_model.significance_level
        assert result.results_criteria == sample_power_model.results_criteria

    def test_insert_and_get_interface_methods(self, storage, sample_power_model, sample_power_query):
        # Insert
        storage.insert(sample_power_model)

        # Get
        result = storage.get(sample_power_query)
        assert result is not None
        assert result.experiment_id == sample_power_model.experiment_id

    def test_get_nonexistent_data(self, storage, sample_power_query):
        result = storage.get_data(sample_power_query)
        assert result is None

    def test_insert_duplicate(self, storage, sample_power_model):
        # First insert
        storage.insert_data(sample_power_model)

        # Insert after modify
        modified_model = PowerModel(
            experiment_id=sample_power_model.experiment_id,
            criterion_code=sample_power_model.criterion_code,
            criterion_parameters=sample_power_model.criterion_parameters,
            sample_size=sample_power_model.sample_size,
            alternative_code=sample_power_model.alternative_code,
            alternative_parameters=sample_power_model.alternative_parameters,
            monte_carlo_count=sample_power_model.monte_carlo_count,
            significance_level=sample_power_model.significance_level,
            results_criteria=[True] * 800 + [False] * 200,  # Updated to 80% power
        )

        storage.insert_data(modified_model)

        # Check if data updated
        query = PowerQuery(
            criterion_code=sample_power_model.criterion_code,
            criterion_parameters=sample_power_model.criterion_parameters,
            sample_size=sample_power_model.sample_size,
            alternative_code=sample_power_model.alternative_code,
            alternative_parameters=sample_power_model.alternative_parameters,
            monte_carlo_count=sample_power_model.monte_carlo_count,
            significance_level=sample_power_model.significance_level,
        )

        result = storage.get_data(query)
        assert result.results_criteria == modified_model.results_criteria

    def test_update_method(self, storage, sample_power_model):
        # Insert
        storage.insert(sample_power_model)

        # Update
        updated_model = PowerModel(
            experiment_id=sample_power_model.experiment_id,
            criterion_code=sample_power_model.criterion_code,
            criterion_parameters=sample_power_model.criterion_parameters,
            sample_size=sample_power_model.sample_size,
            alternative_code=sample_power_model.alternative_code,
            alternative_parameters=sample_power_model.alternative_parameters,
            monte_carlo_count=sample_power_model.monte_carlo_count,
            significance_level=sample_power_model.significance_level,
            results_criteria=[True] * 900 + [False] * 100,  # Updated
        )

        storage.update(updated_model)

        # Check
        query = PowerQuery(
            criterion_code=sample_power_model.criterion_code,
            criterion_parameters=sample_power_model.criterion_parameters,
            sample_size=sample_power_model.sample_size,
            alternative_code=sample_power_model.alternative_code,
            alternative_parameters=sample_power_model.alternative_parameters,
            monte_carlo_count=sample_power_model.monte_carlo_count,
            significance_level=sample_power_model.significance_level,
        )

        result = storage.get_data(query)
        assert result.results_criteria == updated_model.results_criteria

    def test_delete_data(self, storage, sample_power_model, sample_power_query):
        # Insert
        storage.insert_data(sample_power_model)
        assert storage.get_data(sample_power_query) is not None

        # Delete
        storage.delete_data(sample_power_query)
        assert storage.get_data(sample_power_query) is None

    def test_delete_interface_method(self, storage, sample_power_model, sample_power_query):
        storage.insert(sample_power_model)
        assert storage.get(sample_power_query) is not None

        storage.delete(sample_power_query)
        assert storage.get(sample_power_query) is None

    def test_get_by_experiment_id(self, storage, multiple_power_models):
        for model in multiple_power_models:
            storage.insert_data(model)

        results = storage.get_by_experiment_id(1)
        assert len(results) == 1
        assert results[0].experiment_id == 1
        assert results[0].criterion_code == "test_0"

        results = storage.get_by_experiment_id(999)
        assert len(results) == 0

    def test_calculate_power(self, storage, sample_power_model, sample_power_query):
        storage.insert_data(sample_power_model)  # Know  70% power

        power = storage.calculate_power(sample_power_query)

        assert power is not None
        assert abs(power - 0.7) < 0.001

    def test_calculate_power_nonexistent(self, storage, sample_power_query):
        power = storage.calculate_power(sample_power_query)
        assert power is None

    def test_calculate_power_empty_results(self, storage):
        model = PowerModel(
            experiment_id=1,
            criterion_code="empty_test",
            criterion_parameters=[],
            sample_size=100,
            alternative_code="empty_alt",
            alternative_parameters=[],
            monte_carlo_count=1000,
            significance_level=0.05,
            results_criteria=[],
        )

        storage.insert_data(model)

        query = PowerQuery(
            criterion_code="empty_test",
            criterion_parameters=[],
            sample_size=100,
            alternative_code="empty_alt",
            alternative_parameters=[],
            monte_carlo_count=1000,
            significance_level=0.05,
        )

        power = storage.calculate_power(query)
        assert power is None  # TODO: check for actual one

    def test_batch_insert(self, storage, multiple_power_models):
        inserted_count = storage.batch_insert(multiple_power_models)

        assert inserted_count == len(multiple_power_models)

        # Insert
        for model in multiple_power_models:
            query = PowerQuery(
                criterion_code=model.criterion_code,
                criterion_parameters=model.criterion_parameters,
                sample_size=model.sample_size,
                alternative_code=model.alternative_code,
                alternative_parameters=model.alternative_parameters,
                monte_carlo_count=model.monte_carlo_count,
                significance_level=model.significance_level,
            )
            result = storage.get_data(query)
            assert result is not None

    def test_batch_insert_duplicates(self, storage, multiple_power_models):
        storage.batch_insert(multiple_power_models)

        inserted_count = storage.batch_insert(multiple_power_models)
        assert inserted_count == 0

    def test_exists_method(self, storage, sample_power_model, sample_power_query):
        assert storage.exists(sample_power_query) is False

        storage.insert_data(sample_power_model)
        assert storage.exists(sample_power_query) is True

    def test_complex_parameters(self, storage):
        complex_criterion_params = [0.1, 0.2, 0.3, 0.4, 0.5]
        complex_alternative_params = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

        model = PowerModel(
            experiment_id=1,
            criterion_code="complex_test",
            criterion_parameters=complex_criterion_params,
            sample_size=200,
            alternative_code="complex_alt",
            alternative_parameters=complex_alternative_params,
            monte_carlo_count=5000,
            significance_level=0.01,
            results_criteria=[True] * 2500 + [False] * 2500,
        )

        storage.insert_data(model)

        query = PowerQuery(
            criterion_code="complex_test",
            criterion_parameters=complex_criterion_params,
            sample_size=200,
            alternative_code="complex_alt",
            alternative_parameters=complex_alternative_params,
            monte_carlo_count=5000,
            significance_level=0.01,
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.criterion_parameters == complex_criterion_params
        assert result.alternative_parameters == complex_alternative_params


class TestEdgeCases:
    def test_empty_parameters(self, storage):
        model = PowerModel(
            experiment_id=1,
            criterion_code="empty_params",
            criterion_parameters=[],
            sample_size=100,
            alternative_code="empty_alt",
            alternative_parameters=[],
            monte_carlo_count=1000,
            significance_level=0.05,
            results_criteria=[True, False, True],
        )

        storage.insert_data(model)

        query = PowerQuery(
            criterion_code="empty_params",
            criterion_parameters=[],
            sample_size=100,
            alternative_code="empty_alt",
            alternative_parameters=[],
            monte_carlo_count=1000,
            significance_level=0.05,
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.criterion_parameters == []
        assert result.alternative_parameters == []

    def test_single_element_parameters(self, storage):
        model = PowerModel(
            experiment_id=1,
            criterion_code="single_param",
            criterion_parameters=[42.0],
            sample_size=100,
            alternative_code="single_alt",
            alternative_parameters=[3.14],
            monte_carlo_count=1000,
            significance_level=0.05,
            results_criteria=[True] * 1000,
        )

        storage.insert_data(model)

        query = PowerQuery(
            criterion_code="single_param",
            criterion_parameters=[42.0],
            sample_size=100,
            alternative_code="single_alt",
            alternative_parameters=[3.14],
            monte_carlo_count=1000,
            significance_level=0.05,
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.criterion_parameters == [42.0]
        assert result.alternative_parameters == [3.14]

    def test_large_sample_size(self, storage):
        model = PowerModel(
            experiment_id=1,
            criterion_code="large_sample",
            criterion_parameters=[0.5, 1.0],
            sample_size=100000,
            alternative_code="large_alt",
            alternative_parameters=[0.0, 1.0],
            monte_carlo_count=1000,
            significance_level=0.05,
            results_criteria=[True] * 1000,
        )

        storage.insert_data(model)

        query = PowerQuery(
            criterion_code="large_sample",
            criterion_parameters=[0.5, 1.0],
            sample_size=100000,
            alternative_code="large_alt",
            alternative_parameters=[0.0, 1.0],
            monte_carlo_count=1000,
            significance_level=0.05,
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.sample_size == 100000

    def test_special_characters_in_codes(self, storage):
        special_criterion = "criterion-with-dashes_and_underscores"
        special_alternative = "alternative.with.dots"

        model = PowerModel(
            experiment_id=1,
            criterion_code=special_criterion,
            criterion_parameters=[0.5, 1.0],
            sample_size=100,
            alternative_code=special_alternative,
            alternative_parameters=[0.0, 1.0],
            monte_carlo_count=1000,
            significance_level=0.05,
            results_criteria=[True] * 500 + [False] * 500,
        )

        storage.insert_data(model)

        query = PowerQuery(
            criterion_code=special_criterion,
            criterion_parameters=[0.5, 1.0],
            sample_size=100,
            alternative_code=special_alternative,
            alternative_parameters=[0.0, 1.0],
            monte_carlo_count=1000,
            significance_level=0.05,
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.criterion_code == special_criterion
        assert result.alternative_code == special_alternative


class TestErrorHandling:
    @patch("psycopg2.connect")
    def test_connection_error_on_init(self, mock_connect):
        mock_connect.side_effect = StorageError("Connection failed")

        storage = SQLitePowerStorage("invalid_connection_string")
        with pytest.raises(StorageError):
            storage.init()

    def test_invalid_significance_level(self, storage):
        model = PowerModel(
            experiment_id=1,
            criterion_code="invalid_alpha",
            criterion_parameters=[0.5],
            sample_size=100,
            alternative_code="invalid_alt",
            alternative_parameters=[0.0, 1.0],
            monte_carlo_count=1000,
            significance_level=1.5,
            results_criteria=[True] * 1000,
        )

        with pytest.raises(StorageError):
            storage.insert_data(model)

    def test_invalid_sample_size(self, storage):
        model = PowerModel(
            experiment_id=1,
            criterion_code="invalid_size",
            criterion_parameters=[0.5],
            sample_size=0,
            alternative_code="invalid_alt",
            alternative_parameters=[0.0, 1.0],
            monte_carlo_count=1000,
            significance_level=0.05,
            results_criteria=[True] * 1000,
        )

        with pytest.raises(StorageError):
            storage.insert_data(model)


class TestIntegration:
    def test_complete_workflow(self, storage):
        models = []
        for i in range(5):
            model = PowerModel(
                experiment_id=i + 1,
                criterion_code=f"criterion_{i}",
                criterion_parameters=[float(i), float(i + 1)],
                sample_size=50 * (i + 1),
                alternative_code=f"alternative_{i}",
                alternative_parameters=[float(i * 0.1), float(i * 0.2)],
                monte_carlo_count=1000 + i * 100,
                significance_level=0.01 * (i + 1),
                results_criteria=[True] * (600 + i * 100) + [False] * (400 - i * 100),
            )
            models.append(model)

        inserted_count = storage.batch_insert(models)
        assert inserted_count == 5

        for i, model in enumerate(models):
            query = PowerQuery(
                criterion_code=model.criterion_code,
                criterion_parameters=model.criterion_parameters,
                sample_size=model.sample_size,
                alternative_code=model.alternative_code,
                alternative_parameters=model.alternative_parameters,
                monte_carlo_count=model.monte_carlo_count,
                significance_level=model.significance_level,
            )
            assert storage.exists(query) is True

            power = storage.calculate_power(query)
            expected_power = (600 + i * 100) / 1000.0
            assert abs(power - expected_power) < 0.01

        for i, model in enumerate(models):
            query = PowerQuery(
                criterion_code=model.criterion_code,
                criterion_parameters=model.criterion_parameters,
                sample_size=model.sample_size,
                alternative_code=model.alternative_code,
                alternative_parameters=model.alternative_parameters,
                monte_carlo_count=model.monte_carlo_count,
                significance_level=model.significance_level,
            )
            storage.delete_data(query)
            assert storage.exists(query) is False


# TODO: proper description
