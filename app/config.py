import os
from functools import cache

import yaml
from pydantic import BaseSettings, Field


class Postgres(BaseSettings):
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
    secret: str | None = Field(env='SECRET')
    alg: str = Field(default="HS256", env='ALG')

    class Config:
        env_prefix = 'JWT_'


class Telegram(BaseSettings):
    token: str = Field(env='TOKEN')

    class Config:
        env_prefix = 'TELEGRAM_'


class App(BaseSettings):
    origins: list[str] = Field(default_factory=list)

    class Config:
        env_prefix = 'APP_'


class Settings(BaseSettings):
    postgres: Postgres = Field(default_factory=Postgres)
    jwt: JWT = Field(default_factory=JWT)
    telegram: Telegram = Field(default_factory=Telegram)
    app: App = Field(default_factory=App)


@cache
def Config() -> Settings:
    path_to_config = os.environ.get('CONFIG_PATH') or "config.yml"

    if not os.path.exists(path_to_config):
        return Settings()

    with open(path_to_config, "r") as f:
        raw_config = yaml.safe_load(f)

    return Settings(**raw_config)
