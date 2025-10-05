import json
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from pysatl_experiment.persistence.model.experiment.experiment import (
    ExperimentModel,
    ExperimentQuery,
    IExperimentStorage,
)


TABLE_NAME = "experiments"
logger = logging.getLogger(__name__)  # TODO: ????


class PostgreSQLExperimentStorage(IExperimentStorage):
    """
    PostgreSQL implementation for experiment configuration storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.table_name = TABLE_NAME
        self._initialized = False

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.connection_string)

    def init(self) -> None:
        """
        Initialize the database and create tables.
        """
        if self._initialized:
            return

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            experiment_type VARCHAR(255) NOT NULL,
            storage_connection TEXT NOT NULL,
            run_mode VARCHAR(100) NOT NULL,
            report_mode VARCHAR(100) NOT NULL,
            hypothesis TEXT NOT NULL,
            generator_type VARCHAR(255) NOT NULL,
            executor_type VARCHAR(255) NOT NULL,
            report_builder_type VARCHAR(255) NOT NULL,
            sample_sizes JSONB NOT NULL,
            monte_carlo_count INTEGER NOT NULL,
            criteria JSONB NOT NULL,
            alternatives JSONB NOT NULL,
            significance_levels JSONB NOT NULL,
            is_generation_done BOOLEAN DEFAULT FALSE,
            is_execution_done BOOLEAN DEFAULT FALSE,
            is_report_building_done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(experiment_type, storage_connection, run_mode, hypothesis,
                   generator_type, executor_type, report_builder_type,
                   sample_sizes, monte_carlo_count, criteria, alternatives,
                   significance_levels, report_mode),

            CONSTRAINT valid_monte_carlo_count CHECK (monte_carlo_count > 0),
            CONSTRAINT valid_sample_sizes CHECK (jsonb_array_length(sample_sizes) > 0),
            CONSTRAINT valid_significance_levels CHECK (jsonb_array_length(significance_levels) > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_type
        ON {self.table_name} (experiment_type);

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_status
        ON {self.table_name} (is_generation_done, is_execution_done, is_report_building_done);

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_composite
        ON {self.table_name} (experiment_type, generator_type, executor_type);

        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS update_{self.table_name}_updated_at ON {self.table_name};
        CREATE TRIGGER update_{self.table_name}_updated_at
            BEFORE UPDATE ON {self.table_name}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_table_query)
                    conn.commit()
                    self._initialized = True
                    logger.info(f"Experiment storage table '{self.table_name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize experiment storage: {e}")
            raise

    def insert_data(self, model: ExperimentModel) -> None:
        """
        Insert or update experiment configuration.
        """
        if not self._initialized:
            self.init()

        insert_query = f"""
        INSERT INTO {self.table_name}
        (experiment_type, storage_connection, run_mode, report_mode, hypothesis,
         generator_type, executor_type, report_builder_type, sample_sizes,
         monte_carlo_count, criteria, alternatives, significance_levels,
         is_generation_done, is_execution_done, is_report_building_done)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (experiment_type, storage_connection, run_mode, hypothesis,
                    generator_type, executor_type, report_builder_type,
                    sample_sizes, monte_carlo_count, criteria, alternatives,
                    significance_levels, report_mode)
        DO UPDATE SET
            report_mode = EXCLUDED.report_mode,
            is_generation_done = EXCLUDED.is_generation_done,
            is_execution_done = EXCLUDED.is_execution_done,
            is_report_building_done = EXCLUDED.is_report_building_done,
            updated_at = CURRENT_TIMESTAMP;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        insert_query,
                        (
                            model.experiment_type,
                            model.storage_connection,
                            model.run_mode,
                            model.report_mode,
                            model.hypothesis,
                            model.generator_type,
                            model.executor_type,
                            model.report_builder_type,
                            json.dumps(model.sample_sizes),
                            model.monte_carlo_count,
                            json.dumps(model.criteria),
                            json.dumps(model.alternatives),
                            json.dumps(model.significance_levels),
                            model.is_generation_done,
                            model.is_execution_done,
                            model.is_report_building_done,
                        ),
                    )
                    conn.commit()
                    logger.debug(f"Experiment configuration inserted: {model.experiment_type}")
        except Exception as e:
            logger.error(f"Failed to insert experiment configuration: {e}")
            raise

    def get_data(self, query: ExperimentQuery) -> ExperimentModel | None:
        """
        Get experiment configuration by query.
        """
        if not self._initialized:
            self.init()  # TODO: exception???

        select_query = f"""
        SELECT id, experiment_type, storage_connection, run_mode, report_mode, hypothesis,
               generator_type, executor_type, report_builder_type, sample_sizes,
               monte_carlo_count, criteria, alternatives, significance_levels,
               is_generation_done, is_execution_done, is_report_building_done
        FROM {self.table_name}
        WHERE experiment_type = %s
          AND storage_connection = %s
          AND run_mode = %s
          AND hypothesis = %s
          AND generator_type = %s
          AND executor_type = %s
          AND report_builder_type = %s
          AND sample_sizes = %s
          AND monte_carlo_count = %s
          AND criteria = %s
          AND alternatives = %s
          AND significance_levels = %s
          AND report_mode = %s;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        select_query,
                        (
                            query.experiment_type,
                            query.storage_connection,
                            query.run_mode,
                            query.hypothesis,
                            query.generator_type,
                            query.executor_type,
                            query.report_builder_type,
                            json.dumps(query.sample_sizes),
                            query.monte_carlo_count,
                            json.dumps(query.criteria),
                            json.dumps(query.alternatives),
                            json.dumps(query.significance_levels),
                            query.report_mode,
                        ),
                    )
                    result = cursor.fetchone()

                    if result:
                        return ExperimentModel(
                            experiment_type=result["experiment_type"],
                            storage_connection=result["storage_connection"],
                            run_mode=result["run_mode"],
                            report_mode=result["report_mode"],
                            hypothesis=result["hypothesis"],
                            generator_type=result["generator_type"],
                            executor_type=result["executor_type"],
                            report_builder_type=result["report_builder_type"],
                            sample_sizes=json.loads(result["sample_sizes"]),
                            monte_carlo_count=result["monte_carlo_count"],
                            criteria=json.loads(result["criteria"]),
                            alternatives=json.loads(result["alternatives"]),
                            significance_levels=json.loads(result["significance_levels"]),
                            is_generation_done=result["is_generation_done"],
                            is_execution_done=result["is_execution_done"],
                            is_report_building_done=result["is_report_building_done"],
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get experiment configuration: {e}")
            raise

    def delete_data(self, query: ExperimentQuery) -> None:
        """
        Delete experiment configuration by query.
        """
        if not self._initialized:  # TODO: exception??
            self.init()

        delete_query = f"""
        DELETE FROM {self.table_name}
        WHERE experiment_type = %s
          AND storage_connection = %s
          AND run_mode = %s
          AND hypothesis = %s
          AND generator_type = %s
          AND executor_type = %s
          AND report_builder_type = %s
          AND sample_sizes = %s
          AND monte_carlo_count = %s
          AND criteria = %s
          AND alternatives = %s
          AND significance_levels = %s
          AND report_mode = %s;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        delete_query,
                        (
                            query.experiment_type,
                            query.storage_connection,
                            query.run_mode,
                            query.hypothesis,
                            query.generator_type,
                            query.executor_type,
                            query.report_builder_type,
                            json.dumps(query.sample_sizes),
                            query.monte_carlo_count,
                            json.dumps(query.criteria),
                            json.dumps(query.alternatives),
                            json.dumps(query.significance_levels),
                            query.report_mode,
                        ),
                    )
                    conn.commit()
                    logger.debug(f"Experiment configuration deleted: {query.experiment_type}")
        except Exception as e:
            logger.error(f"Failed to delete experiment configuration: {e}")
            raise

    def get_experiment_id(self, query: ExperimentQuery) -> int | None:
        """
        Get experiment ID by query.
        """
        if not self._initialized:
            self.init()

        select_query = f"""
        SELECT id
        FROM {self.table_name}
        WHERE experiment_type = %s
          AND storage_connection = %s
          AND run_mode = %s
          AND hypothesis = %s
          AND generator_type = %s
          AND executor_type = %s
          AND report_builder_type = %s
          AND sample_sizes = %s
          AND monte_carlo_count = %s
          AND criteria = %s
          AND alternatives = %s
          AND significance_levels = %s
          AND report_mode = %s;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        select_query,
                        (
                            query.experiment_type,
                            query.storage_connection,
                            query.run_mode,
                            query.hypothesis,
                            query.generator_type,
                            query.executor_type,
                            query.report_builder_type,
                            json.dumps(query.sample_sizes),
                            query.monte_carlo_count,
                            json.dumps(query.criteria),
                            json.dumps(query.alternatives),
                            json.dumps(query.significance_levels),
                            query.report_mode,
                        ),
                    )
                    result = cursor.fetchone()
                    return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get experiment ID: {e}")
            raise

    def set_generation_done(self, experiment_id: int) -> None:
        """
        Mark generation step as completed.
        """
        self._update_experiment_status(experiment_id, "is_generation_done", True)

    def set_execution_done(self, experiment_id: int) -> None:
        """
        Mark execution step as completed.
        """
        self._update_experiment_status(experiment_id, "is_execution_done", True)

    def set_report_building_done(self, experiment_id: int) -> None:
        """
        Mark report building step as completed.
        """
        self._update_experiment_status(experiment_id, "is_report_building_done", True)

    def _update_experiment_status(self, experiment_id: int, field: str, value: bool) -> None:
        """
        Update a status field for an experiment.
        """
        if not self._initialized:
            self.init()

        update_query = f"""
        UPDATE {self.table_name}
        SET {field} = %s
        WHERE id = %s;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(update_query, (value, experiment_id))
                    conn.commit()
                    logger.debug(f"Updated {field} to {value} for experiment {experiment_id}")
        except Exception as e:
            logger.error(f"Failed to update experiment status: {e}")
            raise
