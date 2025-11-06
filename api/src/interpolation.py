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
    """线性插值到分钟网格。

    - 忽略输入中的非有限值（NaN/Inf）。
    - 使用 numpy.interp 在区间内线性插值；区间外用边界值外推。
    - 若可用样本点 < 2，返回空列表（由调用方决定如何处理）。
    """
    pts = sorted(samples, key=lambda x: x[0])
    if not pts:
        return []

    # 仅保留有限数值样本
    xs_all = np.array([p[0].timestamp() for p in pts], dtype=float)
    ys_all = np.array([p[1] for p in pts], dtype=float)
    mask = np.isfinite(ys_all)
    xs = xs_all[mask]
    ys = ys_all[mask]

    if xs.size < 2:
        # 少于2个有效点，不足以进行线性插值
        return []

    grid = generate_minute_grid(start, end)
    gx = np.array([g.timestamp() for g in grid], dtype=float)

    # 使用边界值外推，确保输出无 NaN
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


