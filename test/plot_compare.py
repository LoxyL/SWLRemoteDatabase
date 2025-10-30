from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import List, Tuple

from urllib import request


def parse_iso8601_z(ts: str) -> datetime:
    # Accept ...Z or with offset
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def to_iso8601_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    iso = dt.isoformat()
    return iso.replace("+00:00", "Z")


def fetch_series(
    api_base: str,
    source: str,
    parameter: str,
    start_iso: str,
    end_iso: str,
    series: str,
) -> List[Tuple[datetime, float]]:
    url = f"{api_base.rstrip('/')}/v1/query"
    payload = json.dumps(
        {
            "source": source,
            "parameter": parameter,
            "start": start_iso,
            "end": end_iso,
            "series": series,
        }
    ).encode("utf-8")
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    points: List[Tuple[datetime, float]] = []
    for item in data:
        t = parse_iso8601_z(item["time"])  # FastAPI returns ISO strings
        v = float(item["value"])
        points.append((t, v))
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch raw & min1 from API and plot comparison")
    parser.add_argument("--api", default="http://localhost:8080", help="API base URL")
    parser.add_argument("--source", default="ACE", help="Source name")
    parser.add_argument("--parameter", default="BZ_GSE", help="Parameter name")
    parser.add_argument("--start", default="2004-11-07T00:00:00Z", help="Start ISO8601 (e.g. 2004-11-07T00:00:00Z)")
    parser.add_argument("--end", default="2004-11-07T02:00:00Z", help="End ISO8601 (e.g. 2004-11-07T02:00:00Z)")
    parser.add_argument("--out", default="plot_compare.png", help="Output PNG file path")
    parser.add_argument("--show", action="store_true", help="Show window in addition to saving PNG")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except Exception:
        print("[ERROR] 未安装 matplotlib。请先执行: python -m pip install matplotlib")
        sys.exit(2)

    raw_pts = fetch_series(args.api, args.source, args.parameter, args.start, args.end, "raw")
    min1_pts = fetch_series(args.api, args.source, args.parameter, args.start, args.end, "min1")

    if not raw_pts and not min1_pts:
        print("[WARN] 在给定的时间范围内没有数据。")
        return

    fig, ax = plt.subplots(figsize=(12, 5))

    if raw_pts:
        tx, vy = zip(*raw_pts)
        ax.plot(tx, vy, label="raw", color="#1f77b4", linewidth=0.8, alpha=0.8)

    if min1_pts:
        tx2, vy2 = zip(*min1_pts)
        ax.plot(tx2, vy2, label="min1", color="#d62728", linewidth=1.6)

    ax.set_title(f"{args.source} {args.parameter} (raw vs min1)")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel(args.parameter)
    ax.set_xlim(tx[0], tx[-1])
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.5)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M", tz=timezone.utc))
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(args.out, dpi=150)
    print(f"[OK] 图已保存: {args.out}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()


