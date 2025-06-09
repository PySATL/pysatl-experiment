from stattest.persistence.model.random_values.random_values import (
    IRandomValuesStorage,
    RandomValuesAllModel,
    RandomValuesAllQuery,
    RandomValuesCountQuery,
    RandomValuesModel,
    RandomValuesQuery,
)

import sqlite3


class SQLiteRandomValuesStorage(IRandomValuesStorage):
    """
    SQLite random values storage.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None  # TODO

    def init(self) -> None:
        """
        Initialize SQLite random values storage.

        :return: None
        """
        self.connection = sqlite3.connect(self.connection_string)
        cursor = self.connection.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS random_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generator_name TEXT NOT NULL,
            generator_parameters TEXT NOT NULL,  -- Stored as JSON
            sample_size INTEGER NOT NULL,
            sample_id INTEGER NOT NULL,
            data TEXT NOT NULL,  -- Stored as JSON array
            UNIQUE(generator_name, generator_parameters, sample_size, sample_id)
        )""")  # TODO: check for library functions + remove JSONs by specification

        # Create index for faster queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_generator_params ON random_values
        (generator_name, generator_parameters, sample_size)
        """)  # TODO: do i really need it?

        self.connection.commit()

    def get_data(self, query: RandomValuesQuery) -> RandomValuesModel:
        """
        Get random values data from SQLite storage.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        cursor.execute("""
        SELECT sample_id, data FROM random_values
        WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ? AND sample_id = ?
        """, (query.generator_name, params_str, query.sample_size, query.sample_id))

        result = cursor.fetchone()
        if result is None:
            raise ValueError("Data not found")

        return RandomValuesModel(
            generator_name=query.generator_name,
            generator_parameters=query.generator_parameters,
            sample_size=query.sample_size,
            data=json.loads(result[1])
        )

        # raise NotImplementedError("Method is not yet implemented")

    def insert_data(self, data: RandomValuesModel) -> None:
        """
        Insert random values data to SQLite storage.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(data.generator_parameters)
        data_str = self._data_to_str(data.data)

        # TODO: delete sample_id field
        try:
            cursor.execute("""
            INSERT INTO random_values 
            (generator_name, generator_parameters, sample_size, sample_id, data)
            VALUES (?, ?, ?, ?, ?)
            """, (data.generator_name, params_str, data.sample_size, data.sample_id, data_str))
            self.connection.commit()
        except sqlite3.IntegrityError:
            # Update if record exists
            cursor.execute("""
            UPDATE random_values SET data = ?
            WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ? AND sample_id = ?
            """, (data_str, data.generator_name, params_str, data.sample_size, data.sample_id))
            self.connection.commit()

        # TODO: return code?
        # raise NotImplementedError("Method is not yet implemented")

    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """
        Get count of samples in SQLite storage.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        cursor.execute("""
            SELECT COUNT(DISTINCT sample_id) FROM random_values
            WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ?
            """, (query.generator_name, params_str, query.sample_size))

        return cursor.fetchone()[0]
        # raise NotImplementedError("Method is not yet implemented")

    def delete_data(self, query: RandomValuesQuery) -> None:
        """
        Delete random values data from SQLite storage.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        cursor.execute("""
            DELETE FROM random_values
            WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ? AND sample_id = ?
            """, (query.generator_name, params_str, query.sample_size, query.sample_id))
        self.connection.commit()

        # raise NotImplementedError("Method is not yet implemented")

    def insert_all_data(self, query: RandomValuesAllModel) -> None:
        """
        Insert all data into SQLite storage based on hypothesis and sample size.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        try:
            for sample_id, sample_data in enumerate(query.data):
                data_str = self._data_to_str(sample_data)
                cursor.execute("""
                INSERT OR REPLACE INTO random_values
                (generator_name, generator_parameters, sample_size, sample_id, data)
                VALUES (?, ?, ?, ?, ?)
                """, (query.generator_name, params_str, query.sample_size, sample_id, data_str))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

        # TODO: rewrite with child method??
        # raise NotImplementedError("Method is not yet implemented")

    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel]:
        """
        Get all data from SQLite storage based on hypothesis and sample size.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        cursor.execute("""
        SELECT sample_id, data FROM random_values
        WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ?
        ORDER BY sample_id
        """, (query.generator_name, params_str, query.sample_size))

        results = []
        for row in cursor.fetchall():
            results.append(RandomValuesModel(
                generator_name=query.generator_name,
                generator_parameters=query.generator_parameters,
                sample_size=query.sample_size,
                data=json.loads(row[1])
            ))

        return results
        # raise NotImplementedError("Method is not yet implemented")

    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """
        Delete all data from SQLite storage based on hypothesis and sample size.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        cursor.execute("""
        DELETE FROM random_values
        WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ?
        """, (query.generator_name, params_str, query.sample_size))
        self.connection.commit()

        # raise NotImplementedError("Method is not yet implemented")

    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel]:
        """
        Get count data based on hypothesis and sample size.
        """
        cursor = self.connection.cursor()
        params_str = self._params_to_str(query.generator_parameters)

        cursor.execute("""
        SELECT sample_id, data FROM random_values
        WHERE generator_name = ? AND generator_parameters = ? AND sample_size = ? AND sample_id = ?
        ORDER BY sample_id
        LIMIT ?
        """, (query.generator_name, params_str, query.sample_size, query.count))

        results = []
        for row in cursor.fetchall():
            results.append(RandomValuesModel(
                generator_name=query.generator_name,
                generator_parameters=query.generator_parameters,
                sample_size=query.sample_size,
                data=json.loads(row[1])
            ))

        return results

        # raise NotImplementedError("Method is not yet implemented")

    def __del__(self):  # TODO: proper codestyle
        """Clean up database connection."""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()

# TODO: how to test it - integration test with real db
# TODO: recycling somehow (inheritance from old version)??
# TODO: remove all query and rewrite with query