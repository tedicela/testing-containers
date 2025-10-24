from .docker_container import DockerContainer
from .models import ContainerOptions, DBConfig
from .postgres.testing_postgres import TestingPostgres

"""
testing_services
~~~~~~~~~~~~~~~~

A unified testing utility for spinning up lightweight Docker-based
service containers (PostgreSQL, MariaDB, Redis, etc.) for integration tests.

Example usage:
    from testing_services import TestingPostgres

    test_db = TestingPostgres()
    config = test_db.db_config
    ...
    test_db.stop()

Subpackages:
    postgres    -- Postgres-specific manager and testing helpers
"""

__all__ = [
    "DockerContainer",
    "TestingPostgres",
    "DBConfig",
    "ContainerOptions",
]
