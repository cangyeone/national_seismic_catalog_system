# National Seismic Catalog System

该项目提供一个全国范围地震编目系统的后端原型，实现实时波形数据接入、自动震相拾取、事件关联与定位、震级及震源机制估计等核心流程的骨架。系统采用 FastAPI 构建 RESTful API，并结合 SQLModel 管理关系型数据库数据，使用 MiniSEED 文件对多台站波形进行持久化管理。

## 功能概览

- **台站管理**：通过 `/stations` 接口对台站进行增删改查，并可扩展状态监测信息。
- **实时波形接入**：`/waveforms/ingest` 提供实时波形上传 API，将原始数据保存为 MiniSEED 文件，并将处理任务投递到异步队列。
- **自动处理流水线**：构建了可扩展的处理管线，包括震相拾取（神经网络）、REAL 关联、PINNLocation 精定位、震级与震源机制估计等模块的接口。
- **事件编目**：处理结果写入数据库，可通过 `/events` 接口查询定位结果，后续可用于 Web 可视化。
- **异常处理**：队列和管线在每一步都进行了异常捕获，保证实时服务的鲁棒性，并将失败记录入事件状态。

## 项目结构

```
backend/
  app/
    api/              # FastAPI 路由定义
    core/             # 配置加载
    db/               # 数据库会话管理
    models/           # SQLModel 数据模型
    schemas/          # Pydantic 请求/响应模型
    services/         # 处理管线、存储与工具服务
  pyproject.toml      # 依赖与项目配置
```

## 快速开始

1. **安装依赖**

   ```bash
   cd backend
   poetry install
   ```

2. **启动服务**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

   服务启动后，可访问 `http://localhost:8000/docs` 查看自动生成的 API 文档。

3. **测试实时接入**

   发送如下示例请求即可将模拟波形送入处理管线：

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

   实际部署时可将实时数据接入 Kafka、RabbitMQ 等消息总线，再调用该 API。

## 模块扩展

- **震相拾取**：在 `PhasePickerService.pick_phases` 中接入已有的神经网络模型。
- **事件关联**：在 `AssociatorService.associate` 中调用 REAL 等算法，返回候选事件。
- **定位与震级**：分别在 `LocatorService`、`MagnitudeService`、`MechanismService` 中实现具体业务逻辑。
- **可视化**：可在前端读取 `/events`、`/stations` 接口数据，结合地图组件实现全国地震目录可视化。

## 异常与监控

- 队列处理过程中如有异常会记录在日志并写入事件状态，便于运维人员追踪。
- 可进一步集成 Prometheus、OpenTelemetry 等工具，对处理时延、队列长度等指标进行监控。

## 许可协议

本项目遵循仓库根目录的 [LICENSE.md](LICENSE.md)。
