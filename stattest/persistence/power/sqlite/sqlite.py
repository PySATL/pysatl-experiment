import json
import sqlite3
from pathlib import Path
from sqlite3 import Connection

from stattest.persistence.model.power.power import IPowerStorage, PowerModel, PowerQuery


class SQLitePowerStorage(IPowerStorage):
    """
    SQLite implementation of power storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn: None | Connection = None

    def init(self) -> None:
        """
        Initialize SQLite power storage and create tables.
        """
        db_path = Path(self.connection_string)
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True)
        self.conn = sqlite3.connect(self.connection_string)
        self._create_tables()

    def _create_tables(self) -> None:
        """
        Create the power table if it doesn't exist.
        """
        if self.conn is not None:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS power (
                        experiment_id INTEGER NOT NULL,
                        criterion_code TEXT NOT NULL,
                        criterion_parameters TEXT NOT NULL,
                        sample_size INTEGER NOT NULL,
                        alternative_code TEXT NOT NULL,
                        alternative_parameters TEXT NOT NULL,
                        monte_carlo_count INTEGER NOT NULL,
                        significance_level REAL NOT NULL,
                        results_criteria TEXT NOT NULL,
                        PRIMARY KEY (
                            experiment_id,
                            criterion_code,
                            criterion_parameters,
                            sample_size,
                            alternative_code,
                            alternative_parameters,
                            monte_carlo_count,
                            significance_level
                        )
                    )
                """)

    def _get_connection(self):
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        return self.conn

    def insert_data(self, data: PowerModel) -> None:
        """
        Insert or replace a power entry.
        """
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO power (
                    experiment_id,
                    criterion_code,
                    criterion_parameters,
                    sample_size,
                    alternative_code,
                    alternative_parameters,
                    monte_carlo_count,
                    significance_level,
                    results_criteria
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.experiment_id,
                    data.criterion_code,
                    json.dumps(data.criterion_parameters),
                    data.sample_size,
                    data.alternative_code,
                    json.dumps(data.alternative_parameters),
                    data.monte_carlo_count,
                    data.significance_level,
                    json.dumps(data.results_criteria),
                ),
            )

    def get_data(self, query: PowerQuery) -> PowerModel | None:
        """
        Retrieve power data matching the query.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT experiment_id, results_criteria FROM power
            WHERE criterion_code = ?
            AND criterion_parameters = ?
            AND sample_size = ?
            AND alternative_code = ?
            AND alternative_parameters = ?
            AND monte_carlo_count = ?
            AND significance_level = ?
        """,
            (
                query.criterion_code,
                json.dumps(query.criterion_parameters),
                query.sample_size,
                query.alternative_code,
                json.dumps(query.alternative_parameters),
                query.monte_carlo_count,
                query.significance_level,
            ),
        )

        row = cursor.fetchone()
        if not row:
            return None

        experiment_id, results_json = row
        return PowerModel(
            experiment_id=experiment_id,
            criterion_code=query.criterion_code,
            criterion_parameters=query.criterion_parameters,
            sample_size=query.sample_size,
            alternative_code=query.alternative_code,
            alternative_parameters=query.alternative_parameters,
            monte_carlo_count=query.monte_carlo_count,
            significance_level=query.significance_level,
            results_criteria=json.loads(results_json),
        )

    def delete_data(self, query: PowerQuery) -> None:
        """
        Delete power data matching the query.
        """
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                DELETE FROM power
                WHERE criterion_code = ?
                AND criterion_parameters = ?
                AND sample_size = ?
                AND alternative_code = ?
                AND alternative_parameters = ?
                AND monte_carlo_count = ?
                AND significance_level = ?
            """,
                (
                    query.criterion_code,
                    json.dumps(query.criterion_parameters),
                    query.sample_size,
                    query.alternative_code,
                    json.dumps(query.alternative_parameters),
                    query.monte_carlo_count,
                    query.significance_level,
                ),
            )
