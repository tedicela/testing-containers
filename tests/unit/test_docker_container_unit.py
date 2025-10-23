import types
import pytest
from testing_containers.docker_container import DockerContainer


@pytest.fixture
def container() -> DockerContainer:
    return DockerContainer(
        container_name="ns-testing-psql", 
        image="postgres:16.3",
        expose_ports=["5433:5432"],
        env={
            "POSTGRES_DB": "postgres",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "password",
        }
    )

def test_container_name_and_defaults(container: DockerContainer):
    assert container.container_name == "ns-testing-psql"
    assert container.image == "postgres:16.3"

def test_is_docker_installed_yes(container: DockerContainer, fake_run_success):
    assert container.is_docker_installed() is True
    assert ["docker", "--version"] in fake_run_success

def test_is_docker_installed_no(container: DockerContainer, fake_run_fail):
    assert container.is_docker_installed() is False
    assert ["docker", "--version"] in fake_run_fail

def test_is_docker_running_yes(container: DockerContainer, fake_run_success):
    assert container.is_docker_running() is True
    assert ["docker", "info"] in fake_run_success

def test_is_docker_running_no(container: DockerContainer, fake_run_fail):
    assert container.is_docker_running() is False
    assert ["docker", "info"] in fake_run_fail

def test_iis_docker_ready_yes(monkeypatch, container: DockerContainer):
    """Should return True when both checks succeed."""
    monkeypatch.setattr(container, "is_docker_installed", lambda: True)
    monkeypatch.setattr(container, "is_docker_running", lambda: True)

    assert container.is_docker_ready() is True

def test_is_docker_ready_false_not_installed(monkeypatch, container: DockerContainer, capsys):
    """Should return False when Docker is not installed."""
    monkeypatch.setattr(container, "is_docker_installed", lambda: False)
    monkeypatch.setattr(container, "is_docker_running", lambda: True)

    result = container.is_docker_ready()
    captured = capsys.readouterr()

    assert result is False
    assert "Docker is not installed" in captured.out

def test_is_docker_ready_false_not_running(monkeypatch, container: DockerContainer, capsys):
    """Should return False when Docker daemon isn’t running."""
    monkeypatch.setattr(container, "is_docker_installed", lambda: True)
    monkeypatch.setattr(container, "is_docker_running", lambda: False)

    result = container.is_docker_ready()
    captured = capsys.readouterr()

    assert result is False
    assert "Docker daemon is not running" in captured.out

def test_is_container_running_true(monkeypatch, container: DockerContainer):
    """Should return True when container name appears in stdout."""
    fake_result = types.SimpleNamespace(
        stdout=f"{container.container_name}\n", 
        returncode=0
    )
    monkeypatch.setattr(container, "_run_command", lambda cmd: fake_result)

    result = container.is_container_running()

    assert result is True

def test_is_container_running_false(monkeypatch, container: DockerContainer):
    """Should return False when stdout is empty or different name."""
    fake_result = types.SimpleNamespace(stdout="other-container\n", returncode=0)
    monkeypatch.setattr(container, "_run_command", lambda cmd: fake_result)

    result = container.is_container_running()

    assert result is False

def test_container_exists_true(monkeypatch, container: DockerContainer):
    """Should return True when container name is found in stdout."""
    fake_result = types.SimpleNamespace(
        stdout=f"{container.container_name}\n",
        returncode=0
    )
    monkeypatch.setattr(container, "_run_command", lambda cmd: fake_result)

    assert container.container_exists() is True

def test_container_exists_false(monkeypatch, container: DockerContainer):
    """Should return False when name not in stdout."""
    fake_result = types.SimpleNamespace(stdout="other-container\n", returncode=0)
    monkeypatch.setattr(container, "_run_command", lambda cmd: fake_result)

    assert container.container_exists() is False

def test_start_container_already_running(monkeypatch, container: DockerContainer, capsys):
    """Should return early if container is already running."""
    monkeypatch.setattr(container, "is_container_running", lambda: True)
    monkeypatch.setattr(container, "container_exists", lambda: True)
    monkeypatch.setattr(
        container, 
        "_run_command", 
        lambda: pytest.fail("_run_command should not be called when container is already running")
    )

    container.start_container()
    out = capsys.readouterr().out
    assert f"Container {container.container_name} is already running." in out

def test_start_container_existing_stopped(
    monkeypatch, 
    container: DockerContainer, 
    capsys, 
    fake_run_success
):
    """Should call `docker start <name>` when container exists but is stopped."""
    monkeypatch.setattr(container, "is_container_running", lambda: False)
    monkeypatch.setattr(container, "container_exists", lambda: True)

    container.start_container()
    out = capsys.readouterr().out

    assert f"Starting existing container: {container.container_name}" in out
    assert ['docker', 'start', 'ns-testing-psql'] in fake_run_success
    assert f"✅ Container '{container.container_name}' started on ports {container.expose_ports}" in out

def test_start_container_create_and_run(
    monkeypatch, 
    container: DockerContainer, 
    capsys, 
    fake_run_success
):
    """Should build correct docker run command when container does not exist."""
    monkeypatch.setattr(container, "is_container_running", lambda: False)
    monkeypatch.setattr(container, "container_exists", lambda: False)

    container.start_container()
    out = capsys.readouterr().out

    # expected env flags
    expected_env = []
    for k, v in container.env.items():
        expected_env += ["-e", f"{k}={v}"]

    expected_ports = []
    for mapping in container.expose_ports:
        host, cont = mapping.split(":")
        expected_ports += ["-p", f"{host}:{cont}"]

    expected_cmd = [
        "docker", "run", "--name", container.container_name,
        *expected_env,
        *expected_ports,
        "-d", container.image,
    ]

    assert "Creating and starting new container" in out
    assert expected_cmd in fake_run_success
    assert f"✅ Container '{container.container_name}' started on ports {container.expose_ports}" in out

def test_stop_container_running_only_stop(
    monkeypatch, 
    container: DockerContainer, 
    capsys, 
    fake_run_success
):
    """If running and remove_container=False, call `docker stop` only."""
    monkeypatch.setattr(container, "is_container_running", lambda: True)
    container.stop_container()
    out = capsys.readouterr().out

    assert ["docker", "stop", container.container_name] in fake_run_success
    assert f"Stopping container: {container.container_name}..." in out
    assert f"✅ Container {container.container_name} has been stopped." in out

def test_remove_container_running(
    monkeypatch, 
    container: DockerContainer, 
    capsys,
    fake_run_success
):
    """If running and remove_container=True, call `docker stop` then `docker rm`."""
    monkeypatch.setattr(container, "is_container_running", lambda: True)

    container.remove_container()
    out = capsys.readouterr().out

    assert ["docker", "stop", container.container_name] in fake_run_success
    assert ["docker", "rm", container.container_name] in fake_run_success
    assert f"Stopping container: {container.container_name}..." in out
    assert f"✅ Container {container.container_name} has been stopped and removed." in out

def test_stop_container_not_running(monkeypatch, container: DockerContainer, capsys):
    """If not running, do not call docker; just print a message."""
    monkeypatch.setattr(container, "is_container_running", lambda: False)
    monkeypatch.setattr(
        container, 
        "_run_command", 
        lambda: pytest.fail("_run_command must not be called when container is not running")
    )

    container.stop_container()
    out = capsys.readouterr().out

    assert f"Container {container.container_name} is not running." in out
