from __future__ import annotations

import sys
from typing import Optional

from .query import query_series


def plot_compare(
    api_base: str,
    source: str,
    parameter: str,
    start_iso: str,
    end_iso: str,
    out_path: str = "plot_compare.png",
    show: bool = False,
) -> Optional[str]:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import timezone
    except Exception:
        print("[ERROR] 未安装 matplotlib。请先执行: python -m pip install matplotlib", file=sys.stderr)
        return None

    raw_pts = query_series(api_base, source, parameter, start_iso, end_iso, "raw")
    min1_pts = query_series(api_base, source, parameter, start_iso, end_iso, "min1")

    if not raw_pts and not min1_pts:
        print("[WARN] 在给定的时间范围内没有数据。")
        return None

    fig, ax = plt.subplots(figsize=(12, 5))

    if raw_pts:
        tx, vy = zip(*raw_pts)
        ax.plot(tx, vy, label="raw", color="#1f77b4", linewidth=0.8, alpha=0.8)

    if min1_pts:
        tx2, vy2 = zip(*min1_pts)
        ax.plot(tx2, vy2, label="min1", color="#d62728", linewidth=1.6)

    ax.set_title(f"{source} {parameter} (raw vs min1)")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel(parameter)
    if raw_pts:
        ax.set_xlim(tx[0], tx[-1])
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.5)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M", tz=timezone.utc))
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(out_path, dpi=150)
    if show:
        plt.show()
    return out_path


