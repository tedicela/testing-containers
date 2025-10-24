from pydantic import BaseModel


class DBConfig(BaseModel):
    host: str = "localhost"
    name: str
    user: str
    password: str
    port: int


class ContainerOptions(BaseModel):
    namespace: str | None = None
    name: str | None = None
    image: str | None = None
    should_stop: bool = False
    remove_on_stop: bool = False
