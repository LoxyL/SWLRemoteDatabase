## SWL Remote Database

基于 TimescaleDB 的空间天气时序数据库与 FastAPI 服务，支持：

- 高吞吐写入与查询（原始表 + 1 分钟表，按 source 分区）
- 批量上传：同一 source/parameter 的一批点
- 自动生成 1 分钟序列（如果已为 1 分钟则直接落库）
- 按 source/parameter/时间段查询原始或 1 分钟序列

### 运行

1. 可选：创建环境变量文件 `.env`（与 `docker-compose.yml` 同级）：

```
POSTGRES_DB=swldb
POSTGRES_USER=swluser
POSTGRES_PASSWORD=swlpass
DB_SSLMODE=disable
API_PORT=8080
```

2. 启动服务：

```
docker compose up -d --build
```

数据库端口默认 `5432`，API 端口默认 `8080`。

### API

- 健康检查：`GET /v1/health`
- 批量写入：`POST /v1/ingest`

  请求体（同一 source/parameter 批量）：

  ```json
  [
    {"time":"2025-01-01T00:00:00Z","source":"ACE","parameter":"Bz","value":-3.2},
    {"time":"2025-01-01T00:00:30Z","source":"ACE","parameter":"Bz","value":-2.8}
  ]
  ```

  返回：`{ "stored_raw": N, "stored_min1": M }`

- 查询：`POST /v1/query`

  ```json
  {
    "source":"ACE",
    "parameter":"Bz",
    "start":"2025-01-01T00:00:00Z",
    "end":"2025-01-01T01:00:00Z",
    "series":"min1"  // raw 或 min1
  }
  ```

### 设计要点

- TimescaleDB hypertable：时间 + `source` 哈希分区，便于并行写入与查询
- 原始表 `swl.raw_measurements`：任意采样间隔
- 1 分钟表 `swl.min1_measurements`：对齐到分钟，便于统一分析
- Upsert 主键 `(time, source, parameter)`，避免重复
- 可按需开启 Timescale 压缩与保留策略（见 `sql/init.sql` 注释）


