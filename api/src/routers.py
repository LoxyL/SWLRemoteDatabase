from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from .models import (
    IngestResponse,
    MeasurementIn,
    MeasurementOut,
    QueryRequest,
)
from .interpolation import is_regular_1min_series, linear_interpolate_to_minute
from .repository import insert_min1, insert_raw, query_series


router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(measurements: List[MeasurementIn]) -> IngestResponse:
    if not measurements:
        return IngestResponse(stored_raw=0, stored_min1=0)

    # Validate single source/parameter batch to simplify pipeline
    src = {m.source for m in measurements}
    prm = {m.parameter for m in measurements}
    if len(src) != 1 or len(prm) != 1:
        raise HTTPException(status_code=400, detail="每次上传应为同一 source 与 parameter 的批次")

    source = next(iter(src))
    parameter = next(iter(prm))

    tuples = [(m.time, m.source, m.parameter, m.value, m.quality) for m in measurements]
    stored_raw = await insert_raw(tuples)

    # 生成/复制 1 分钟序列
    times = [m.time for m in measurements]
    start, end = min(times), max(times)
    pts = [(m.time, m.value) for m in measurements]
    if is_regular_1min_series(pts):
        tuples_min1 = [(t, source, parameter, v, None) for t, v in pts]
    else:
        interp = linear_interpolate_to_minute(pts, start, end)
        tuples_min1 = [(t, source, parameter, v, None) for t, v in interp]
    stored_min1 = await insert_min1(tuples_min1)

    return IngestResponse(stored_raw=stored_raw, stored_min1=stored_min1)


@router.post("/query", response_model=List[MeasurementOut])
async def query(req: QueryRequest) -> List[MeasurementOut]:
    if req.end <= req.start:
        raise HTTPException(status_code=400, detail="end 必须大于 start")
    rows = await query_series(req.source, req.parameter, req.start, req.end, req.series)
    return [
        MeasurementOut(
            time=r["time"],
            source=r["source"],
            parameter=r["parameter"],
            value=r["value"],
            quality=r.get("quality"),
        )
        for r in rows
    ]


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


