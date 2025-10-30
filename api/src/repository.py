from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Tuple

from .db import db_pool


async def insert_raw(
    rows: Iterable[Tuple[datetime, str, str, float, int | None]]
) -> int:
    q = (
        "INSERT INTO swl.raw_measurements (time, source, parameter, value, quality)\n"
        "VALUES (%s, %s, %s, %s, %s)\n"
        "ON CONFLICT (time, source, parameter) DO UPDATE SET\n"
        "  value = EXCLUDED.value, quality = EXCLUDED.quality"
    )
    rows_list = list(rows)
    if not rows_list:
        return 0
    async with db_pool.transaction() as conn:
        await conn.executemany(q, rows_list)  # type: ignore[arg-type]
    return len(rows_list)


async def insert_min1(
    rows: Iterable[Tuple[datetime, str, str, float, int | None]]
) -> int:
    q = (
        "INSERT INTO swl.min1_measurements (time, source, parameter, value, quality)\n"
        "VALUES (%s, %s, %s, %s, %s)\n"
        "ON CONFLICT (time, source, parameter) DO UPDATE SET\n"
        "  value = EXCLUDED.value, quality = EXCLUDED.quality"
    )
    rows_list = list(rows)
    if not rows_list:
        return 0
    async with db_pool.transaction() as conn:
        await conn.executemany(q, rows_list)  # type: ignore[arg-type]
    return len(rows_list)


async def query_series(
    source: str,
    parameter: str,
    start: datetime,
    end: datetime,
    series: str,
) -> List[tuple]:
    table = "swl.raw_measurements" if series == "raw" else "swl.min1_measurements"
    q = (
        f"SELECT time, source, parameter, value, quality FROM {table}\n"
        "WHERE source = %s AND parameter = %s AND time >= %s AND time <= %s\n"
        "ORDER BY time ASC"
    )
    async with db_pool.transaction() as conn:
        cur = await conn.execute(q, (source, parameter, start, end))
        rows = await cur.fetchall()
    return rows


