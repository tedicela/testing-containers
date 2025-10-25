# 🧪 testing-containers

[![PyPI](https://img.shields.io/pypi/v/testing-containers.svg)](https://pypi.org/project/testing-containers/)
[![CI](https://github.com/tedicela/testing-containers/actions/workflows/ci.yml/badge.svg)](https://github.com/tedicela/testing-containers/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Lightweight Python utilities for running ephemeral Docker containers in tests.**
> Includes `TestingPostgres` for disposable PostgreSQL test databases and `DockerContainer` for ad-hoc containers.

---

## 🚀 Overview

`testing-containers` helps you run **real services inside Docker** for integration or functional tests — without ever needing to manually start external databases, message brokers or anything else.

It provides:

- **`TestingPostgres`** — a PostgreSQL-specific helper that automatically creates a **fresh empty test database** before tests start and tears it down afterwards.
- **`DockerContainer`** — a generic helper to start, stop, and execute commands inside *any* Docker container (Postgres, Redis, LocalStack, etc.).

The goal is simple:
> Make your tests fully isolated, reproducible, and environment-agnostic — no shared state, no external dependencies.

---

## 🧭 Design Principles

- 🧩 **No external services** need to be manually started
- 🔁 **Fresh empty databases** are created every test run
- 🧹 **Automatic cleanup** when tests finish
- 🧱 **No pollution of your dev DB** — tests never touch your development data
- ⚙️ **Consistent environments** — use the same database version as production via Docker
- 🧰 **Generic & extensible** — same approach works for PostgreSQL, Redis, LocalStack, RabbitMQ, etc.
- 🐳 **Only dependency:** Docker (required only when containers are used)

---

## ⚙️ Installation

```bash
pip install testing-containers
```

> Requires Docker installed and running if you plan to spin up containerized services.

## 💡 Usage

### `TestingPostgres`

You can use `TestingPostgres` in two ways

**a) Run Postgres inside Docker**

```python
import psycopg
from testing_containers import TestingPostgres, ContainerOptions

pg = TestingPostgres(
    options=ContainerOptions(
        namespace="myproject-name" # optional – you can add a namespace to the container
        name="testdb" # optional – you can give a name to the container
        image="postgres:15.6" # optional / default postgres:16.3
        # The following options defines what should happen on stop()
        # container will stop or not
        # container will be removed or not
        # (you can decide on the speed you want on test startup and teardown)
        should_stop=True # optional / default=False
        remove_on_stop=True # optional / default=False
    )
)  # spins up a postgres:16.3 container
testdb = pg.postgres.testdb  # connection info for your test DB

# Connect and run migrations or tests
conn = psycopg.connect(
    dbname=testdb.name,
    user=testdb.user,
    password=testdb.password,
    host=testdb.host,
    port=testdb.port,
)
print("Connected:", conn)

# After tests
pg.stop()
```

**b) Connect to an existing Postgres instance**

> ❗ **Important:** In case the provided database is not available/ready it will spin a postgres container and use that as a fallback

```python
from testing_containers import TestingPostgres, DBConfig

dev_db_config = DBConfig(
    host="localhost",
    name="dev_db",
    user="postgres",
    password="secret",
    port=5432,
)
pg = TestingPostgres(db_config=dev_db_config)
print(pg.testdb)  # e.g. "test_dev_db" — a fresh copy created on the fly
# ... run tests ...
pg.stop()  # drops the test DB
```

✅ Each run creates a temporary database (test_<original_dbname>) and destroys it afterwards.

#### Example: using pytests, alembic and settings on conftest

- You run `TestingPostgres`
- You mock DB environment variables to the one of `TestingPostgres().postgres.test_db`
- So your app during tests runtime will be connected to **testdb**
- Create a pytest fixture which run alembic migration on start and stops testdb(drops testdb) on teardown

```python
import os
import pytest
from unittest.mock import patch
from alembic import command
from alembic.config import Config
from testing_containers import TestingPostgres

testing = TestingPostgres()
testdb = testing.postgres.test_db

env_vars = {
    "DB__USER": testdb.db.user,
    "DB__PASSWORD": testdb.db.password,
    "DB__HOST": testdb.db.host,
    "DB__PORT": str(testdb.db.port),
    "DB__NAME": testdb.db.name,
}
with patch.dict(os.environ, env_vars):
    from app.settings import settings


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Setup and teardown for the test database"""
    # Run Alembic migrations
    alembic_cfg = Config("alembic.ini")  # Ensure the path to alembic.ini is correct
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception:
        raise

    yield  # Run tests

    # Cleanup: Stop and remove the test DB
    testdb.stop()
```


### Generic DockerContainer
Start any service container on demand — e.g. Redis:

```python
from testing_containers import DockerContainer

redis = DockerContainer(
    container_name="test-redis",
    image="redis:7",
    expose_ports=["6379:6379"]
)

redis.start_container()
result = redis.exec(["redis-cli", "ping"])
print(result.stdout.strip())  # → PONG
redis.stop_container()
redis.remove_container()
```

✅ Great for spinning up ad-hoc containers for any dependency during tests.

## 🧠 Why use this

| Problem | Solution |
|----------|-----------|
| 🧩 **Tests depend on manually started external services** | `TestingPostgres` and `DockerContainer` spin up Docker containers automatically for your tests. |
| 🧹 **Test data pollutes your development database** | Each test run uses a **fresh, isolated test database**, which is dropped when tests finish. |
| ⚙️ **Local database version differs from production** | Run your tests inside Docker using the **same version** as production (e.g. `postgres:16.3`). |
| 🧱 **CI/CD pipelines need reproducible environments** | Works seamlessly in CI — no extra setup; containers are created and torn down automatically. |
| 🚀 **You need Redis, LocalStack, or any other service** | `DockerContainer` can run **any Docker image**, not just databases. |
| 🧪 **You want clean, reliable integration tests** | Ensures tests always start from a **known empty state** — no shared data, no side effects. |


## 🧪 Requirements
- Python 3.10+
- Docker (required only for containerized tests)

## 💡 Inspiration

This project was inspired by [`testing.postgresql`](https://pypi.org/project/testing.postgresql/) package,
which provides temporary PostgreSQL instances for testing.

However, `testing.postgresql` requires **PostgreSQL to be installed locally** on the developer’s machine.
That can lead to common issues in real-world teams:

- Developers might have **different PostgreSQL versions** installed.
- Local PostgreSQL configuration may **differ from the production environment**.
- Installing or managing Postgres locally can be **slow or error-prone in CI and requires additional setup**

`testing-containers` solves these problems by leveraging **Docker**:
- No local Postgres installation required.
- The same Postgres (or Redis, MariaDB, etc.) **version used in production** can be pulled and run in tests.
- Works identically on **any environment** — macOS, Linux, Windows, or CI/CD runners.

In short, it keeps the convenience of `testing.postgresql` while ensuring **environment parity and zero setup**.


## 🧾 License

MIT © Tedi Cela
