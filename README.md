# National Seismic Catalog System

该项目提供一个以大数据流式处理为核心的全国地震编目系统后端原型。整体架构围绕 **Kafka + Flink/Spark + 对象存储 + 列式数据库** 搭建，实现地震波形的实时接入、智能震相拾取、事件关联与定位以及编目结果的快速查询。FastAPI 仅扮演薄层的 API/鉴权/前端接口角色，所有计算密集型任务均通过流式计算引擎完成，确保水平扩展能力与毫秒级响应。

## 架构总览

```
波形采集 → Kafka(Raw Waveforms) → Flink/Spark(Phase Picking) →
Kafka(Phase Picks) → Flink/Spark(Association) → Kafka(Associations) →
PINN Location / Magnitude / Mechanism 作业 → 列式库 & 对象存储 → Web 查询
```

核心组件：

- **消息总线（Kafka）**：统一的实时数据骨干，划分 `waveforms.raw`、`waveforms.phase_picks`、`waveforms.associations`、`waveforms.locations` 等主题，用于阶段性产出与消费。
- **流式计算（Flink/Spark）**：承载震相拾取、REAL 关联、PINNLocation 精定位、震级与震源机制估计等实时处理作业，支持容错与回放。
- **对象存储（S3/OSS/OBS）**：MiniSEED 波形数据持久化的主存储，按台站/日期分区，支持 CDN 分发与冷备份。
- **列式数据库（ClickHouse/Hologres 等）**：面向分析与可视化的事件存储，支撑全国地震编目查询、统计与大屏展示。
- **薄层 API（FastAPI）**：仅负责元数据登记、鉴权、状态查看与对外接口，所有实时处理通过消息流与流式计算集群完成。

## 功能概览

- **台站管理**：`/stations` 接口维护台站基础信息，可扩展对台站状态、心跳等实时指标的写入与查询。
- **实时波形入库**：`/waveforms/ingest` 将波形转存为 MiniSEED，并上传对象存储，同时将元数据推送到 Kafka 原始波形主题，供后续流式作业消费。
- **编目结果查询**：`/events` 提供事件查询能力，列式库可作为 OLAP 数据源，支持大范围统计与可视化。
- **异常处理**：所有流式步骤建议通过 Dead Letter Topic、指标告警（Prometheus + Alertmanager）与链路追踪（OpenTelemetry）实现端到端可观测性。本原型在消息发布失败时会抛出详细日志，方便集成生产级补偿机制。

## 项目结构

```
backend/
  app/
    api/              # FastAPI 路由定义
    core/             # 配置加载（Kafka、对象存储、列式库等）
    db/               # SQLModel 会话（用于薄层 API 的元数据管理）
    models/           # 元数据模型
    schemas/          # Pydantic 请求/响应模型
    services/
      streaming/      # 消息总线抽象与发布器
      storage/        # MiniSEED 暂存与对象存储上传
      pipeline/       # 供流式作业复用的上下文与处理骨架
  pyproject.toml      # 依赖与项目配置
```

## 快速开始

1. **安装依赖**

   ```bash
   cd backend
   poetry install
   ```

2. **启动 FastAPI 薄层服务**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

   服务启动后，可访问 `http://localhost:8000/docs` 查看 API 文档。

3. **配置 Kafka / 对象存储 / 列式库**

   - 在 `.env` 中设置：

     ```env
     STREAMING_DRIVER=kafka
     KAFKA_BOOTSTRAP_SERVERS=broker:9092
     TOPIC_WAVEFORMS_RAW=waveforms.raw
     TOPIC_WAVEFORMS_PHASE_PICKS=waveforms.phase_picks
     TOPIC_WAVEFORMS_ASSOCIATIONS=waveforms.associations
     TOPIC_WAVEFORMS_LOCATIONS=waveforms.locations
     OBJECT_STORE_BUCKET=seismic-waveforms
     OBJECT_STORE_ENDPOINT=http://minio:9000
     OBJECT_STORE_SCHEME=s3
     COLUMNAR_DSN=clickhouse://clickhouse:9000
     ```

   - FastAPI 仅负责写入对象存储与推送 Kafka，Flink/Spark 作业需要独立部署并消费相应主题。

4. **模拟实时入流**

   ```bash
   curl -X POST http://localhost:8000/waveforms/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "station_code": "ABC1",
       "network": "CN",
       "sampling_rate": 100.0,
       "start_time": "2024-01-01T00:00:00Z",
       "end_time": "2024-01-01T00:00:10Z",
       "samples": [0.0, 0.1, 0.2, 0.1, 0.0]
     }'
   ```

   API 会生成 MiniSEED 文件（本地缓存），上传到对象存储，并将对象 URI 与元数据发布到 Kafka `waveforms.raw` 主题。

## 流式处理管线

- `services/pipeline/context.py` 描述统一的数据结构，供 Flink/Spark 作业在各个阶段共享信息。
- `services/pipeline/processing/*` 提供震相拾取、关联、定位、震级与震源机制的抽象接口，可在流式作业中加载深度学习模型、REAL 算法和 PINNLocation。
- `services/streaming/message_bus.py` 封装消息总线，实现了 InMemory（开发测试）与 Kafka（生产）两套驱动，方便在 CI/CD 中模拟流式行为。

## 可观测性与容错建议

- 生产环境建议结合 Prometheus + Grafana 监控 Kafka Lag、Flink Checkpoint、处理时延等指标。
- 借助 Dead Letter Topic 与对象存储版本化功能实现数据回放与审计。
- 对于列式库写入，可通过 Flink Sink 或 Spark Structured Streaming Sink 持续刷新编目结果，FastAPI 只需查询即可。

## 许可协议

本项目遵循仓库根目录的 [LICENSE.md](LICENSE.md)。
