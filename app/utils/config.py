import os
from functools import cache

import yaml
from pydantic import BaseSettings, Field


class Postgres(BaseSettings):
    user: str
    password: str
    database: str
    host: str
    port: int

    @property
    def dsn(self) -> str:
        return ''.join([
            f'postgresql+asyncpg://',
            f'{self.user}:{self.password}@',
            f'{self.host}:{self.port}/',
            f'{self.database}'
        ])



class JWT(BaseSettings):
    secret: str
    alg: str


class Telegram(BaseSettings):
    token: str


class App(BaseSettings):
    port: int
    host: str
    origins: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    postgres: Postgres
    jwt: JWT
    telegram: Telegram
    app: App


@cache
def Config() -> Settings:
    path_to_config = os.environ.get('CONFIG_PATH') or "config.yml"

    if not os.path.exists(path_to_config):
        return Settings()

    with open(path_to_config, "r") as f:
        raw_config = yaml.safe_load(f)

    return Settings(**raw_config)
