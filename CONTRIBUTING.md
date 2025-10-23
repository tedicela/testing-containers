
# 🤝 Contributing to testing-containers

First off — thank you for taking the time to contribute 💙  
`testing-containers` is a lightweight library that helps developers run ephemeral Docker containers (like Postgres, Redis, LocalStack, etc.) during testing.  
We welcome improvements, bug fixes, new service integrations, and documentation updates!

---

## 🧩 How to Contribute

### 1️⃣ Fork & Clone

```bash
git clone https://github.com/<your-username>/testing-containers.git
cd testing-containers
```

### 2️⃣ Create a Branch

Use a descriptive branch name:
```bash
git checkout -b feature/testing-redis
# or
git checkout -b fix/docker-timeout
```

### 3️⃣ Set Up the Development Environment

We use [Poetry](https://python-poetry.org/) and pre-commit.
```bash
poetry install
pre-commit install
```
This installs both runtime and development dependencies (pytest, pre-commit, mypy, etc.).


## 🧪 Running Tests

All tests must pass before merging.

```bash
poetry run pytest tests -q
```

To see coverage:
```bash
pytest --cov=testing_containers --cov-report=term-missing
```

Run linting and type checks:
```bash
pre-commit run --all-files
mypy testing_containers
```

## 🐳 Docker Requirements

> **⚠️ Important:** Some tests use Docker.
> Make sure Docker is installed and the daemon is running on your machine before running tests.

You can verify with
```bash
docker info
```
## 🧱 Code Style

We enforce consistent code style and quality using:
- Ruff → linting and formatting
- Mypy → static type checking
- Black-like formatting (via Ruff)
- Pre-commit hooks → automatic before each commit

Run manually:
```bash
pre-commit run --all-files
```

## 🧰 Adding a New Service (e.g. Redis, MariaDB, LocalStack)

To extend `testing-containers` with a new service:

1. Create a new subpackage:
```markdown
testing_containers/
    redis/
        __init__.py
        redis_docker_container.py
```
2. Implement a class following this pattern:
```python
from testing_containers import DockerContainer

class RedisDockerContainer:
    def __init__(self, port=6379, **kwargs):
        self.container = DockerContainer(
            container_name="testing-redis",
            image="redis:7",
            expose_ports=[f"{port}:6379"],
            should_stop=True,
            remove_container=True,
            **kwargs,
        )

    def ensure_ready(self):
        self.container.start_container()
        result = self.container.exec(["redis-cli", "ping"])
        if "PONG" not in result.stdout:
            raise RuntimeError("Redis not ready")
```

3. Add unit tests in `tests/unit/redis/test_redis_container.py` and functional tests under `tests/functional/`
4. Update the README.md with a short example.

## 🧩 Commit Messages

Keep commits small, clear, and focused.
Use the following format:
```scss
feat(redis): add support for redis
fix(docker): handle missing Docker daemon gracefully
docs(readme): update example for TestingPostgres
```

## 🔍 Pull Requests

Before submitting a PR:
- ✅ All tests pass
- ✅ Coverage is not decreased
- ✅ Linting and mypy checks pass
- ✅ Documentation and examples updated if needed

PRs that include new features should also include:
- Unit tests
- Short entry in CHANGELOG.md (if present)
- Example in the README (if user-facing)

## 🧠 Questions or Suggestions

If you have questions, ideas, or bug reports:

- Open a [GitHub Issue](../../issues)
- Propose design discussions via [Discussions](../../discussions)

## 🪪 License

By contributing to testing-containers, you agree that your contributions will be licensed under the same MIT License as the project.

✨ Thank you for helping make testing fast, clean, and reproducible!