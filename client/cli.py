from __future__ import annotations

import argparse
import json
import sys

from .api import health_check
from .ingest import ingest_csv
from .query import query_series, save_points
from .plot import plot_compare


def main() -> None:
    parser = argparse.ArgumentParser(description="SWL Remote DB Client")
    parser.add_argument("--api", default="http://localhost:8080", help="API base URL, e.g. http://localhost:8080")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_health = sub.add_parser("health", help="Check API health")

    p_ingest = sub.add_parser("ingest", help="Ingest CSV in batches")
    p_ingest.add_argument("--file", required=True, help="Path to CSV file")
    p_ingest.add_argument("--source", required=True, help="Source name")
    p_ingest.add_argument("--parameter", required=True, help="Parameter name")
    p_ingest.add_argument("--batch-size", type=int, default=1000)
    p_ingest.add_argument("--sleep-ms", type=int, default=50)
    p_ingest.add_argument("--max-batches", type=int, default=0)

    p_query = sub.add_parser("query", help="Query time range and print count (optional export)")
    p_query.add_argument("--source", required=True)
    p_query.add_argument("--parameter", required=True)
    p_query.add_argument("--start", required=True, help="ISO8601, e.g. 2004-11-07T00:00:00Z")
    p_query.add_argument("--end", required=True, help="ISO8601, e.g. 2004-11-07T02:00:00Z")
    p_query.add_argument("--series", default="raw", choices=["raw", "min1"])
    p_query.add_argument("--out", help="Optional export path (.json or .csv). If omitted, not saved.")

    p_plot = sub.add_parser("plot-compare", help="Plot raw vs min1 and save PNG")
    p_plot.add_argument("--source", required=True)
    p_plot.add_argument("--parameter", required=True)
    p_plot.add_argument("--start", required=True)
    p_plot.add_argument("--end", required=True)
    p_plot.add_argument("--out", default="plot_compare.png")
    p_plot.add_argument("--show", action="store_true")

    args = parser.parse_args()

    if args.cmd == "health":
        data = health_check(args.api)
        print(json.dumps(data, ensure_ascii=False))
        return

    if args.cmd == "ingest":
        result = ingest_csv(
            api_base=args.api,
            csv_path=args.file,
            source=args.source,
            parameter=args.parameter,
            batch_size=args.batch_size,
            sleep_ms=args.sleep_ms,
            max_batches=args.max_batches,
        )
        print(json.dumps(result, ensure_ascii=False))
        return

    if args.cmd == "query":
        pts = query_series(args.api, args.source, args.parameter, args.start, args.end, args.series)
        print(len(pts))
        if getattr(args, "out", None):
            out_path = save_points(args.out, pts, args.source, args.parameter)
            print(f"[OK] 导出: {out_path}")
        return

    if args.cmd == "plot-compare":
        out = plot_compare(args.api, args.source, args.parameter, args.start, args.end, args.out, args.show)
        if out:
            print(f"[OK] 图已保存: {out}")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
        sys.exit(130)


