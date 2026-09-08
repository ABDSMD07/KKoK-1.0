import psycopg2
from psycopg2.extras import RealDictCursor

from .db_config import DB_CONFIG


class DatabaseManager:
    """PostgreSQL database manager for PS 26018."""

    def __init__(self):
        self.connection = None

    def connect(self):
        """Establish connection to PostgreSQL."""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
            )

        return self.connection

    def close(self):
        """Close the database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def test_connection(self):
        """Test whether the database connection works."""
        connection = self.connect()

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user;")
            result = cursor.fetchone()

        return {
            "database": result[0],
            "user": result[1],
        }

    def execute(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE or other SQL statements."""
        connection = self.connect()

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    def fetch_one(self, query, params=None):
        """Fetch one row as a dictionary."""
        connection = self.connect()

        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query, params=None):
        """Fetch all rows as dictionaries."""
        connection = self.connect()

        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()