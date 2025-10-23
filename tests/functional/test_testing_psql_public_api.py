from testing_containers.postgres.postgres_docker_container import PostgresDockerContainer
from testing_containers.postgres.testing_postgres import TestingPostgres
from testing_containers.models import DBConfig, ContainerOptions


def test_testpsql_without_db_config():
    options = ContainerOptions(remove_on_stop=True, should_stop=True)
    testdb = TestingPostgres(options=options)

    assert testdb.postgres.master_db == DBConfig(
        host='localhost',
        name='postgres',
        user='postgres',
        password='password',
        port=5433
    )
    assert testdb.options.namespace == None
    assert isinstance(testdb._pg_container, PostgresDockerContainer)
    assert testdb._pg_container.container.image == "postgres:16.3"
    assert testdb.postgres.testdb == DBConfig(
        host='localhost',
        name='tmp_testdb',
        user='postgres',
        password='password',
        port=5433
    )
    testdb.stop()

def test_testpsql_with_db_config():
    # Let's run container to simulate Development DB
    devpostgres_container = PostgresDockerContainer(
        port=5444,
        options=ContainerOptions(name="dev-db", should_stop=True, remove_on_stop=True)
    )
    devpostgres_container.ensure_postgres_is_ready()

    dev_db_config = DBConfig(
        host="localhost",
        name=devpostgres_container.master_db.name,
        user=devpostgres_container.master_db.user,
        password=devpostgres_container.master_db.password,
        port=devpostgres_container.master_db.port
    )

    # It should NOT create/run another container instead should re-use the same container
    test_postgres = TestingPostgres(master_db=dev_db_config)
    
    assert test_postgres.postgres.testdb == DBConfig(
        host=dev_db_config.host,
        name="tmp_testdb",
        user=dev_db_config.user,
        password=dev_db_config.password,
        port=dev_db_config.port
    )
    assert test_postgres._pg_container is None
    devpostgres_container.stop_container()