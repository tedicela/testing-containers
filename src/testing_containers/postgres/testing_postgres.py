from typing import Optional
from testing_containers.models import ContainerOptions, DBConfig
from .postgres_manager import PostgresManager
from .postgres_docker_container import PostgresDockerContainer

class TestingPostgres:
    __test__ = False  # tell pytest this is not a test class
    postgres: PostgresManager
    _pg_container: Optional[PostgresDockerContainer]

    def __init__(
        self, 
        master_db: Optional[DBConfig] = None, 
        options: Optional[ContainerOptions] = None
    ):
        self.options = options or ContainerOptions()
        self._pg_container = None
        self._setup(master_db)


    def stop(self):
        self.postgres.destroy()
        if self._pg_container:
            self._pg_container.stop_container()

    def _setup(self, master_db: Optional[DBConfig] = None):
        try:
            if master_db is None:
                raise
            self.postgres = self._get_current_postgres(master_db)
        except:
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