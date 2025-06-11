import json
import sqlite3
from pathlib import Path
from sqlite3 import Connection

from stattest.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)


class SQLiteRandomValuesStorage(IRandomValuesStorage):
    """
    SQLite implementation of random values storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn: None | Connection = None

    def init(self) -> None:
        """Initialize the database and create tables."""
        db_path = Path(self.connection_string)
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True)
        self.conn = sqlite3.connect(self.connection_string)
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS random_values (
                generator_name TEXT NOT NULL,
                generator_parameters TEXT NOT NULL,
                sample_size INTEGER NOT NULL,
                sample_num INTEGER NOT NULL,
                data TEXT NOT NULL,
                PRIMARY KEY (generator_name, generator_parameters, sample_size, sample_num)
            )
            """)

    def _get_connection(self):
        """Get database connection, ensuring it's initialized."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        return self.conn

    def get_data(self, query: RandomValuesQuery) -> RandomValuesModel | None:
        """Get specific random values data."""
        conn = self._get_connection()
        params_json = json.dumps(query.generator_parameters)

        cursor = conn.execute(
            """
            SELECT data FROM random_values
            WHERE generator_name = ?
            AND generator_parameters = ?
            AND sample_size = ?
            AND sample_num = ?
        """,
            (query.generator_name, params_json, query.sample_size, query.sample_num),
        )

        row = cursor.fetchone()
        if not row:
            return None

        data = json.loads(row[0])
        return RandomValuesModel(
            generator_name=query.generator_name,
            generator_parameters=query.generator_parameters,
            sample_size=query.sample_size,
            sample_num=query.sample_num,
            data=data,
        )

    def insert_data(self, data: RandomValuesModel) -> None:
        """Insert single random values data entry."""
        conn = self._get_connection()
        params_json = json.dumps(data.generator_parameters)
        data_json = json.dumps(data.data)

        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO random_values
                (generator_name, generator_parameters, sample_size, sample_num, data)
                VALUES (?, ?, ?, ?, ?)
            """,
                (data.generator_name, params_json, data.sample_size, data.sample_num, data_json),
            )

    def delete_data(self, query: RandomValuesQuery) -> None:
        """Delete specific random values data."""
        conn = self._get_connection()
        params_json = json.dumps(query.generator_parameters)

        with conn:
            conn.execute(
                """
                DELETE FROM random_values
                WHERE generator_name = ?
                AND generator_parameters = ?
                AND sample_size = ?
                AND sample_num = ?
            """,
                (query.generator_name, params_json, query.sample_size, query.sample_num),
            )

    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """Get count of samples for given parameters."""
        conn = self._get_connection()
        params_json = json.dumps(query.generator_parameters)

        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM random_values
            WHERE generator_name = ?
            AND generator_parameters = ?
            AND sample_size = ?
        """,
            (query.generator_name, params_json, query.sample_size),
        )

        return cursor.fetchone()[0]

    def insert_all_data(self, data: RandomValuesAllModel) -> None:
        """Insert all data for a given configuration."""
        conn = self._get_connection()
        params_json = json.dumps(data.generator_parameters)

        with conn:
            # Delete existing data first
            conn.execute(
                """
                DELETE FROM random_values
                WHERE generator_name = ?
                AND generator_parameters = ?
                AND sample_size = ?
            """,
                (data.generator_name, params_json, data.sample_size),
            )

            # Insert new data
            for i, sample in enumerate(data.data):
                data_json = json.dumps(sample)
                conn.execute(
                    """
                    INSERT INTO random_values
                    (generator_name, generator_parameters, sample_size, sample_num, data)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (data.generator_name, params_json, data.sample_size, i + 1, data_json),
                )

    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel] | None:
        """Get all data for given parameters."""
        conn = self._get_connection()
        params_json = json.dumps(query.generator_parameters)

        cursor = conn.execute(
            """
            SELECT sample_num, data FROM random_values
            WHERE generator_name = ?
            AND generator_parameters = ?
            AND sample_size = ?
            ORDER BY sample_num
        """,
            (query.generator_name, params_json, query.sample_size),
        )

        results = []
        for row in cursor:
            sample_num, data_json = row
            data = json.loads(data_json)
            results.append(
                RandomValuesModel(
                    generator_name=query.generator_name,
                    generator_parameters=query.generator_parameters,
                    sample_size=query.sample_size,
                    sample_num=sample_num,
                    data=data,
                )
            )

        return results

    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """Delete all data for given parameters."""
        conn = self._get_connection()
        params_json = json.dumps(query.generator_parameters)

        with conn:
            conn.execute(
                """
                DELETE FROM random_values
                WHERE generator_name = ?
                AND generator_parameters = ?
                AND sample_size = ?
            """,
                (query.generator_name, params_json, query.sample_size),
            )

    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel] | None:
        """Get limited number of samples for given parameters."""
        conn = self._get_connection()
        params_json = json.dumps(query.generator_parameters)

        cursor = conn.execute(
            """
            SELECT sample_num, data FROM random_values
            WHERE generator_name = ?
            AND generator_parameters = ?
            AND sample_size = ?
            ORDER BY sample_num
            LIMIT ?
        """,
            (query.generator_name, params_json, query.sample_size, query.count),
        )

        results = []
        for row in cursor:
            sample_num, data_json = row
            data = json.loads(data_json)
            results.append(
                RandomValuesModel(
                    generator_name=query.generator_name,
                    generator_parameters=query.generator_parameters,
                    sample_size=query.sample_size,
                    sample_num=sample_num,
                    data=data,
                )
            )

        return results
