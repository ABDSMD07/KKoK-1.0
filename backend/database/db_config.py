import os


DB_CONFIG = {
    "host": os.getenv("PS26018_DB_HOST", "localhost"),
    "port": int(os.getenv("PS26018_DB_PORT", "5432")),
    "database": os.getenv("PS26018_DB_NAME", "P_S26018"),
    "user": os.getenv("PS26018_DB_USER", "postgres"),
    "password": os.getenv("PS26018_DB_PASSWORD", ""),
}