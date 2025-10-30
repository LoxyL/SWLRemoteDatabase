-- Initialize TimescaleDB and schema for space weather large-volume time series

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Force UTC at the database level for consistent timestamp behavior
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_db_role_setting s
    JOIN pg_database d ON d.oid = s.setdatabase
    WHERE d.datname = current_database() AND s.setrole = 0 AND s.setconfig::text LIKE '%TimeZone%')
  THEN
    EXECUTE format('ALTER DATABASE %I SET TIMEZONE TO ''UTC''', current_database());
  END IF;
END$$;

CREATE SCHEMA IF NOT EXISTS swl;

-- Raw measurements: arbitrary cadence
CREATE TABLE IF NOT EXISTS swl.raw_measurements (
  time        TIMESTAMPTZ       NOT NULL,
  source      TEXT              NOT NULL,
  parameter   TEXT              NOT NULL,
  value       DOUBLE PRECISION  NOT NULL,
  quality     SMALLINT,
  inserted_at TIMESTAMPTZ       NOT NULL DEFAULT now(),
  CONSTRAINT raw_pk PRIMARY KEY (time, source, parameter)
);

-- Promote to hypertable with hash partitioning on source for better parallelism
SELECT create_hypertable(
  relation => 'swl.raw_measurements',
  time_column_name => 'time',
  partitioning_column => 'source',
  number_partitions => 8,
  chunk_time_interval => INTERVAL '7 days',
  if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS raw_spl_time_idx
  ON swl.raw_measurements (source, parameter, time DESC);

-- 1-minute interpolated measurements. Times are aligned to the minute
CREATE TABLE IF NOT EXISTS swl.min1_measurements (
  time        TIMESTAMPTZ       NOT NULL,
  source      TEXT              NOT NULL,
  parameter   TEXT              NOT NULL,
  value       DOUBLE PRECISION  NOT NULL,
  quality     SMALLINT,
  inserted_at TIMESTAMPTZ       NOT NULL DEFAULT now(),
  CONSTRAINT min1_time_on_minute CHECK (date_trunc('minute', time) = time),
  CONSTRAINT min1_pk PRIMARY KEY (time, source, parameter)
);

SELECT create_hypertable(
  relation => 'swl.min1_measurements',
  time_column_name => 'time',
  partitioning_column => 'source',
  number_partitions => 8,
  chunk_time_interval => INTERVAL '30 days',
  if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS min1_spl_time_idx
  ON swl.min1_measurements (source, parameter, time DESC);

-- Optional: enable compression to reduce storage; uncomment as needed
-- ALTER TABLE swl.raw_measurements SET (
--   timescaledb.compress,
--   timescaledb.compress_segmentby = 'source, parameter',
--   timescaledb.compress_orderby = 'time DESC'
-- );
-- SELECT add_compression_policy('swl.raw_measurements', INTERVAL '14 days');
-- ALTER TABLE swl.min1_measurements SET (
--   timescaledb.compress,
--   timescaledb.compress_segmentby = 'source, parameter',
--   timescaledb.compress_orderby = 'time DESC'
-- );
-- SELECT add_compression_policy('swl.min1_measurements', INTERVAL '90 days');


