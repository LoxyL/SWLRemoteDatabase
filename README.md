## SWL Remote Database

A space-weather time-series database built on TimescaleDB with a FastAPI service.

- High-throughput writes and queries (raw table + 1-minute table, partitioned by `source`)
- Batch ingestion: one batch per `source`/`parameter`
- Automatic 1-minute series generation (or direct insert if already 1-minute regular)
- Query by `source`/`parameter`/time range for either raw or 1-minute series

### Quick Start

1) Optional: create a `.env` file (same directory as `docker-compose.yml`)

```
POSTGRES_DB=swldb
POSTGRES_USER=swluser
POSTGRES_PASSWORD=swlpass
DB_SSLMODE=disable
API_PORT=8080
```

2) Start services

```
docker compose up -d --build
```

Default ports: database `5432`, API `8080`.

### Environment Variables

| Name | Default | Description |
| --- | --- | --- |
| `POSTGRES_DB` | `swldb` | Database name created in TimescaleDB. |
| `POSTGRES_USER` | `swluser` | Database user. |
| `POSTGRES_PASSWORD` | `swlpass` | Database password. |
| `DB_SSLMODE` | `disable` | Postgres SSL mode (`disable`, `require`, etc.). |
| `API_PORT` | `8080` | API listening port exposed by the container. |
| `DB_HOST` | `db` (in container) / `localhost` (outside) | Postgres host used by the API service. |
| `DB_PORT` | `5432` | Postgres port used by the API service. |

### API Overview

| Endpoint | Method | Purpose | Request | Response |
| --- | --- | --- | --- | --- |
| `/v1/health` | GET | Health check | – | `{ "status": "ok" }` |
| `/v1/ingest` | POST | Batch ingest points of the same `source` and `parameter` | Body: array of `MeasurementIn` | `IngestResponse` |
| `/v1/query` | POST | Query a time range from raw or min1 series | Body: `QueryRequest` | Array of `MeasurementOut` |

#### Data Models

`MeasurementIn`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `time` | ISO-8601 string (UTC) | Yes | Timestamp of the sample. Any sub-second precision is accepted. |
| `source` | string | Yes | Data source identifier. |
| `parameter` | string | Yes | Parameter name. |
| `value` | number | Yes | Numeric value. |
| `quality` | integer | No | Optional quality flag. |

`IngestResponse`

| Field | Type | Description |
| --- | --- | --- |
| `stored_raw` | integer | Number of rows written to `raw` (insert + update). |
| `stored_min1` | integer | Number of rows written to `min1` (insert + update). |

`QueryRequest`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `source` | string | Yes | Data source to query. |
| `parameter` | string | Yes | Parameter to query. |
| `start` | ISO-8601 string (UTC) | Yes | Start time inclusive. |
| `end` | ISO-8601 string (UTC) | Yes | End time inclusive; must be greater than `start`. |
| `series` | enum(`raw`, `min1`) | No (default `raw`) | Select raw series or 1-minute series. |

`MeasurementOut`

| Field | Type | Description |
| --- | --- | --- |
| `time` | ISO-8601 string (UTC) | Sample timestamp. |
| `source` | string | Source identifier. |
| `parameter` | string | Parameter name. |
| `value` | number | Value. |
| `quality` | integer/null | Quality flag if present. |

### Interpolation Policy (min1)

- If the incoming batch is already a regular 1-minute series (points on exact minutes and spaced by 60s), it is copied as-is to the `min1` table.
- Otherwise, the API builds a minute-aligned grid covering `[start, end]` and computes linear interpolation using the raw samples; values outside the sample range are clamped to edge values.
- Both `raw` and `min1` use upsert semantics on the primary key `(time, source, parameter)`: inserting the same key updates `value`/`quality` instead of creating duplicates.

### Examples

Health check

```bash
curl http://localhost:8080/v1/health
```

Batch ingest (body is an array of `MeasurementIn` with the same `source` and `parameter`)

```bash
curl -X POST http://localhost:8080/v1/ingest \
  -H "Content-Type: application/json" \
  --data-binary @ingest.json
```

Query 1-minute series

```bash
curl -X POST http://localhost:8080/v1/query \
  -H "Content-Type: application/json" \
  --data-binary @query.json
```

### Database Schema (TimescaleDB)

- Schema `swl`
- `raw_measurements(time timestamptz, source text, parameter text, value double precision, quality smallint, inserted_at timestamptz default now(), primary key(time, source, parameter))`
- `min1_measurements(...)` same columns, with a constraint that `time` is aligned to the minute; both are hypertables partitioned by `source`.

### Service & Ports

- Database port: `5432` (native PostgreSQL/TimescaleDB). Use with `psql`, DBeaver, etc.
- API port: `8080` (HTTP/JSON). Interactive docs at `http://localhost:8080/docs`.

