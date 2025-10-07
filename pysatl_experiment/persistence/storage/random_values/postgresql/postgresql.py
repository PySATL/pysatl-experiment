import json

import psycopg2
from psycopg2.extras import RealDictCursor

from pysatl_experiment.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)


class PostgreSQLRandomValuesStorage(IRandomValuesStorage):
    """
    PostgreSQL implementation of random values storage.
    """

    def __init__(self, connection_string: str, table_name: str = "random_values"):
        self.connection_string = connection_string
        self.table_name = table_name
        self._init_database()

    def _get_connection(self):
        """Get database connection, ensuring it's initialized."""
        return psycopg2.connect(self.connection_string)

    # TODO created at??
    def _init_database(self):
        """Initialize database table if it doesn't exist."""
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            generator_name VARCHAR(255) NOT NULL,
            generator_parameters JSONB NOT NULL,
            sample_size INTEGER NOT NULL,
            sample_num INTEGER NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (generator_name, generator_parameters, sample_size, sample_num)
        );

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_generator
        ON {self.table_name} (generator_name, generator_parameters, sample_size);
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_table_query)
                conn.commit()

    def insert(self, model: RandomValuesModel) -> None:
        """Insert a single RandomValuesModel."""
        insert_query = f"""
        INSERT INTO {self.table_name}
        (generator_name, generator_parameters, sample_size, sample_num, data)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (generator_name, generator_parameters, sample_size, sample_num)
        DO UPDATE SET data = EXCLUDED.data;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_query,
                    (
                        model.generator_name,
                        json.dumps(model.generator_parameters),
                        model.sample_size,
                        model.sample_num,
                        json.dumps(model.data),
                    ),
                )
                conn.commit()

    def get_data(self, query: RandomValuesQuery) -> RandomValuesModel | None:
        """Get a single RandomValuesModel by query."""
        select_query = f"""
        SELECT data FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s
          AND sample_num = %s;
        """

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    select_query,
                    (query.generator_name, json.dumps(query.generator_parameters), query.sample_size, query.sample_num),
                )
                result = cursor.fetchone()

                if result:
                    return RandomValuesModel(
                        generator_name=result["generator_name"],
                        generator_parameters=json.loads(result["generator_parameters"]),
                        sample_size=result["sample_size"],
                        sample_num=result["sample_num"],
                        data=json.loads(result["data"]),
                    )
                return None

    def update(self, model: RandomValuesModel) -> None:
        """Update a RandomValuesModel."""
        # Используем insert с ON CONFLICT для upsert операции
        self.insert(model)

    def delete(self, query: RandomValuesQuery) -> None:
        """Delete a RandomValuesModel by query."""
        delete_query = f"""
        DELETE FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s
          AND sample_num = %s;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    delete_query,
                    (query.generator_name, json.dumps(query.generator_parameters), query.sample_size, query.sample_num),
                )
                conn.commit()

    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """Get count of samples."""
        count_query = f"""
        SELECT COUNT(*) as count
        FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    count_query, (query.generator_name, json.dumps(query.generator_parameters), query.sample_size)
                )
                result = cursor.fetchone()
                return result[0] if result else 0

    def insert_all_data(self, model: RandomValuesAllModel) -> None:
        """Insert all data based on hypothesis and sample size."""
        # Delete old TODO??
        delete_query = f"""
        DELETE FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s;
        """

        insert_query = f"""
        INSERT INTO {self.table_name}
        (generator_name, generator_parameters, sample_size, sample_num, data)
        VALUES (%s, %s, %s, %s, %s);
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Delete
                cursor.execute(
                    delete_query, (model.generator_name, json.dumps(model.generator_parameters), model.sample_size)
                )

                # Insert
                for sample_num, data in enumerate(model.data, 1):
                    cursor.execute(
                        insert_query,
                        (
                            model.generator_name,
                            json.dumps(model.generator_parameters),
                            model.sample_size,
                            sample_num,
                            json.dumps(data),
                        ),
                    )

                conn.commit()

    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel] | None:
        """Get all data based on hypothesis and sample size."""
        select_query = f"""
        SELECT generator_name, generator_parameters, sample_size, sample_num, data
        FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s
        ORDER BY sample_num;
        """

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    select_query, (query.generator_name, json.dumps(query.generator_parameters), query.sample_size)
                )
                results = cursor.fetchall()

                if results:
                    return [
                        RandomValuesModel(
                            generator_name=row["generator_name"],
                            generator_parameters=json.loads(row["generator_parameters"]),
                            sample_size=row["sample_size"],
                            sample_num=row["sample_num"],
                            data=json.loads(row["data"]),
                        )
                        for row in results
                    ]
                return None

    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """Delete all data based on hypothesis and sample size."""
        delete_query = f"""
        DELETE FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    delete_query, (query.generator_name, json.dumps(query.generator_parameters), query.sample_size)
                )
                conn.commit()

    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel] | None:
        """Get count data based on hypothesis and sample size."""
        select_query = f"""
        SELECT generator_name, generator_parameters, sample_size, sample_num, data
        FROM {self.table_name}
        WHERE generator_name = %s
          AND generator_parameters = %s
          AND sample_size = %s
        ORDER BY sample_num
        LIMIT %s;
        """

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    select_query,
                    (query.generator_name, json.dumps(query.generator_parameters), query.sample_size, query.count),
                )
                results = cursor.fetchall()

                if results:
                    return [
                        RandomValuesModel(
                            generator_name=row["generator_name"],
                            generator_parameters=json.loads(row["generator_parameters"]),
                            sample_size=row["sample_size"],
                            sample_num=row["sample_num"],
                            data=json.loads(row["data"]),
                        )
                        for row in results
                    ]
                return None
