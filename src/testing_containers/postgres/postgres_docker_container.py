import time
import sys

from testing_containers.docker_container import DockerContainer
from testing_containers.models import DBConfig, ContainerOptions


class PostgresDockerContainer:
    def __init__(self, options: ContainerOptions, port: int = 5433):
        self.options = options
        self.master_db = DBConfig(
            name="postgres", user="postgres", password ="password", port=port,
        )
        self.container = DockerContainer(
            container_name=options.name or "testing-postgres",
            image=options.image or "postgres:16.3",
            expose_ports=[f"{self.master_db.port}:5432"],
            env={
                "POSTGRES_DB": self.master_db.name,
                "POSTGRES_USER": self.master_db.user,
                "POSTGRES_PASSWORD": self.master_db.password,
            },
        )

    def stop_container(self):
        if self.options.should_stop:
            self.container.stop_container()
            if self.options.remove_on_stop:
                self.container.remove_container()

    def start_container(self):
        if not self.container.is_docker_ready():
            sys.exit(1)

        self.container.start_container()

    def is_postgres_ready(self, retries=10, delay=3) -> bool:
        """Waits until PostgreSQL inside the Docker container is ready."""
        for attempt in range(retries):
            result = self.container.exec(["pg_isready", "-U", self.master_db.user])
            if result.returncode == 0:
                print("✅ PostgreSQL is ready!")
                return True
            print(f"Waiting for PostgreSQL to be ready... (Attempt {attempt+1}/{retries})")
            time.sleep(delay)
        
        print("⚠️  PostgreSQL is not ready after multiple attempts.")
        return False
    
    def ensure_postgres_is_ready(self):
        """Ensures Docker and PostgreSQL are ready to use."""
        self.start_container()

        if not self.is_postgres_ready():
            sys.exit(1)