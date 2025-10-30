from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Tuple

import numpy as np


def align_to_minute(ts: datetime) -> datetime:
    return ts.replace(second=0, microsecond=0)


def generate_minute_grid(start: datetime, end: datetime) -> List[datetime]:
    start_aligned = align_to_minute(start)
    end_aligned = align_to_minute(end)
    if end_aligned < end:
        end_aligned = end_aligned + timedelta(minutes=1)
    steps = int((end_aligned - start_aligned).total_seconds() // 60) + 1
    return [start_aligned + timedelta(minutes=i) for i in range(steps)]


def linear_interpolate_to_minute(
    samples: Iterable[Tuple[datetime, float]],
    start: datetime,
    end: datetime,
) -> List[Tuple[datetime, float]]:
    pts = sorted(samples, key=lambda x: x[0])
    if not pts:
        return []
    grid = generate_minute_grid(start, end)

    xs = np.array([p[0].timestamp() for p in pts], dtype=float)
    ys = np.array([p[1] for p in pts], dtype=float)
    gx = np.array([g.timestamp() for g in grid], dtype=float)

    # Use numpy interp: values outside range get extrapolated with edge values
    gy = np.interp(gx, xs, ys)
    return list(zip(grid, gy.tolist()))


def is_regular_1min_series(samples: Iterable[Tuple[datetime, float]]) -> bool:
    pts = sorted(samples, key=lambda x: x[0])
    if len(pts) < 2:
        # 单点也视作对齐到分钟，便于直接写入 1min 表
        return pts[0][0].second == 0 and pts[0][0].microsecond == 0 if pts else False
    for i in range(len(pts)):
        t = pts[i][0]
        if not (t.second == 0 and t.microsecond == 0):
            return False
        if i > 0:
            dt = (t - pts[i - 1][0]).total_seconds()
            if dt % 60 != 0:
                return False
    return True


