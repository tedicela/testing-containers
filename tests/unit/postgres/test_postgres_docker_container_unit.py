import types

import pytest

import testing_containers.postgres.postgres_docker_container as pdc
from testing_containers.models import ContainerOptions


def _cp(returncode=0, stdout="", stderr=""):
    """Tiny CompletedProcess-like object."""
    return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


@pytest.fixture
def instance():
    # Build a real PostgresDockerContainer; we'll monkeypatch its `container` methods.
    return pdc.PostgresDockerContainer(
        port=5544, options=ContainerOptions(name="test-pg", should_stop=True, remove_on_stop=True)
    )


def test_is_postgres_ready_immediate_success(instance, monkeypatch, capsys):
    # Make the first exec call succeed
    monkeypatch.setattr(instance.container, "exec", lambda cmd: _cp(returncode=0))

    assert instance.is_postgres_ready(retries=3, delay=0) is True
    out = capsys.readouterr().out
    assert "PostgreSQL is ready!" in out


def test_is_postgres_ready_retries_then_success(instance, monkeypatch, capsys):
    # Fail twice, then succeed
    rcs = iter([1, 2, 0])

    def exec_seq(cmd):
        return _cp(returncode=next(rcs))

    monkeypatch.setattr(instance.container, "exec", exec_seq)
    monkeypatch.setattr(pdc.time, "sleep", lambda *_: None)

    assert instance.is_postgres_ready(retries=5, delay=0) is True
    out = capsys.readouterr().out
    assert "Waiting for PostgreSQL to be ready... (Attempt 1/5)" in out
    assert "Waiting for PostgreSQL to be ready... (Attempt 2/5)" in out
    assert "PostgreSQL is ready!" in out


def test_is_postgres_ready_gives_up(instance, monkeypatch, capsys):
    # Always fail
    monkeypatch.setattr(instance.container, "exec", lambda cmd: _cp(returncode=1))
    monkeypatch.setattr(pdc.time, "sleep", lambda *_: None)

    assert instance.is_postgres_ready(retries=3, delay=0) is False
    out = capsys.readouterr().out
    assert "PostgreSQL is not ready after multiple attempts." in out


def test_ensure_postgres_is_ready_happy_path(instance, monkeypatch, capsys):
    # Docker ready → start_container() called → PG ready immediately
    start_calls = {"n": 0}
    monkeypatch.setattr(instance.container, "is_docker_ready", lambda: True)
    monkeypatch.setattr(
        instance.container,
        "start_container",
        lambda: start_calls.__setitem__("n", start_calls["n"] + 1),
    )
    monkeypatch.setattr(instance.container, "exec", lambda cmd: _cp(returncode=0))

    instance.ensure_postgres_is_ready()

    assert start_calls["n"] == 1
    out = capsys.readouterr().out
    assert "PostgreSQL is ready!" in out


def test_ensure_postgres_is_ready_exits_when_docker_not_ready(instance, monkeypatch):
    monkeypatch.setattr(instance.container, "is_docker_ready", lambda: False)
    # Guard: start_container should not be called
    monkeypatch.setattr(
        instance.container,
        "start_container",
        lambda: (_ for _ in ()).throw(AssertionError("start_container should not be called")),
    )

    with pytest.raises(SystemExit) as ei:
        instance.ensure_postgres_is_ready()
    assert ei.value.code == 1


def test_ensure_postgres_is_ready_exits_when_pg_not_ready(instance, monkeypatch):
    start_calls = {"n": 0}
    monkeypatch.setattr(pdc.time, "sleep", lambda *_: None)
    monkeypatch.setattr(instance.container, "is_docker_ready", lambda: True)
    monkeypatch.setattr(
        instance.container,
        "start_container",
        lambda: start_calls.__setitem__("n", start_calls["n"] + 1),
    )
    monkeypatch.setattr(instance.container, "exec", lambda cmd: _cp(returncode=1))

    with pytest.raises(SystemExit) as ei:
        instance.ensure_postgres_is_ready()
    assert ei.value.code == 1
    assert start_calls["n"] == 1  # it tried to start once


def test_stop_container_delegates(instance, monkeypatch):
    # Ensure PostgresDockerContainer.stop_container just delegates to container.stop_container
    called = {"n": 0, "m": 0}
    monkeypatch.setattr(
        instance.container, "stop_container", lambda: called.__setitem__("n", called["n"] + 1)
    )
    monkeypatch.setattr(
        instance.container, "remove_container", lambda: called.__setitem__("m", called["m"] + 1)
    )
    instance.stop_container()
    assert called["n"] == 1
    assert called["m"] == 1
