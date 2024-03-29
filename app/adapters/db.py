from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


class SessionFactory:
    def __init__(self, dsn: str, echo: bool, expire_on_commit: bool = False):
        self.async_engine = create_async_engine(
            dsn,
            echo=echo
        )

        self.session_maker = async_sessionmaker(
            self.async_engine,
            expire_on_commit=expire_on_commit,
            class_=AsyncSession,
        )

    def __call__(self, **kwargs) -> AsyncSession:
        return self.session_maker(**kwargs)
