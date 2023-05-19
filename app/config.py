import os
from functools import cache
from typing import Any

import yaml
from pydantic import BaseSettings, Field


class Database(BaseSettings):
    user: str = Field(default='postgres', env='USER')
    password: str = Field(default='postgres', env='PASSWORD')
    database: str = Field(default='iss', env='DATABASE')
    host: str = Field(default='localhost', env='HOST')
    port: int = Field(default=5432, env='PORT')

    @property
    def dsn(self) -> str:
        return ''.join([
            f'postgresql+asyncpg://',
            f'{self.user}:{self.password}@',
            f'{self.host}:{self.port}/',
            f'{self.database}'
        ])

    class Config:
        env_prefix = 'POSTGRES_'


class JWT(BaseSettings):

    def __init__(self, **values: Any):
        super().__init__(**values)

    secret: str | None = Field(env='SECRET')
    alg: str = Field(default="HS256", env='ALG')

    class Config:
        env_prefix = 'ISS_'


class Config(BaseSettings):
    database: Database = Database()
    jwt: JWT = JWT()


@cache
def Configuration() -> Config:
    print(f"load configuration")
    path_to_config = os.environ.get('CONFIG_PATH') or "config.yml"
    if not os.path.exists(path_to_config):
        return Config()
    with open(path_to_config, "r") as f:
        raw_config = yaml.safe_load(f)

    print(raw_config)
    return Config(**raw_config)
