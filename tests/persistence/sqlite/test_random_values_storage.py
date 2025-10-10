import psycopg2
import pytest

from pysatl_experiment.persistence.model.random_values.random_values import (
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)
from pysatl_experiment.persistence.storage.random_values.sqlite.sqlite import SQLiteRandomValuesStorage


# TODO: clearance


@pytest.fixture(scope="function")
def temp_postgres_db():
    test_db_name = "test_random_values_db"
    original_connection_string = "test.db"

    conn = psycopg2.connect(original_connection_string)
    conn.autocommit = True
    cursor = conn.cursor()

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

    test_connection_string = f"postgresql://user:password@localhost:5432/{test_db_name}"

    yield test_connection_string

    try:
        conn = psycopg2.connect(original_connection_string)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE {test_db_name};")
        cursor.close()
        conn.close()
    except Exception:
        pass


@pytest.fixture
def storage(temp_postgres_db):
    return SQLiteRandomValuesStorage(temp_postgres_db, "test_random_values")


@pytest.fixture
def sample_model():
    return RandomValuesModel(
        generator_name="normal",
        generator_parameters=[0.0, 1.0],
        sample_size=100,
        sample_num=1,
        data=[0.1, 0.2, 0.3, 0.4, 0.5],
    )


@pytest.fixture
def sample_query():
    return RandomValuesQuery(generator_name="normal", generator_parameters=[0.0, 1.0], sample_size=100, sample_num=1)


@pytest.fixture
def sample_all_query():
    return RandomValuesAllQuery(generator_name="normal", generator_parameters=[0.0, 1.0], sample_size=100)


@pytest.fixture
def sample_count_query():
    return RandomValuesCountQuery(generator_name="normal", generator_parameters=[0.0, 1.0], sample_size=100, count=2)


class TestSQLiteRandomValuesStorage:
    def test_initialization(self, storage):
        assert storage is not None
        assert storage.table_name == "test_random_values"

    def test_table_creation(self, storage):
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

    def test_insert_and_get(self, storage, sample_model, sample_query):
        storage.insert(sample_model)

        result = storage.get_data(sample_query)

        assert result is not None
        assert result.generator_name == sample_model.generator_name
        assert result.generator_parameters == sample_model.generator_parameters
        assert result.sample_size == sample_model.sample_size
        assert result.sample_num == sample_model.sample_num
        assert result.data == sample_model.data

    def test_get_nonexistent(self, storage, sample_query):
        result = storage.get_data(sample_query)
        assert result is None

    def test_insert_duplicate(self, storage, sample_model):
        storage.insert(sample_model)

        modified_model = RandomValuesModel(
            generator_name=sample_model.generator_name,
            generator_parameters=sample_model.generator_parameters,
            sample_size=sample_model.sample_size,
            sample_num=sample_model.sample_num,
            data=[1.0, 2.0, 3.0],
        )

        storage.insert(modified_model)

        query = RandomValuesQuery(
            generator_name=sample_model.generator_name,
            generator_parameters=sample_model.generator_parameters,
            sample_size=sample_model.sample_size,
            sample_num=sample_model.sample_num,
        )

        result = storage.get_data(query)
        assert result.data == modified_model.data

    def test_update(self, storage, sample_model):
        storage.insert(sample_model)

        updated_model = RandomValuesModel(
            generator_name=sample_model.generator_name,
            generator_parameters=sample_model.generator_parameters,
            sample_size=sample_model.sample_size,
            sample_num=sample_model.sample_num,
            data=[9.0, 8.0, 7.0],
        )

        storage.update(updated_model)

        query = RandomValuesQuery(
            generator_name=sample_model.generator_name,
            generator_parameters=sample_model.generator_parameters,
            sample_size=sample_model.sample_size,
            sample_num=sample_model.sample_num,
        )

        result = storage.get_data(query)
        assert result.data == updated_model.data

    def test_delete(self, storage, sample_model, sample_query):
        storage.insert(sample_model)
        assert storage.get_data(sample_query) is not None

        storage.delete(sample_query)
        assert storage.get_data(sample_query) is None

    def test_get_rvs_count(self, storage, sample_all_query):
        count = storage.get_rvs_count(sample_all_query)
        assert count == 0

        for i in range(3):
            model = RandomValuesModel(
                generator_name="normal",
                generator_parameters=[0.0, 1.0],
                sample_size=100,
                sample_num=i + 1,
                data=[float(i)] * 5,
            )
            storage.insert(model)

        count = storage.get_rvs_count(sample_all_query)
        assert count == 3

    def test_insert_all_data(self, storage, sample_all_query):
        all_data_model = RandomValuesAllModel(
            generator_name="normal",
            generator_parameters=[0.0, 1.0],
            sample_size=100,
            data=[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
        )

        storage.insert_all_data(all_data_model)

        results = storage.get_all_data(sample_all_query)
        assert results is not None
        assert len(results) == 3

        for i, result in enumerate(results, 1):
            assert result.sample_num == i
            assert result.data == all_data_model.data[i - 1]

    def test_get_all_data(self, storage, sample_all_query):
        for i in range(3):
            model = RandomValuesModel(
                generator_name="normal",
                generator_parameters=[0.0, 1.0],
                sample_size=100,
                sample_num=i + 1,
                data=[float(i + j) for j in range(3)],
            )
            storage.insert(model)

        results = storage.get_all_data(sample_all_query)

        assert results is not None
        assert len(results) == 3

        sample_nums = [r.sample_num for r in results]
        assert sample_nums == [1, 2, 3]

    def test_get_all_data_empty(self, storage, sample_all_query):
        results = storage.get_all_data(sample_all_query)
        assert results is None

    def test_delete_all_data(self, storage, sample_all_query):
        for i in range(3):
            model = RandomValuesModel(
                generator_name="normal",
                generator_parameters=[0.0, 1.0],
                sample_size=100,
                sample_num=i + 1,
                data=[float(i)] * 5,
            )
            storage.insert(model)

        assert storage.get_rvs_count(sample_all_query) == 3

        storage.delete_all_data(sample_all_query)

        assert storage.get_rvs_count(sample_all_query) == 0
        assert storage.get_all_data(sample_all_query) is None

    def test_get_count_data(self, storage, sample_count_query):
        for i in range(5):
            model = RandomValuesModel(
                generator_name="normal",
                generator_parameters=[0.0, 1.0],
                sample_size=100,
                sample_num=i + 1,
                data=[float(i)] * 3,
            )
            storage.insert(model)

        results = storage.get_count_data(sample_count_query)

        assert results is not None
        assert len(results) == 2

        assert results[0].sample_num == 1
        assert results[1].sample_num == 2

    def test_get_count_data_more_than_exists(self, storage, sample_count_query):
        model = RandomValuesModel(
            generator_name="normal",
            generator_parameters=[0.0, 1.0],
            sample_size=100,
            sample_num=1,
            data=[1.0, 2.0, 3.0],
        )
        storage.insert(model)

        sample_count_query.count = 2
        results = storage.get_count_data(sample_count_query)

        assert results is not None
        assert len(results) == 1

    def test_different_generators(self, storage):
        model1 = RandomValuesModel(
            generator_name="normal",
            generator_parameters=[0.0, 1.0],
            sample_size=100,
            sample_num=1,
            data=[1.0, 2.0, 3.0],
        )

        model2 = RandomValuesModel(
            generator_name="uniform",
            generator_parameters=[0.0, 10.0],
            sample_size=100,
            sample_num=1,
            data=[5.0, 6.0, 7.0],
        )

        storage.insert(model1)
        storage.insert(model2)

        query1 = RandomValuesAllQuery(generator_name="normal", generator_parameters=[0.0, 1.0], sample_size=100)

        query2 = RandomValuesAllQuery(generator_name="uniform", generator_parameters=[0.0, 10.0], sample_size=100)

        results1 = storage.get_all_data(query1)
        results2 = storage.get_all_data(query2)

        assert results1 is not None
        assert results2 is not None
        assert len(results1) == 1
        assert len(results2) == 1
        assert results1[0].generator_name == "normal"
        assert results2[0].generator_name == "uniform"

    def test_complex_parameters(self, storage):
        complex_parameters = [0.0, 1.0, 2.0, 3.14159]

        model = RandomValuesModel(
            generator_name="complex",
            generator_parameters=complex_parameters,
            sample_size=100,
            sample_num=1,
            data=list(range(10)),
        )

        storage.insert(model)

        query = RandomValuesQuery(
            generator_name="complex", generator_parameters=complex_parameters, sample_size=100, sample_num=1
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.generator_parameters == complex_parameters

    def test_large_data(self, storage):
        large_data = list(range(10000))

        model = RandomValuesModel(
            generator_name="large", generator_parameters=[0.0, 1.0], sample_size=10000, sample_num=1, data=large_data
        )

        storage.insert(model)

        query = RandomValuesQuery(
            generator_name="large", generator_parameters=[0.0, 1.0], sample_size=10000, sample_num=1
        )

        result = storage.get_data(query)
        assert result is not None
        assert len(result.data) == 10000
        assert result.data == large_data


class TestEdgeCases:
    def test_empty_parameters(self, storage):
        model = RandomValuesModel(
            generator_name="empty_params", generator_parameters=[], sample_size=100, sample_num=1, data=[1.0, 2.0, 3.0]
        )

        storage.insert(model)

        query = RandomValuesQuery(generator_name="empty_params", generator_parameters=[], sample_size=100, sample_num=1)

        result = storage.get_data(query)
        assert result is not None
        assert result.generator_parameters == []

    def test_empty_data(self, storage):
        model = RandomValuesModel(
            generator_name="empty_data", generator_parameters=[1.0, 2.0], sample_size=100, sample_num=1, data=[]
        )

        storage.insert(model)

        query = RandomValuesQuery(
            generator_name="empty_data", generator_parameters=[1.0, 2.0], sample_size=100, sample_num=1
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.data == []

    def test_special_characters_in_name(self, storage):
        special_name = "generator-with-dashes_and_underscores"

        model = RandomValuesModel(
            generator_name=special_name,
            generator_parameters=[0.0, 1.0],
            sample_size=100,
            sample_num=1,
            data=[1.0, 2.0, 3.0],
        )

        storage.insert(model)

        query = RandomValuesQuery(
            generator_name=special_name, generator_parameters=[0.0, 1.0], sample_size=100, sample_num=1
        )

        result = storage.get_data(query)
        assert result is not None
        assert result.generator_name == special_name


class TestIntegration:
    def test_complete_workflow(self, storage):
        models = []
        for i in range(5):
            model = RandomValuesModel(
                generator_name="workflow_test",
                generator_parameters=[i * 1.0, i * 2.0],
                sample_size=100,
                sample_num=i + 1,
                data=[float(i + j) for j in range(10)],
            )
            models.append(model)
            storage.insert(model)

        all_query = RandomValuesAllQuery(
            generator_name="workflow_test",
            generator_parameters=[0.0, 0.0],
            sample_size=100,
        )

        count = storage.get_rvs_count(all_query)
        assert count == 1

        for i, model in enumerate(models):
            query = RandomValuesAllQuery(
                generator_name="workflow_test", generator_parameters=[i * 1.0, i * 2.0], sample_size=100
            )

            results = storage.get_all_data(query)
            assert results is not None
            assert len(results) == 1
            assert results[0].data == model.data

        for i, model in enumerate(models):
            delete_query = RandomValuesQuery(
                generator_name="workflow_test",
                generator_parameters=[i * 1.0, i * 2.0],
                sample_size=100,
                sample_num=i + 1,
            )
            storage.delete(delete_query)

            result = storage.get_data(delete_query)
            assert result is None


# TODO: comments!
# TODO: think about connection error
