import json
import sqlite3
from pathlib import Path
from sqlite3 import Connection

from stattest.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


class SQLiteTimeComplexityStorage(ITimeComplexityStorage):
    """
    SQLite implementation of time complexity storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn: None | Connection = None

    def init(self) -> None:
        """
        Initialize SQLite time complexity storage and create tables.
        """
        db_path = Path(self.connection_string)
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True)
        self.conn = sqlite3.connect(self.connection_string)
        self._create_tables()

    def _create_tables(self):
        """
        Create time complexity table if it doesn't exist.
        """
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS time_complexity (
                    experiment_id INTEGER NOT NULL,
                    criterion_code TEXT NOT NULL,
                    criterion_parameters TEXT NOT NULL,
                    sample_size INTEGER NOT NULL,
                    monte_carlo_count INTEGER NOT NULL,
                    results_times TEXT NOT NULL,
                    PRIMARY KEY (
                        experiment_id,
                        criterion_code,
                        criterion_parameters,
                        sample_size,
                        monte_carlo_count
                    )
                )
            """)

    def _get_connection(self):
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        return self.conn

    def insert_data(self, data: TimeComplexityModel) -> None:
        """
        Insert or replace time complexity data.
        """
        conn = self._get_connection()

        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO time_complexity (
                    experiment_id,
                    criterion_code,
                    criterion_parameters,
                    sample_size,
                    monte_carlo_count,
                    results_times
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    data.experiment_id,
                    data.criterion_code,
                    json.dumps(data.criterion_parameters),
                    data.sample_size,
                    data.monte_carlo_count,
                    json.dumps(data.results_times),
                ),
            )

    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        """
        Get time complexity data matching the query.
        """
        conn = self._get_connection()

        cursor = conn.execute(
            """
            SELECT experiment_id, results_times FROM time_complexity
            WHERE criterion_code = ?
            AND criterion_parameters = ?
            AND sample_size = ?
            AND monte_carlo_count = ?
        """,
            (
                query.criterion_code,
                json.dumps(query.criterion_parameters),
                query.sample_size,
                query.monte_carlo_count,
            ),
        )

        row = cursor.fetchone()
        if not row:
            return None

        experiment_id, results_json = row
        return TimeComplexityModel(
            experiment_id=experiment_id,
            criterion_code=query.criterion_code,
            criterion_parameters=query.criterion_parameters,
            sample_size=query.sample_size,
            monte_carlo_count=query.monte_carlo_count,
            results_times=json.loads(results_json),
        )

    def delete_data(self, query: TimeComplexityQuery) -> None:
        """
        Delete time complexity data matching the query.
        """
        conn = self._get_connection()

        with conn:
            conn.execute(
                """
                DELETE FROM time_complexity
                WHERE criterion_code = ?
                AND criterion_parameters = ?
                AND sample_size = ?
                AND monte_carlo_count = ?
            """,
                (
                    query.criterion_code,
                    json.dumps(query.criterion_parameters),
                    query.sample_size,
                    query.monte_carlo_count,
                ),
            )
