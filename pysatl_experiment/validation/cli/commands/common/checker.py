import sqlite3


class SQLiteCriticalValueChecker:
    """
    A utility class to check for the existence of pre-calculated
    critical values in an SQLite database.

    This class connects to a specific SQLite database and provides a method
    to query if a result for a given hypothesis, criterion, and sample size
    has already been stored.
    """

    def __init__(self, connection_string: str):
        """
        Initializes the checker and connects to the SQLite database.

        Args:
            connection_string (str): The file path or connection string for the
                SQLite database.

        Raises:
            ConnectionError: If the connection to the database fails.
        """
        self.connection_string = connection_string
        self.connection = None
        try:
            self.connection = sqlite3.connect(self.connection_string)
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to the database '{self.connection_string}': {e}")

    def check_exists(self, hypothesis: str, criterion_code: str, sample_size: int) -> bool:
        """
        Checks if a critical value for a specific parameter set exists in the DB.

        Args:
            hypothesis (str): The statistical hypothesis (e.g., "NORMAL").
            criterion_code (str): The short code for the statistical criterion (e.g., "KS").
            sample_size (int): The sample size used for the calculation.

        Returns:
            bool: True if a matching record exists, False otherwise.

        Raises:
            sqlite3.Error: If a critical error occurs during the SQL query execution.
        """
        if self.connection is None:
            return False

        sql_query = """
            SELECT EXISTS (
                SELECT 1
                FROM limit_distributions ld
                JOIN experiments e ON ld.experiment_id = e.id
                WHERE UPPER(e.hypothesis) = ?
                  AND ld.criterion_code = ?
                  AND ld.sample_size = ?
            )
        """
        params = (hypothesis.upper(), criterion_code, sample_size)

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query, params)
            row = cursor.fetchone()
            if row:
                return row[0] == 1
            return False
        except sqlite3.Error as e:
            print(f"A critical error occurred during SQL execution in check_exists: {e}")
            raise

    def close(self):
        """Closes the connection to the database."""
        if self.connection:
            self.connection.close()
