import os
import subprocess
import sys


class DockerContainer:
    def __init__(self, 
        image: str,
        container_name: str, 
        expose_ports: list[str] = [],
        env: dict = {},
    ):
        self.image = image
        self.container_name = container_name
        self.expose_ports = expose_ports
        self.env = env

    def _run_command(self, command: list, check=False, env = {}) -> subprocess.CompletedProcess:
        """Runs a shell command and returns the completed process."""
        try:
            return subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=check,
                env={**os.environ, **env}
            )
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            sys.exit(1)

    def is_docker_installed(self) -> bool:
        """Checks if Docker is installed."""
        result = self._run_command(["docker", "--version"])
        return result.returncode == 0

    def is_docker_running(self) -> bool:
        """Checks if the Docker daemon is running."""
        result = self._run_command(["docker", "info"])
        return result.returncode == 0

    def is_docker_ready(self) -> bool:
        """Ensures Docker is ready to use."""
        if not self.is_docker_installed():
            print("⚠️  Docker is not installed. Please install Docker.")
            return False

        if not self.is_docker_running():
            print("⚠️  Docker daemon is not running. Please start Docker.")
            return False
        return True
    
    def is_container_running(self) -> bool:
        """Checks if the specified container is running."""
        result = self._run_command(
            ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"]
        )
        return self.container_name in result.stdout.strip()

    def container_exists(self) -> bool:
        """Checks if the container exists (running or stopped)."""
        result = self._run_command(
            ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"]
        )
        return self.container_name in result.stdout.strip()
    
    def exec(self, command: list) -> subprocess.CompletedProcess:
        return self._run_command(["docker", "exec", self.container_name, *command])
    
    def start_container(self):
        """Starts the container using `docker run` if it's not running."""
        if self.is_container_running():
            print(f"Container {self.container_name} is already running.")
            return

        if self.container_exists():
            print(f"▶️ Starting existing container: {self.container_name}...")
            command = ["docker", "start", self.container_name]
        else:
            print(f"🚀 Creating and starting new container: {self.container_name}...")
            env_options = []
            for k, v in self.env.items():
                env_options += ["-e", f"{k}={v}"]

            port_options = []
            for p in self.expose_ports:
                expose_port = p.split(":")
                port_options += ["-p", f"{expose_port[0]}:{expose_port[1]}"]
                
            command = [
                "docker", "run", "--name", self.container_name,
                *env_options, 
                *port_options,
                "-d", self.image,
            ]

        self._run_command(command, check=True)
        print(f"✅ Container '{self.container_name}' started on ports {self.expose_ports}")
    
    def stop_container(self):
        """Stops and removes the container if it's running."""
        if self.is_container_running():
            print(f"Stopping container: {self.container_name}...")
            self._run_command(["docker", "stop", self.container_name], check=True)
            print(f"✅ Container {self.container_name} has been stopped.")
        else:
            print(f"Container {self.container_name} is not running.")

    def remove_container(self):
        """Removes the container"""
        if self.is_container_running():
            print(f"Stopping container: {self.container_name}...")
            self._run_command(["docker", "stop", self.container_name], check=True)
        else:
            print(f"Container {self.container_name} is not running.")

        self._run_command(["docker", "rm", self.container_name], check=True)
        print(f"✅ Container {self.container_name} has been stopped and removed.")
