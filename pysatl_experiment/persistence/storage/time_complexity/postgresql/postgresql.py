import json

import psycopg2
from psycopg2.extras import RealDictCursor

from pysatl_experiment.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


class PostgreSQLTimeComplexityStorage(ITimeComplexityStorage):
    """
    PostgreSQL implementation of time complexity storage.
    """

    def __init__(self, connection_string: str, table_name: str = "time_complexity"):
        """
        Initialize PostgreSQL storage.

        Args:
            connection_string: PostgreSQL connection string
            table_name: Name of the table to store time complexity data
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self._connection = None

    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(self.connection_string)
        return self._connection

    def init(self) -> None:
        """
        Initialize PostgreSQL time complexity storage and create tables.
        """
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            experiment_id INTEGER NOT NULL,
            criterion_code VARCHAR(255) NOT NULL,
            criterion_parameters JSONB NOT NULL,
            sample_size INTEGER NOT NULL,
            monte_carlo_count INTEGER NOT NULL,
            results_times JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(experiment_id, criterion_code, sample_size, monte_carlo_count)
        );

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_experiment_id ON {self.table_name}(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_criterion_code ON {self.table_name}(criterion_code);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_sample_size ON {self.table_name}(sample_size);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_monte_carlo_count ON {self.table_name}(monte_carlo_count);
        """

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(create_table_query)
            conn.commit()
        except Exception as e:
            raise Exception(f"Failed to initialize time complexity storage: {e}")

    def insert_data(self, data: TimeComplexityModel) -> None:
        """
        Insert or replace time complexity data.
        """
        insert_query = f"""
        INSERT INTO {self.table_name}
            (experiment_id, criterion_code, criterion_parameters, sample_size, monte_carlo_count, results_times)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (experiment_id, criterion_code, sample_size, monte_carlo_count)
        DO UPDATE SET
            criterion_parameters = EXCLUDED.criterion_parameters,
            results_times = EXCLUDED.results_times,
            created_at = CURRENT_TIMESTAMP
        """

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_query,
                    (
                        data.experiment_id,
                        data.criterion_code,
                        json.dumps(data.criterion_parameters),
                        data.sample_size,
                        data.monte_carlo_count,
                        json.dumps(data.results_times),
                    ),
                )
            conn.commit()
        except Exception as e:
            raise Exception(f"Failed to insert time complexity data: {e}")

    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        """
        Get time complexity data matching the query.
        """
        select_query = f"""
        SELECT experiment_id, criterion_code, criterion_parameters, sample_size,
               monte_carlo_count, results_times
        FROM {self.table_name}
        WHERE criterion_code = %s
          AND criterion_parameters = %s
          AND sample_size = %s
          AND monte_carlo_count = %s
        ORDER BY created_at DESC
        LIMIT 1
        """

        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    select_query,
                    (
                        query.criterion_code,
                        json.dumps(query.criterion_parameters),
                        query.sample_size,
                        query.monte_carlo_count,
                    ),
                )

                result = cursor.fetchone()

                if result:
                    return TimeComplexityModel(
                        experiment_id=result["experiment_id"],
                        criterion_code=result["criterion_code"],
                        criterion_parameters=json.loads(result["criterion_parameters"]),
                        sample_size=result["sample_size"],
                        monte_carlo_count=result["monte_carlo_count"],
                        results_times=json.loads(result["results_times"]),
                    )
                return None

        except Exception as e:
            raise Exception(f"Failed to get time complexity data: {e}")

    def delete_data(self, query: TimeComplexityQuery) -> None:
        """
        Delete time complexity data matching the query.
        """
        delete_query = f"""
        DELETE FROM {self.table_name}
        WHERE criterion_code = %s
          AND criterion_parameters = %s
          AND sample_size = %s
          AND monte_carlo_count = %s
        """

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    delete_query,
                    (
                        query.criterion_code,
                        json.dumps(query.criterion_parameters),
                        query.sample_size,
                        query.monte_carlo_count,
                    ),
                )
            conn.commit()
        except Exception as e:
            raise Exception(f"Failed to delete time complexity data: {e}")

    def close(self) -> None:
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# TODO: logger!
# TODO: indexes not needed?
