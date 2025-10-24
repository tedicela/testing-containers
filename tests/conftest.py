import pytest


class DummyCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def dummy_completed_process():
    return DummyCompletedProcess


@pytest.fixture
def fake_run_success(monkeypatch, dummy_completed_process):
    """Mock subprocess.run; configurable per-test via closure."""
    calls = []

    def _fake_run(cmd, capture_output=True, text=None, check=False, env=None):
        calls.append(cmd)
        # default happy path
        return dummy_completed_process(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)
    return calls


@pytest.fixture
def fake_run_fail(monkeypatch, dummy_completed_process):
    """Mock subprocess.run; configurable per-test via closure."""
    calls = []

    def _fake_run(cmd, capture_output=True, text=None, check=False, env=None):
        calls.append(cmd)
        # default happy path
        return dummy_completed_process(returncode=1, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)
    return calls


@pytest.fixture
def fake_psycopg_connect(monkeypatch):
    """Mock psycopg.connect with minimal context manager + cursor behavior."""

    class DummyCursor:
        def __init__(self, store):
            self.store = store

        def execute(self, sql, params=None) -> None:
            self.store.append(("execute", sql, params))

        def close(self) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class DummyConn:
        def __init__(self, store):
            self.autocommit = False
            self.closed = False
            self.store = store

        def cursor(self) -> DummyCursor:
            return DummyCursor(self.store)

        def close(self) -> None:
            self.closed = True

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.close()
            return False

    store = []

    def _fake_connect(*args, **kwargs):
        return DummyConn(store)

    monkeypatch.setattr("psycopg.connect", _fake_connect)
    return store
