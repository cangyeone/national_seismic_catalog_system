# National Seismic Catalog System

全国地震编目系统（National Seismic Catalog System，NSCS）是一个以 **Kafka + Flink/Spark + 对象存储 + 列式数据库** 为核心的数据密集型平台，用于高并发接入地震波形、执行实时震相拾取与事件关联、完成精细定位与震级估计，并将编目结果对外提供 API 与可视化服务。后端 Web 服务仅作为薄层入口，实现鉴权、配置管理与查询接口，所有计算任务均在流式处理引擎中执行，以保证高吞吐、低延迟与弹性伸缩能力。

## 目录

1. [系统亮点](#系统亮点)
2. [整体架构](#整体架构)
3. [数据流程](#数据流程)
4. [核心功能模块](#核心功能模块)
5. [API 概览](#api-概览)
6. [开发环境与部署步骤](#开发环境与部署步骤)
7. [配置说明](#配置说明)
8. [流式作业参考实现](#流式作业参考实现)
9. [数据存储与治理](#数据存储与治理)
10. [可观测性与容错策略](#可观测性与容错策略)
11. [项目结构](#项目结构)
12. [后续规划](#后续规划)
13. [贡献指南](#贡献指南)
14. [联系方式](#联系方式)
15. [许可证](#许可证)

## 系统亮点

- **流式优先**：所有实时计算均通过 Kafka + Flink/Spark 流处理完成，FastAPI 仅负责 API 接入层，便于独立扩缩容。
- **完整编目链路**：涵盖波形入库、智能震相拾取、REAL 事件关联、PINNLocation 精定位、震级/震源机制计算等步骤。
- **存算分离**：波形数据冷存储于对象存储（S3/OSS/OBS），编目结果写入列式数据库（ClickHouse/Hologres 等），兼容多种云平台。
- **鲁棒性设计**：通过幂等入库、重试/死信队列、指标监控与链路追踪保证实时作业稳定。
- **可视化友好**：Web API 对外提供事件查询与台站管理，便于构建大屏展示或第三方接入。

## 整体架构

```
波形采集 → Kafka (waveforms.raw) → Flink/Spark Phase Picking → Kafka (waveforms.phase_picks)
             ↓                                                              ↓
        对象存储 (MiniSEED)                                       Flink/Spark Association → Kafka (waveforms.associations)
                                                                                                  ↓
                                                                                       PINNLocation & Magnitude Jobs
                                                                                                  ↓
                                                                                         列式库 / 分析服务
                                                                                                  ↓
                                                                                           Web API & 可视化
```

**关键子系统说明**：

- **Ingest Gateway（FastAPI）**：接收波形/台站/事件请求，进行基础校验，将波形转存 MiniSEED 并推送至 Kafka。
- **Streaming Jobs**：在 Flink 或 Spark Streaming 中执行震相拾取（深度学习）、REAL 事件关联、PINNLocation 定位、震级与震源机制求解。
- **Object Storage**：存储原始与衍生波形文件，支持版本化与冷热分层。
- **Columnar Store**：保存最终编目结果（事件、震相、震级等），对外提供高并发查询能力。
- **Observability Stack**：Prometheus + Alertmanager + Grafana + OpenTelemetry，用于指标、告警与链路追踪。

## 数据流程

1. **波形采集**：台站通过边缘节点或代理发送原始波形至 `/waveforms/ingest`。
2. **落盘与上传**：服务端将波形转为 MiniSEED 本地暂存，并同步写入对象存储，生成全局唯一的对象 URI。
3. **元数据入流**：将波形元数据（台站、时间段、采样率、对象 URI 等）发布到 Kafka `waveforms.raw` 主题。
4. **震相拾取**：流式作业消费 `waveforms.raw`，运行深度网络，输出 Pg/Sg/Pn/Sn 等震相并写入 `waveforms.phase_picks`。
5. **事件关联**：REAL 或自研算法消费 `waveforms.phase_picks`，产出候选事件并推送 `waveforms.associations`。
6. **定位与震级**：PINNLocation 作业读取关联结果，计算震中、震源深度，后续作业计算震级与震源机制，最终落库。
7. **结果查询**：Web API 或 BI 工具从列式库查询事件信息，同时可通过对象存储回溯波形。

## 核心功能模块

### 台站管理
- `POST /stations`：新增或更新台站元数据（位置、仪器类型等）。
- `GET /stations`：分页查询台站列表，支持按区域过滤。
- 可拓展指标：心跳、在线率、电量等实时监控字段可通过 Kafka 流接入。

### 波形实时接入
- `POST /waveforms/ingest`：接收原始波形数组或二进制，保存为 MiniSEED，上传对象存储，并发布元数据到 Kafka。
- 异常处理：消息发布失败会记录错误并抛出，可结合 Retry/Dead Letter Topic 保障数据最终一致。

### 编目结果管理
- `GET /events`：查询已定位事件，可按时间、震级、空间范围过滤。
- 列式库 schema 推荐字段：`event_id`, `origin_time`, `latitude`, `longitude`, `depth_km`, `magnitude_ml`, `mechanism`, `phase_count`, `quality_flag`。

### USGS 实时数据接入
- `GET /usgs/events/live`：直连 USGS GeoJSON 实时事件源，支持最小震级、时间窗口与数量限制，可用于大屏或仪表板展示。
- `GET /usgs/stations/live`：获取实时台站分布，可选网络/通道过滤与可用性信息，便于在独立页面绘制分布图。

### 实时处理扩展
- 震相拾取模型：可部署 P/S 深度模型（如 EQTransformer），支持 GPU 加速。
- 事件关联：默认兼容 REAL 算法，亦可集成基于图的聚类方法。
- 定位算法：PINNLocation、双差定位等均可替换，处理结果通过 Kafka 返回。

## API 概览

| 路径 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/stations` | `POST` | 新增/更新台站信息 |
| `/stations` | `GET` | 查询台站列表 |
| `/waveforms/ingest` | `POST` | 上传波形、转存 MiniSEED 并推送 Kafka |
| `/events` | `GET` | 查询已编目的地震事件 |
| `/usgs/events/live` | `GET` | 获取 USGS 实时事件，用于 Web 可视化 |
| `/usgs/stations/live` | `GET` | 获取 USGS 实时台站分布 |

> 更多请求/响应字段详见 `backend/app/schemas` 目录。

## 开发环境与部署步骤

### 前置条件
- Python 3.10+
- Poetry（用于 Python 依赖管理）
- Kafka 及 Schema Registry（可选）
- 对象存储服务（MinIO/AWS S3/阿里云 OSS 等）
- 列式数据库（ClickHouse/Hologres/Doris 等）
- 可选：Flink 1.17+ 或 Spark 3.4+ 集群

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/<org>/national_seismic_catalog_system.git
cd national_seismic_catalog_system/backend

# 安装依赖
poetry install

# 激活虚拟环境（可选）
poetry shell

# 启动 FastAPI 服务
poetry run uvicorn app.main:app --reload
```

访问 `http://localhost:8000/docs` 查看自动生成的 Swagger 文档。

### 集成 Kafka 与对象存储

1. 准备 Kafka 集群，可在开发阶段使用 `docker-compose` 快速启动。
2. 部署 MinIO 或连接现有对象存储，创建 `seismic-waveforms` 等桶。
3. 在 FastAPI `.env` 中配置连接信息（见下节）。
4. 部署 Flink/Spark 作业消费对应主题，实现震相、关联、定位等算法。

## 配置说明

所有关键参数通过环境变量或 `.env` 文件传入。常用配置如下：

| 变量 | 说明 | 示例 |
| ---- | ---- | ---- |
| `STREAMING_DRIVER` | 消息总线驱动（`kafka` 或 `memory`） | `kafka` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka 集群地址 | `broker:9092` |
| `TOPIC_WAVEFORMS_RAW` | 原始波形主题 | `waveforms.raw` |
| `TOPIC_WAVEFORMS_PHASE_PICKS` | 震相拾取输出主题 | `waveforms.phase_picks` |
| `TOPIC_WAVEFORMS_ASSOCIATIONS` | 关联结果主题 | `waveforms.associations` |
| `TOPIC_WAVEFORMS_LOCATIONS` | 定位结果主题 | `waveforms.locations` |
| `OBJECT_STORE_SCHEME` | 对象存储协议 | `s3` |
| `OBJECT_STORE_ENDPOINT` | 对象存储 Endpoint | `http://minio:9000` |
| `OBJECT_STORE_BUCKET` | MiniSEED 存储桶名称 | `seismic-waveforms` |
| `COLUMNAR_DSN` | 列式数据库连接串 | `clickhouse://clickhouse:9000` |
| `TMP_STORAGE_PATH` | 本地 MiniSEED 暂存目录 | `/data/mseed` |
| `USGS_BASE_URL` | USGS 实时数据接口域名 | `https://earthquake.usgs.gov` |
| `USGS_EVENT_PATH` | USGS 事件接口路径 | `/fdsnws/event/1/query` |
| `USGS_STATION_PATH` | USGS 台站接口路径 | `/fdsnws/station/1/query` |
| `USGS_TIMEOUT_SECONDS` | 调用 USGS 接口的超时时间（秒） | `10` |

## 流式作业参考实现

- **Phase Picking Job**
  - 输入：`waveforms.raw`
  - 输出：`waveforms.phase_picks`
  - 核心逻辑：加载深度学习模型（例如 P-PhaseNet、EQTransformer），对波形滑动窗口推断，并将震相标注打包。

- **Association Job**
  - 输入：`waveforms.phase_picks`
  - 输出：`waveforms.associations`
  - 核心逻辑：REAL 或图聚类算法，产出初始事件（事件 ID、候选震相集合、粗略位置）。

- **Location Job**
  - 输入：`waveforms.associations`
  - 输出：`waveforms.locations`
  - 核心逻辑：调用 PINNLocation 或其他反演算法，计算精确震中、震源深度与误差估计。

- **Magnitude & Focal Mechanism Job**
  - 输入：`waveforms.locations`
  - 输出：写入列式库或 `waveforms.magnitudes` 等新主题
  - 核心逻辑：根据 P 波初动、振幅等参数估算震级，利用初动极性求解震源机制。

所有作业需实现状态管理（Checkpointing）、异常重试与滞后处理策略，保证端到端数据一致性。

## 数据存储与治理

- **对象存储结构**：`{bucket}/{network}/{station}/{YYYY}/{MM}/{DD}/{event_id}_{stream_id}.mseed`
- **元数据索引**：Kafka 消息与列式库需包含对象 URI、校验和（MD5/SHA256）以便审计。
- **数据生命周期**：利用对象存储生命周期策略实现热数据与冷数据分层；可将长期归档保存到 Glacier/OBS Archive。
- **权限控制**：推荐结合 IAM 或 STS 令牌授予最小权限访问，防止未授权下载。

## 可观测性与容错策略

- **监控指标**：Kafka Lag、Flink Checkpoint、处理延迟、对象存储写入成功率、API 响应时间。
- **日志与追踪**：集成 OpenTelemetry，链路贯穿 API → Kafka → Flink/Spark → 列式库。
- **异常恢复**：在消息队列中使用 Dead Letter Topic，结合定时回放机制，确保异常波形可重新处理。
- **压力调节**：通过 Kafka 分区扩容、Flink 并行度调节，实现水平扩展；FastAPI 可以通过多副本配合负载均衡。

## 项目结构

```
backend/
  app/
    api/              # FastAPI 路由定义
    core/             # 配置加载（Kafka、对象存储、列式库等）
    db/               # SQLModel 会话与薄层数据访问
    models/           # ORM 模型
    schemas/          # Pydantic 请求/响应模型
    services/
      pipeline/       # 处理上下文与骨架
      processing/     # 拾取、关联、定位、震级、机制接口抽象
      storage/        # MiniSEED 暂存与对象存储上传
      streaming/      # 消息总线抽象与发布器
  pyproject.toml      # 依赖与工程配置
```

## 后续规划

- 引入 Terraform/Helm 模板，实现一键化云端部署。
- 完善 CI/CD 流程，对接流式作业的集成测试。
- 加入前端大屏或 GIS 可视化页面，展示实时震情与台站状态。
- 扩展多模态数据（例如 GNSS、InSAR）融合能力。

## 贡献指南

欢迎社区贡献代码与文档：

1. Fork 仓库并创建特性分支。
2. 在 `backend` 目录运行 `poetry run pytest`（如依赖完整可用）。
3. 提交 Pull Request 时请附带变更描述与测试结果。

## 联系方式

如需交流或商务合作，请联系：**caiyuqiming@163.com**。

## 许可证

本项目遵循仓库根目录的 [LICENSE.md](LICENSE.md)。
