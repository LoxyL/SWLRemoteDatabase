from __future__ import annotations

import csv
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List

from .api import post_json


def parse_time_to_iso8601_utc(raw: str) -> str:
    raw = raw.strip()
    if "." in raw:
        date_part, frac = raw.split(".", 1)
        micro = (frac.split()[0] + "000000")[:6]
        ts = f"{date_part}.{micro}"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
    else:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    dt = dt.replace(tzinfo=timezone.utc)
    iso = dt.isoformat()
    if iso.endswith("+00:00"):
        iso = iso[:-6] + "Z"
    return iso


def batched(iterable: Iterator[Dict[str, Any]], batch_size: int) -> Iterator[List[Dict[str, Any]]]:
    batch: List[Dict[str, Any]] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def stream_csv_rows(csv_path: str, source: str, parameter: str) -> Iterator[Dict[str, Any]]:
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "Time" not in (reader.fieldnames or []) or len(reader.fieldnames or []) < 2:
            raise RuntimeError(f"CSV header unexpected. Got fields: {reader.fieldnames}")
        value_column = next(col for col in reader.fieldnames if col != "Time")
        for row in reader:
            t_raw = (row.get("Time") or "").strip()
            v_raw = (row.get(value_column) or "").strip()
            if not t_raw or v_raw == "":
                continue
            try:
                t_iso = parse_time_to_iso8601_utc(t_raw)
                value = float(v_raw)
            except Exception:
                continue
            yield {
                "time": t_iso,
                "source": source,
                "parameter": parameter,
                "value": value,
            }


def ingest_csv(
    api_base: str,
    csv_path: str,
    source: str,
    parameter: str,
    batch_size: int = 1000,
    sleep_ms: int = 50,
    max_batches: int = 0,
) -> Dict[str, int]:
    total_rows = 0
    total_raw = 0
    total_min1 = 0
    start_time = time.time()

    for i, batch in enumerate(batched(stream_csv_rows(csv_path, source, parameter), batch_size), start=1):
        result = post_json(api_base, "/v1/ingest", batch, timeout_s=60)
        total_rows += len(batch)
        total_raw += int(result.get("stored_raw", 0))
        total_min1 += int(result.get("stored_min1", 0))

        time.sleep(max(0, sleep_ms / 1000.0))
        if max_batches and i >= max_batches:
            break

    elapsed_s = time.time() - start_time
    return {"rows": total_rows, "raw": total_raw, "min1": total_min1, "elapsed_s": int(elapsed_s)}


