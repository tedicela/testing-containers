from psycopg import Connection, connect, sql

from testing_containers.models import DBConfig


class PostgresManager:
    connection: Connection

    def __init__(self, master_db: DBConfig):
        self.master_db = master_db
        self.testdb = DBConfig(
            host=master_db.host,
            name="tmp_testdb",
            user=master_db.user,
            password=master_db.password,
            port=master_db.port,
        )

    def _connect(self) -> Connection:
        """Establish a connection to the specified database."""
        if not hasattr(self, "connection") or self.connection.closed:
            self.connection = connect(
                dbname=self.master_db.name,
                user=self.master_db.user,
                password=self.master_db.password,
                host=self.master_db.host,
                port=self.master_db.port,
            )
        return self.connection

    def is_postgres_ready(self) -> bool:
        """Check if PostgreSQL is ready for connection."""
        try:
            with self._connect():
                return True
        except Exception as e:
            print(f"⚠️  PostgreSQL not ready: {e}")
            return False

    def create_database(self, db_name: str) -> None:
        """Create a new database."""
        try:
            with self._connect() as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"✅ Database {db_name} created successfully.")
        except Exception as e:
            print(f"⚠️  Error creating database {db_name}: {e}")

    def drop_database(self, db_name: str) -> None:
        """Drop a database, terminating active connections if necessary."""
        try:
            with self._connect() as conn:
                conn.autocommit = True  # Allow dropping databases
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = %s AND pid <> pg_backend_pid();
                        """,
                        (db_name,),
                    )
                    cur.execute(
                        sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
                    )
                print(f"✅ Database {db_name} dropped successfully.")
        except Exception as e:
            print(f"Error dropping database {db_name}: {e}")

    def destroy(self) -> None:
        self.drop_database(self.testdb.name)

    def setup_testdb(self) -> None:
        """Drop and recreate the testdb database."""
        if self.is_postgres_ready():
            self.drop_database(self.testdb.name)
            self.create_database(self.testdb.name)
        else:
            raise RuntimeError("PostgreSQL is not accessible. Check credentials and connection.")
