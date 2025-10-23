from typing import Optional
from pydantic import BaseModel


class DBConfig(BaseModel):
    host: str = "localhost"
    name: str
    user: str
    password: str
    port: int

class ContainerOptions(BaseModel):
    namespace: Optional[str] = None
    name: Optional[str] = None
    image: Optional[str] = None
    should_stop: bool = False
    remove_on_stop: bool = False