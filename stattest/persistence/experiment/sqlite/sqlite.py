import json
import sqlite3
from pathlib import Path
from sqlite3 import Connection

from stattest.persistence.model.experiment.experiment import (
    ExperimentModel,
    ExperimentQuery,
    IExperimentStorage,
)


class SQLiteExperimentStorage(IExperimentStorage):
    """
    SQLite implementation for experiment configuration storage.
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
        """Create experiments table if it doesn't exist."""
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_type TEXT NOT NULL,
                storage_connection TEXT NOT NULL,
                run_mode TEXT NOT NULL,
                hypothesis TEXT NOT NULL,
                generator_type TEXT NOT NULL,
                executor_type TEXT NOT NULL,
                report_builder_type TEXT NOT NULL,
                sample_sizes TEXT NOT NULL,
                monte_carlo_count INTEGER NOT NULL,
                criteria TEXT NOT NULL,
                alternatives TEXT NOT NULL,
                significance_levels TEXT NOT NULL,
                is_generation_done INTEGER NOT NULL DEFAULT 0,
                is_execution_done INTEGER NOT NULL DEFAULT 0,
                is_report_building_done INTEGER NOT NULL DEFAULT 0,
                UNIQUE(
                    experiment_type, storage_connection, run_mode, hypothesis,
                    generator_type, executor_type, report_builder_type,
                    sample_sizes, monte_carlo_count, criteria,
                    alternatives, significance_levels
                )
            )
            """)

    def _get_connection(self):
        """Get database connection, ensuring it's initialized."""
        if self.conn is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        return self.conn

    def _model_to_row(self, model: ExperimentModel) -> dict:
        """Convert ExperimentModel to database row format."""
        return {
            "experiment_type": model.experiment_type,
            "storage_connection": model.storage_connection,
            "run_mode": model.run_mode,
            "hypothesis": model.hypothesis,
            "generator_type": model.generator_type,
            "executor_type": model.executor_type,
            "report_builder_type": model.report_builder_type,
            "sample_sizes": json.dumps(model.sample_sizes),
            "monte_carlo_count": model.monte_carlo_count,
            "criteria": json.dumps(model.criteria),
            "alternatives": json.dumps(model.alternatives),
            "significance_levels": json.dumps(model.significance_levels),
            "is_generation_done": int(model.is_generation_done),
            "is_execution_done": int(model.is_execution_done),
            "is_report_building_done": int(model.is_report_building_done),
        }

    def _row_to_model(self, row: dict) -> ExperimentModel:
        """Convert database row to ExperimentModel."""
        return ExperimentModel(
            experiment_type=row["experiment_type"],
            storage_connection=row["storage_connection"],
            run_mode=row["run_mode"],
            hypothesis=row["hypothesis"],
            generator_type=row["generator_type"],
            executor_type=row["executor_type"],
            report_builder_type=row["report_builder_type"],
            sample_sizes=json.loads(row["sample_sizes"]),
            monte_carlo_count=row["monte_carlo_count"],
            criteria=json.loads(row["criteria"]),
            alternatives=json.loads(row["alternatives"]),
            significance_levels=json.loads(row["significance_levels"]),
            is_generation_done=bool(row["is_generation_done"]),
            is_execution_done=bool(row["is_execution_done"]),
            is_report_building_done=bool(row["is_report_building_done"]),
        )

    def insert_data(self, data: ExperimentModel) -> None:
        """Insert or update experiment configuration."""
        conn = self._get_connection()
        row_data = self._model_to_row(data)

        # Remove status flags for upsert comparison
        insert_data = row_data.copy()
        for status_field in ["is_generation_done", "is_execution_done", "is_report_building_done"]:
            insert_data.pop(status_field)

        columns = ", ".join(insert_data.keys())
        placeholders = ", ".join("?" * len(insert_data))
        values = list(insert_data.values())

        # Upsert with conflict handling
        with conn:
            conn.execute(
                f"""
                INSERT INTO experiments (
                    {columns},
                    is_generation_done,
                    is_execution_done,
                    is_report_building_done
                )
                VALUES (
                    {placeholders},
                    {int(data.is_generation_done)},
                    {int(data.is_execution_done)},
                    {int(data.is_report_building_done)}
                )
                ON CONFLICT (
                    experiment_type, storage_connection, run_mode, hypothesis,
                    generator_type, executor_type, report_builder_type,
                    sample_sizes, monte_carlo_count, criteria,
                    alternatives, significance_levels
                )
                DO UPDATE SET
                    is_generation_done = excluded.is_generation_done,
                    is_execution_done = excluded.is_execution_done,
                    is_report_building_done = excluded.is_report_building_done
            """,
                values,
            )

    def get_data(self, query: ExperimentQuery) -> ExperimentModel | None:
        """Get experiment configuration by query."""
        conn = self._get_connection()

        # Convert query to search format
        search_data = {
            "experiment_type": query.experiment_type,
            "storage_connection": query.storage_connection,
            "run_mode": query.run_mode,
            "hypothesis": query.hypothesis,
            "generator_type": query.generator_type,
            "executor_type": query.executor_type,
            "report_builder_type": query.report_builder_type,
            "sample_sizes": json.dumps(query.sample_sizes),
            "monte_carlo_count": query.monte_carlo_count,
            "criteria": json.dumps(query.criteria),
            "alternatives": json.dumps(query.alternatives),
            "significance_levels": json.dumps(query.significance_levels),
        }

        conditions = []
        values = []
        for key, value in search_data.items():
            conditions.append(f"{key} = ?")
            values.append(value)

        sql = f"""
            SELECT * FROM experiments
            WHERE {' AND '.join(conditions)}
        """

        cursor = conn.execute(sql, values)
        row = cursor.fetchone()

        if not row:
            return None

        # Convert row to dict
        columns = [col[0] for col in cursor.description]
        row_dict = dict(zip(columns, row, strict=True))

        return self._row_to_model(row_dict)

    def delete_data(self, query: ExperimentQuery) -> None:
        """Delete experiment configuration by query."""
        conn = self._get_connection()

        # Convert query to search format
        search_data = {
            "experiment_type": query.experiment_type,
            "storage_connection": query.storage_connection,
            "run_mode": query.run_mode,
            "hypothesis": query.hypothesis,
            "generator_type": query.generator_type,
            "executor_type": query.executor_type,
            "report_builder_type": query.report_builder_type,
            "sample_sizes": json.dumps(query.sample_sizes),
            "monte_carlo_count": query.monte_carlo_count,
            "criteria": json.dumps(query.criteria),
            "alternatives": json.dumps(query.alternatives),
            "significance_levels": json.dumps(query.significance_levels),
        }

        conditions = []
        values = []
        for key, value in search_data.items():
            conditions.append(f"{key} = ?")
            values.append(value)

        sql = f"""
            DELETE FROM experiments
            WHERE {' AND '.join(conditions)}
        """

        with conn:
            conn.execute(sql, values)

    def get_experiment_id(self, query: ExperimentQuery) -> int | None:
        """Get experiment ID by query."""
        conn = self._get_connection()

        # Convert query to search format
        search_data = {
            "experiment_type": query.experiment_type,
            "storage_connection": query.storage_connection,
            "run_mode": query.run_mode,
            "hypothesis": query.hypothesis,
            "generator_type": query.generator_type,
            "executor_type": query.executor_type,
            "report_builder_type": query.report_builder_type,
            "sample_sizes": json.dumps(query.sample_sizes),
            "monte_carlo_count": query.monte_carlo_count,
            "criteria": json.dumps(query.criteria),
            "alternatives": json.dumps(query.alternatives),
            "significance_levels": json.dumps(query.significance_levels),
        }

        conditions = []
        values = []
        for key, value in search_data.items():
            conditions.append(f"{key} = ?")
            values.append(value)

        sql = f"""
            SELECT id FROM experiments
            WHERE {' AND '.join(conditions)}
        """

        cursor = conn.execute(sql, values)
        row = cursor.fetchone()

        if not row:
            raise ValueError("Experiment not found")

        return row[0]

    def set_generation_done(self, experiment_id: int) -> None:
        """Mark generation step as completed."""
        self._update_status(experiment_id, "is_generation_done", 1)

    def set_execution_done(self, experiment_id: int) -> None:
        """Mark execution step as completed."""
        self._update_status(experiment_id, "is_execution_done", 1)

    def set_report_building_done(self, experiment_id: int) -> None:
        """Mark report building step as completed."""
        self._update_status(experiment_id, "is_report_building_done", 1)

    def _update_status(self, experiment_id: int, field: str, value: int) -> None:
        """Update a status field for an experiment."""
        conn = self._get_connection()
        with conn:
            conn.execute(
                f"""
                UPDATE experiments
                SET {field} = ?
                WHERE id = ?
            """,
                (value, experiment_id),
            )
