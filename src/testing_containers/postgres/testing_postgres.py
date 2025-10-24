from testing_containers.models import ContainerOptions, DBConfig

from .postgres_docker_container import PostgresDockerContainer
from .postgres_manager import PostgresManager


class TestingPostgres:
    __test__ = False  # tell pytest this is not a test class
    postgres: PostgresManager
    _pg_container: PostgresDockerContainer | None

    def __init__(self, master_db: DBConfig | None = None, options: ContainerOptions | None = None):
        self.options = options or ContainerOptions()
        self._pg_container = None
        self._setup(master_db)

    def stop(self) -> None:
        self.postgres.destroy()
        if self._pg_container:
            self._pg_container.stop_container()

    def _setup(self, master_db: DBConfig | None = None) -> None:
        try:
            if master_db is None:
                raise ValueError("No masterdb provided")
            self.postgres = self._get_current_postgres(master_db)
        except ValueError:
            self._pg_container = self._create_postgres_container(self.options)
            self.postgres = PostgresManager(master_db=self._pg_container.master_db)
        self.postgres.setup_testdb()

    @staticmethod
    def _get_container_name(container_namespace: str | None) -> str:
        if container_namespace:
            return f"{container_namespace}-testing-postgres"
        return "testing-postgres"

    def _create_postgres_container(self, options: ContainerOptions) -> PostgresDockerContainer:
        pg_container = PostgresDockerContainer(
            options=ContainerOptions(
                image=options.image,
                namespace=options.namespace,
                name=options.name or self._get_container_name(self.options.namespace),
                should_stop=options.should_stop,
                remove_on_stop=options.remove_on_stop,
            )
        )
        pg_container.ensure_postgres_is_ready()

        return pg_container

    def _get_current_postgres(self, master_db: DBConfig) -> PostgresManager:
        postgres = PostgresManager(master_db=master_db)
        if postgres.is_postgres_ready():
            return postgres
        raise ValueError(f"Postgres not available master_db={master_db}")
