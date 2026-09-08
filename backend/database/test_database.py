from database.db_manager import DatabaseManager


def main():
    print("POSTGRESQL CONNECTION TEST")
    print("-" * 40)

    db = DatabaseManager()

    try:
        result = db.test_connection()

        print("Connection: SUCCESS")
        print(f"Database:   {result['database']}")
        print(f"User:       {result['user']}")

    except Exception as e:
        print("Connection: FAILED")
        print(f"Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()