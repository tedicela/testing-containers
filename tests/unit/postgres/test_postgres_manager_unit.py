import pytest
from psycopg import sql

import testing_containers.postgres.postgres_manager as pm
from testing_containers.models import DBConfig
from testing_containers.postgres.postgres_manager import PostgresManager

# --- helpers: dummy psycopg connection/cursor --------------------------------


class DummyCursor:
    def __init__(self, store):
        self.store = store  # list of ("execute", stmt, params)

    def execute(self, stmt, params=None):
        self.store.append(("execute", stmt, params))

    # context manager protocol
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class DummyConn:
    def __init__(self, store):
        self.store = store
        self.autocommit = False
        self.closed = False

    def cursor(self):
        return DummyCursor(self.store)

    def close(self) -> None:
        self.closed = True

    # context manager protocol
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


@pytest.fixture
def cfg():
    return DBConfig(host="localhost", name="postgres", user="u", password="p", port=5432)


@pytest.fixture
def store():
    return []  # collects cursor.execute calls


@pytest.fixture
def patch_connect(monkeypatch, store):
    """Monkeypatch pm.connect to return a DummyConn and expose call counter."""
    calls = {"n": 0}

    def _fake_connect(*args, **kwargs):
        calls["n"] += 1
        return DummyConn(store)

    monkeypatch.setattr(pm, "connect", _fake_connect)
    return calls


# --- tests -------------------------------------------------------------------


def test__connect_caches_connection(cfg, store, patch_connect):
    mgr = PostgresManager(cfg)
    conn1 = mgr._connect()
    assert isinstance(conn1, DummyConn)
    conn2 = mgr._connect()
    assert conn2 is conn1  # cached
    assert patch_connect["n"] == 1  # connect called once

    # If connection is marked closed, _connect should call connect again
    conn1.closed = True  # type: ignore
    conn3 = mgr._connect()
    assert conn3 is not conn1
    assert patch_connect["n"] == 2


def test_is_postgres_ready_true(cfg, store, patch_connect, capsys):
    mgr = PostgresManager(cfg)
    assert mgr.is_postgres_ready() is True
    out = capsys.readouterr().out
    assert "PostgreSQL not ready" not in out


def test_is_postgres_ready_false_on_exception(cfg, monkeypatch, capsys):
    # Make pm.connect raise to simulate failure
    monkeypatch.setattr(pm, "connect", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    mgr = PostgresManager(cfg)
    assert mgr.is_postgres_ready() is False
    out = capsys.readouterr().out
    assert "PostgreSQL not ready: boom" in out


def test_create_database_executes_sql_with_autocommit(cfg, store, patch_connect, capsys):
    mgr = PostgresManager(cfg)
    mgr.create_database("my_test_db")

    # autocommit must have been enabled
    # (we can't see it directly after context exit, but we can infer that no exception occurred
    # and that statements were executed)
    executes = [x for x in store if x[0] == "execute"]
    assert len(executes) == 1
    stmt, params = executes[0][1], executes[0][2]

    # Statement must be a psycopg sql object and include CREATE DATABASE with the db name
    assert isinstance(stmt, sql.Composed | sql.SQL | str)
    assert "CREATE DATABASE" in str(stmt)
    assert "my_test_db" in str(stmt)
    assert params is None

    out = capsys.readouterr().out
    assert "Database my_test_db created successfully." in out


def test_drop_database_executes_terminate_and_drop(cfg, store, patch_connect, capsys):
    mgr = PostgresManager(cfg)
    mgr.drop_database("temp_db")

    executes = [x for x in store if x[0] == "execute"]
    # First call: terminate backends with paramized db name
    # Second call: DROP DATABASE IF EXISTS <identifier>
    assert len(executes) == 2

    # 1) terminate backends
    stmt1, params1 = executes[0][1], executes[0][2]
    assert "pg_terminate_backend" in str(stmt1)
    assert params1 == ("temp_db",)

    # 2) drop database (identifier-quoted)
    stmt2, params2 = executes[1][1], executes[1][2]
    assert "DROP DATABASE IF EXISTS" in str(stmt2)
    assert "temp_db" in str(stmt2)
    assert params2 is None

    out = capsys.readouterr().out
    assert "Database temp_db dropped successfully." in out


def test_destroy_calls_drop_on_testdb_name(cfg, monkeypatch):
    mgr = PostgresManager(cfg)
    called = {"name": None}
    monkeypatch.setattr(mgr, "drop_database", lambda name: called.__setitem__("name", name))
    mgr.destroy()
    assert called["name"] == mgr.testdb.name


def test_setup_testdb_happy_path_calls_drop_then_create(cfg, monkeypatch):
    mgr = PostgresManager(cfg)
    # Force readiness
    monkeypatch.setattr(mgr, "is_postgres_ready", lambda: True)

    calls = []
    monkeypatch.setattr(mgr, "drop_database", lambda name: calls.append(("drop", name)))
    monkeypatch.setattr(mgr, "create_database", lambda name: calls.append(("create", name)))

    mgr.setup_testdb()

    assert calls == [("drop", mgr.testdb.name), ("create", mgr.testdb.name)]


def test_setup_testdb_raises_when_not_ready(cfg, monkeypatch):
    mgr = PostgresManager(cfg)
    monkeypatch.setattr(mgr, "is_postgres_ready", lambda: False)

    with pytest.raises(RuntimeError) as ei:
        mgr.setup_testdb()
    assert "PostgreSQL is not accessible" in str(ei.value)
