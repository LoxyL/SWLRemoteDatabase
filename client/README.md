## SWL Remote DB - Python 客户端

轻量级 Python 客户端，遵循 `test/` 脚本的实现风格（内置 `urllib`，无需第三方 HTTP 库），用于：
- 健康检查
- 本地 CSV 批量写入远端 API
- 区间数据查询（raw/min1）
- raw vs min1 对比画图（需要 matplotlib）

### 目录结构

- `client/api.py`：API 基础封装（健康检查、POST JSON）
- `client/ingest.py`：CSV 流式读取、批量写入
- `client/query.py`：区间查询与时间格式处理
- `client/plot.py`：raw/min1 对比绘图
- `client/cli.py`：命令行工具（health/ingest/query/plot-compare）

### 运行环境

- Python 3.8+
- 可选依赖：`matplotlib`（仅画图需要）
- 不依赖 `requests` 等第三方库

安装画图依赖（可选）：

```bash
python -m pip install matplotlib
```

### 快速开始（命令行）

默认 API 地址为 `http://localhost:8080`，可通过 `--api` 指定你的服务器地址，例如 `http://114.66.61.12:8080`。

1) 健康检查

```bash
python -m client.cli --api http://114.66.61.12:8080 health
```

2) 批量写入（CSV 结构同 `test/data` 示例）

```bash
python -m client.cli --api http://114.66.61.12:8080 ingest \
  --file test/data/space_weather_cdaweb_AC_H0_MFI_20041107_BGSEc_2.csv \
  --source ACE \
  --parameter BZ_GSE \
  --batch-size 1000 \
  --sleep-ms 50
```

3) 区间查询（仅打印条数，或可选导出到文件）

```bash
python -m client.cli --api http://114.66.61.12:8080 query \
  --source ACE --parameter BZ_GSE \
  --start 2004-11-07T00:00:00Z --end 2004-11-07T02:00:00Z \
  --series raw

python -m client.cli --api http://114.66.61.12:8080 query \
  --source ACE --parameter BZ_GSE \
  --start 2004-11-07T00:00:00Z --end 2004-11-07T02:00:00Z \
  --series min1

# 导出为 JSON（根据扩展名自动识别，未提供扩展名默认 JSON）
python -m client.cli --api http://114.66.61.12:8080 query \
  --source ACE --parameter BZ_GSE \
  --start 2004-11-07T00:00:00Z --end 2004-11-07T02:00:00Z \
  --series raw --out query_raw.json

# 导出为 CSV（列：time,value,source,parameter）
python -m client.cli --api http://114.66.61.12:8080 query \
  --source ACE --parameter BZ_GSE \
  --start 2004-11-07T00:00:00Z --end 2004-11-07T02:00:00Z \
  --series min1 --out query_min1.csv
```

4) 画图（raw vs min1）

```bash
python -m client.cli --api http://114.66.61.12:8080 plot-compare \
  --source ACE --parameter BZ_GSE \
  --start 2004-11-07T00:00:00Z --end 2004-11-07T02:00:00Z \
  --out plot_compare_client.png
```

### CSV 数据格式要求

- 文件编码：`utf-8` 或 `utf-8-sig`（自动去除 BOM）
- 表头：必须含有 `Time` 列，以及至少一个数值列；客户端会选择第一列非 `Time` 的列作为数值列。
- 时间格式：
  - `YYYY-MM-DD HH:MM:SS` 或 `YYYY-MM-DD HH:MM:SS.xxxxxx`
  - 若存在超过 6 位的小数秒，会自动截断为微秒精度
  - 最终上送为 ISO-8601 UTC 字符串，形如 `2004-11-07T00:00:00Z`

示例（前两列）：

```csv
Time,Value
2004-11-07 00:00:00.123456,1.23
2004-11-07 00:00:57.858999968,1.24
```

### 命令行参数说明

- `health`
  - `--api`：API 基地址（默认 `http://localhost:8080`）

- `ingest`
  - `--file`：CSV 文件路径
  - `--source`：数据源标识（如 `ACE`）
  - `--parameter`：参数名（如 `BZ_GSE`）
  - `--batch-size`：每次 POST 的数据点数量（默认 1000）
  - `--sleep-ms`：批次之间等待毫秒数（默认 50）
  - `--max-batches`：最多发送的批次数（0 表示不限制）

- `query`
  - `--source`，`--parameter`
  - `--start`，`--end`：ISO8601（带 `Z` 或 `+00:00`）
  - `--series`：`raw` 或 `min1`
  - `--out`：可选，导出路径；支持 `.json` 或 `.csv`（未提供或无扩展名时默认保存 JSON；若不提供此参数，则不保存到本地）

- `plot-compare`
  - 与 `query` 相同的参数，另有：
  - `--out`：输出 PNG 路径（默认 `plot_compare.png`）
  - `--show`：是否显示窗口

### 作为库在代码中使用

```python
from client import health_check, ingest_csv, query_series, plot_compare

api = "http://114.66.61.12:8080"

# 健康检查
print(health_check(api))

# 批量写入（仅示例，参数请按需修改）
stats = ingest_csv(
    api_base=api,
    csv_path="test/data/space_weather_cdaweb_AC_H0_MFI_20041107_BGSEc_2.csv",
    source="ACE",
    parameter="BZ_GSE",
    batch_size=1000,
    sleep_ms=50,
)
print(stats)

# 查询（返回 [(datetime, float), ...]）
pts_raw = query_series(api, "ACE", "BZ_GSE", "2004-11-07T00:00:00Z", "2004-11-07T02:00:00Z", "raw")
pts_m1  = query_series(api, "ACE", "BZ_GSE", "2004-11-07T00:00:00Z", "2004-11-07T02:00:00Z", "min1")
print(len(pts_raw), len(pts_m1))

# 画图（需要 matplotlib）
plot_compare(api, "ACE", "BZ_GSE", "2004-11-07T00:00:00Z", "2004-11-07T02:00:00Z", out_path="plot_compare_client.png")
```

### 与服务端行为的对应关系

- 写入接口 `/v1/ingest`：
  - 需要同一批次内的 `source`/`parameter` 一致
  - 服务端会对 `raw` 与 `min1` 表做 upsert（相同主键会更新值）
  - 若来的是非严格 1 分钟点，服务端会对 `min1` 进行线性插值

- 查询接口 `/v1/query`：
  - `end` 必须大于 `start`
  - `series` 默认为 `raw`，可选 `min1`

### 性能与可靠性建议

- 增大 `--batch-size` 可提升吞吐；必要时适度调高 `--sleep-ms` 限制瞬时峰值
- 从小文件开始验证；随后再进行全量导入
- 一旦返回 400/500，请检查 CSV 格式（时间列与数值列）、时区、参数名等

### Windows 使用提示

- 直接使用 `python -m client.cli ...` 即可
- 中文终端如出现编码问题，可尝试 `chcp 65001`

### 常见问题

1) 健康检查失败 / 连接被拒绝
   - 确认容器正常运行、API 端口已对外映射（默认 8080）

2) 写入返回 400（批次不合法）
   - 同一批次内必须保证 `source` 与 `parameter` 一致

3) 查询返回为空
   - 检查时间范围与 `source`/`parameter` 是否匹配已写入的数据


