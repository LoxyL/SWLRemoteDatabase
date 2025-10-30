from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from typing import Iterator, List, Dict

from urllib import request, error


def parse_time_to_iso8601_utc(raw: str) -> str:
    """Parse timestamps like '2004-11-07 00:00:57.858999968' into ISO-8601 UTC.

    Python datetime only supports microseconds (6 digits). Truncate any extra
    fractional digits and convert to a timezone-aware UTC ISO string.
    """
    raw = raw.strip()
    if "." in raw:
        date_part, frac = raw.split(".", 1)
        # Keep only first 6 digits for microseconds; pad if too short
        micro = (frac.split()[0] + "000000")[:6]
        ts = f"{date_part}.{micro}"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
    else:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    dt = dt.replace(tzinfo=timezone.utc)
    iso = dt.isoformat()
    # Prefer 'Z' suffix for readability
    if iso.endswith("+00:00"):
        iso = iso[:-6] + "Z"
    return iso


def batched(iterable: Iterator[Dict], batch_size: int) -> Iterator[List[Dict]]:
    batch: List[Dict] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def health_check(api_base: str, timeout_s: int = 10) -> None:
    url = f"{api_base.rstrip('/')}/v1/health"
    try:
        with request.urlopen(url, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") != "ok":
            print(f"[WARN] Health check returned: {data}")
        else:
            print("[OK] API health check passed")
    except Exception as exc:
        print(f"[ERROR] API health check failed: {exc}")
        sys.exit(2)


def stream_csv_rows(csv_path: str, source: str, parameter: str) -> Iterator[Dict]:
    # Use 'utf-8-sig' to strip potential BOM (\ufeff) from the header
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "Time" not in reader.fieldnames or len(reader.fieldnames or []) < 2:
            raise RuntimeError(
                f"CSV header unexpected. Got fields: {reader.fieldnames}. Expected 'Time,<VALUE_COLUMN>'."
            )
        # Choose the first non-Time column as the value column
        value_column = next(col for col in reader.fieldnames if col != "Time")
        for row in reader:
            t_raw = row["Time"].strip()
            v_raw = row[value_column].strip()
            if not t_raw or v_raw == "":
                continue
            try:
                t_iso = parse_time_to_iso8601_utc(t_raw)
                value = float(v_raw)
            except Exception:
                # Skip unparsable rows silently to keep ingestion robust
                continue
            yield {
                "time": t_iso,
                "source": source,
                "parameter": parameter,
                "value": value,
            }


def post_batch(api_base: str, batch: List[Dict], timeout_s: int = 30) -> Dict:
    url = f"{api_base.rstrip('/')}/v1/ingest"
    payload = json.dumps(batch).encode("utf-8")
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CSV data into SWL API in batches.")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--api", default="http://localhost:8080", help="API base URL, e.g. http://localhost:8080")
    parser.add_argument("--source", default="ACE", help="Source name for this dataset")
    parser.add_argument("--parameter", default="BZ_GSE", help="Parameter name for this dataset")
    parser.add_argument("--batch-size", type=int, default=1000, help="Number of rows per POST")
    parser.add_argument("--sleep-ms", type=int, default=50, help="Sleep between batches to avoid bursts")
    parser.add_argument(
        "--max-batches", type=int, default=0, help="Stop after this many batches (0 = no limit)"
    )
    args = parser.parse_args()

    health_check(args.api)

    total_rows = 0
    total_raw_stored = 0
    total_min1_stored = 0
    start_time = time.time()

    try:
        for i, batch in enumerate(batched(stream_csv_rows(args.file, args.source, args.parameter), args.batch_size), start=1):
            try:
                result = post_batch(args.api, batch)
            except error.HTTPError as http_err:
                body = http_err.read().decode("utf-8", errors="ignore")
                print(f"[ERROR] HTTP {http_err.code} on batch {i}: {body}")
                sys.exit(3)
            except Exception as exc:
                print(f"[ERROR] Failed posting batch {i}: {exc}")
                sys.exit(3)

            total_rows += len(batch)
            total_raw_stored += int(result.get("stored_raw", 0))
            total_min1_stored += int(result.get("stored_min1", 0))

            if i % 10 == 0:
                elapsed = time.time() - start_time
                print(
                    f"[PROGRESS] batches={i}, rows_sent={total_rows}, raw={total_raw_stored}, min1={total_min1_stored}, elapsed={elapsed:.1f}s"
                )

            time.sleep(max(0, args.sleep_ms / 1000.0))

            if args.max_batches and i >= args.max_batches:
                print(f"[INFO] Reached max-batches={args.max_batches}, stopping early.")
                break

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")

    elapsed = time.time() - start_time
    print(
        f"[DONE] rows_sent={total_rows}, raw={total_raw_stored}, min1={total_min1_stored}, elapsed={elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()


