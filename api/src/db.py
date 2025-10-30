from contextlib import asynccontextmanager
from typing import AsyncIterator

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .config import settings


class DatabasePool:
    def __init__(self) -> None:
        self._pool: AsyncConnectionPool | None = None

    async def connect(self) -> None:
        if self._pool is None:
            # row_factory applies to each acquired connection via kwargs
            self._pool = AsyncConnectionPool(
                settings.dsn(), min_size=1, max_size=10, kwargs={"row_factory": dict_row}
            )
            await self._pool.open()

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def transaction(self):
        if self._pool is None:
            await self.connect()
        assert self._pool is not None
        async with self._pool.connection() as conn:
            async with conn.transaction():
                yield conn


db_pool = DatabasePool()


