from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import os
import csv
import json

from urllib import request

from .api import post_json


def parse_iso8601_z(ts: str) -> datetime:
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def to_iso8601_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    iso = dt.isoformat()
    return iso.replace("+00:00", "Z")


def query_series(
    api_base: str,
    source: str,
    parameter: str,
    start_iso: str,
    end_iso: str,
    series: str = "raw",
) -> List[Tuple[datetime, float]]:
    payload: Dict[str, Any] = {
        "source": source,
        "parameter": parameter,
        "start": start_iso,
        "end": end_iso,
        "series": series,
    }
    data = post_json(api_base, "/v1/query", payload, timeout_s=60)
    points: List[Tuple[datetime, float]] = []
    for item in data:
        t = parse_iso8601_z(item["time"])  # API returns ISO strings
        v = float(item["value"])
        points.append((t, v))
    return points


def save_points(out_path: str, points: List[Tuple[datetime, float]], source: str, parameter: str) -> str:
    ext = os.path.splitext(out_path)[1].lower()
    if ext in (".json", ""):
        arr: List[Dict[str, Any]] = [
            {"time": to_iso8601_z(t), "value": v, "source": source, "parameter": parameter}
            for t, v in points
        ]
        with open(out_path if ext else out_path + ".json", "w", encoding="utf-8") as f:
            json.dump(arr, f, ensure_ascii=False)
        return out_path if ext else out_path + ".json"
    elif ext == ".csv":
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "value", "source", "parameter"])
            for t, v in points:
                writer.writerow([to_iso8601_z(t), v, source, parameter])
        return out_path
    else:
        # 未知扩展名，按 JSON 处理
        arr = [
            {"time": to_iso8601_z(t), "value": v, "source": source, "parameter": parameter}
            for t, v in points
        ]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(arr, f, ensure_ascii=False)
        return out_path


