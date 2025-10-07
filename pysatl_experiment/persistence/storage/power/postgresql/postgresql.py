import json
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from pysatl_experiment.exceptions import StorageError
from pysatl_experiment.persistence.model.power.power import IPowerStorage, PowerModel, PowerQuery


logger = logging.getLogger(__name__)  # TODO ???


class PostgreSQLPowerStorage(IPowerStorage):
    """
    PostgreSQL implementation of PowerStorage interface.
    """

    def __init__(self, connection_string: str, table_name: str = "power_analysis"):
        """
        Initialize PostgreSQL power storage.

        Args:
            connection_string: PostgreSQL connection string
            table_name: Name of the table to store power analysis data
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self._initialized = False

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.connection_string)

    def init(self) -> None:
        """
        Initialize SQLite power storage and create tables.
        """
        if self._initialized:
            return

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            experiment_id INTEGER NOT NULL,
            criterion_code VARCHAR(255) NOT NULL,
            criterion_parameters JSONB NOT NULL,
            sample_size INTEGER NOT NULL,
            alternative_code VARCHAR(255) NOT NULL,
            alternative_parameters JSONB NOT NULL,
            monte_carlo_count INTEGER NOT NULL,
            significance_level FLOAT NOT NULL,
            results_criteria JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(experiment_id, criterion_code, sample_size, alternative_code,
                   monte_carlo_count, significance_level),

            CONSTRAINT valid_significance_level CHECK (significance_level > 0 AND significance_level < 1),
            CONSTRAINT valid_sample_size CHECK (sample_size > 0),
            CONSTRAINT valid_monte_carlo_count CHECK (monte_carlo_count > 0)
        );

        -- Индексы для ускорения поиска
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_experiment
        ON {self.table_name} (experiment_id);

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_criterion
        ON {self.table_name} (criterion_code, criterion_parameters);

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_alternative
        ON {self.table_name} (alternative_code, alternative_parameters);

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_sample_size
        ON {self.table_name} (sample_size);

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_composite
        ON {self.table_name} (criterion_code, alternative_code, sample_size, significance_level);
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_table_query)
                    conn.commit()
                    self._initialized = True
                    logger.info(f"Power storage table '{self.table_name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize power storage: {e}")
            raise StorageError

    def insert(self, model: PowerModel) -> None:
        """
        Insert a PowerModel into storage.

        Args:
            model: PowerModel to insert
        """
        self.insert_data(model)

    def insert_data(self, data: PowerModel) -> None:
        """
        Insert or replace a power entry.
        """
        if not self._initialized:
            self.init()

        insert_query = f"""
        INSERT INTO {self.table_name}
        (experiment_id, criterion_code, criterion_parameters, sample_size,
         alternative_code, alternative_parameters, monte_carlo_count,
         significance_level, results_criteria)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (experiment_id, criterion_code, sample_size, alternative_code,
                    monte_carlo_count, significance_level)
        DO UPDATE SET
            criterion_parameters = EXCLUDED.criterion_parameters,
            alternative_parameters = EXCLUDED.alternative_parameters,
            results_criteria = EXCLUDED.results_criteria,
            created_at = CURRENT_TIMESTAMP;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        insert_query,
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
                    conn.commit()
                    logger.debug(f"Power data inserted for experiment {data.experiment_id}")
        except Exception as e:
            logger.error(f"Failed to insert power data: {e}")
            raise StorageError

    def get(self, query: PowerQuery) -> PowerModel | None:
        """
        Get a PowerModel by query.

        Args:
            query: PowerQuery to search for

        Returns:
            PowerModel if found, None otherwise
        """
        return self.get_data(query)

    def get_data(self, query: PowerQuery) -> PowerModel | None:
        """
        Retrieve power data matching the query.
        """
        if not self._initialized:
            self.init()

        select_query = f"""
        SELECT experiment_id, criterion_code, criterion_parameters, sample_size,
               alternative_code, alternative_parameters, monte_carlo_count,
               significance_level, results_criteria
        FROM {self.table_name}
        WHERE criterion_code = %s
          AND criterion_parameters = %s
          AND sample_size = %s
          AND alternative_code = %s
          AND alternative_parameters = %s
          AND monte_carlo_count = %s
          AND significance_level = %s;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        select_query,
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
                    result = cursor.fetchone()

                    if result:
                        return PowerModel(
                            experiment_id=result["experiment_id"],
                            criterion_code=result["criterion_code"],
                            criterion_parameters=json.loads(result["criterion_parameters"]),
                            sample_size=result["sample_size"],
                            alternative_code=result["alternative_code"],
                            alternative_parameters=json.loads(result["alternative_parameters"]),
                            monte_carlo_count=result["monte_carlo_count"],
                            significance_level=result["significance_level"],
                            results_criteria=json.loads(result["results_criteria"]),
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get power data: {e}")
            raise StorageError

    def update(self, model: PowerModel) -> None:
        """
        Update a PowerModel (uses insert with upsert).

        Args:
            model: PowerModel to update
        """
        self.insert_data(model)

    def delete(self, query: PowerQuery) -> None:
        """
        Delete a PowerModel by query.

        Args:
            query: PowerQuery to identify record to delete
        """
        self.delete_data(query)

    def delete_data(self, query: PowerQuery) -> None:
        """
        Delete power data matching the query.
        """
        if not self._initialized:
            self.init()

        delete_query = f"""
        DELETE FROM {self.table_name}
        WHERE criterion_code = %s
          AND criterion_parameters = %s
          AND sample_size = %s
          AND alternative_code = %s
          AND alternative_parameters = %s
          AND monte_carlo_count = %s
          AND significance_level = %s;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        delete_query,
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
                    conn.commit()
                    logger.debug(f"Power data deleted for query: {query}")
        except Exception as e:
            logger.error(f"Failed to delete power data: {e}")
            raise StorageError

    # TODO: remove if unnecessary
    def get_by_experiment_id(self, experiment_id: int) -> list[PowerModel]:
        """
        Get all power data for a specific experiment ID.

        Args:
            experiment_id: Experiment ID to search for

        Returns:
            List of PowerModel objects
        """
        if not self._initialized:
            self.init()

        select_query = f"""
        SELECT experiment_id, criterion_code, criterion_parameters, sample_size,
               alternative_code, alternative_parameters, monte_carlo_count,
               significance_level, results_criteria
        FROM {self.table_name}
        WHERE experiment_id = %s
        ORDER BY criterion_code, alternative_code;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(select_query, (experiment_id,))
                    results = cursor.fetchall()

                    return [
                        PowerModel(
                            experiment_id=row["experiment_id"],
                            criterion_code=row["criterion_code"],
                            criterion_parameters=json.loads(row["criterion_parameters"]),
                            sample_size=row["sample_size"],
                            alternative_code=row["alternative_code"],
                            alternative_parameters=json.loads(row["alternative_parameters"]),
                            monte_carlo_count=row["monte_carlo_count"],
                            significance_level=row["significance_level"],
                            results_criteria=json.loads(row["results_criteria"]),
                        )
                        for row in results
                    ]
        except Exception as e:
            logger.error(f"Failed to get power data by experiment ID: {e}")
            raise StorageError

    def calculate_power(self, query: PowerQuery) -> float | None:
        """
        Calculate power from results_criteria.

        Args:
            query: PowerQuery to identify the data

        Returns:
            Power value (proportion of True in results_criteria) or None if not found
        """
        data = self.get_data(query)
        if data and data.results_criteria:
            true_count = sum(1 for result in data.results_criteria if result)
            return true_count / len(data.results_criteria)
        return None

    def batch_insert(self, models: list[PowerModel]) -> int:
        """
        Insert multiple PowerModel objects in batch.

        Args:
            models: List of PowerModel objects to insert

        Returns:
            Number of successfully inserted records
        """
        if not self._initialized:
            self.init()

        insert_query = f"""
        INSERT INTO {self.table_name}
        (experiment_id, criterion_code, criterion_parameters, sample_size,
         alternative_code, alternative_parameters, monte_carlo_count,
         significance_level, results_criteria)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (experiment_id, criterion_code, sample_size, alternative_code,
                    monte_carlo_count, significance_level)
        DO NOTHING;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    data_tuples = []
                    for model in models:
                        data_tuples.append(
                            (
                                model.experiment_id,
                                model.criterion_code,
                                json.dumps(model.criterion_parameters),
                                model.sample_size,
                                model.alternative_code,
                                json.dumps(model.alternative_parameters),
                                model.monte_carlo_count,
                                model.significance_level,
                                json.dumps(model.results_criteria),
                            )
                        )

                    cursor.executemany(insert_query, data_tuples)
                    conn.commit()
                    inserted_count = cursor.rowcount
                    logger.debug(f"Batch inserted {inserted_count} power records")
                    return inserted_count
        except Exception as e:
            logger.error(f"Failed to batch insert power data: {e}")
            raise StorageError

    def exists(self, query: PowerQuery) -> bool:
        """
        Check if power data exists for the given query.

        Args:
            query: PowerQuery to check

        Returns:
            True if data exists, False otherwise
        """
        return self.get_data(query) is not None
