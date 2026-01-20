# 表格流水线设计（V1）

## 1. 目标与范围

本设计文档定义 **表格类 Asset（能耗表 / 运行表）** 的 V1 处理流水线。总体原则：

- 以 **规则 + 配置 + 代码** 为主，可测试、可回放
- 将 **大模型能力封装为可选“解释器/助手”层**，不直接改动底层数据
- 所有表格最终都标准化为 **时序数据**，与工程结构（Building/System/Zone/Device）打通

V1 重点实现：

- 能耗表流水线：`数据规范 → 数据清洗 → 电表功能分项匹配 → 分项能耗统计分析 → 绘图输出`  
- 运行表：只做基础设计占位，后续单独细化（特别是“稳定运行时间段”识别）

---

## 2. 基础数据模型假设

### 2.1 现有资产层

- `assets` 表：存储文件级别 Asset（包括表格文件）
  - 关键字段：`id, project_id, building_id, zone_id, system_id, device_id, modality="table", source, content_role, file_id, capture_time`
- `asset_structured_payloads` 表：结构化结果
  - 用于记录表格解析配置、质量报告、统计摘要等

V1 中新增/约定：

- `schema_type`：
  - `energy_table_v1`：能耗表（电表、热表、水表等）
  - `runtime_table_v1`：设备运行/工况记录表

### 2.2 时序数据层（建议 TimescaleDB）

统一将表格行写入时序表：

```sql
-- 原始读数明细
CREATE TABLE energy_readings (
    id              uuid PRIMARY KEY,
    project_id      uuid NOT NULL,
    meter_id        uuid NOT NULL,        -- 关联电表主数据
    ts              timestamptz NOT NULL, -- 读数时间
    value           double precision NOT NULL,
    value_type      text NOT NULL,        -- 'cumulative' | 'interval'
    unit            text NOT NULL,        -- kWh, kW, m3 等
    source_asset_id uuid NOT NULL,        -- 溯源到哪份表格
    quality_flag    text NULL             -- 'ok' | 'missing' | 'estimated' | 'outlier'
);

-- 功能/分项维度聚合表（可按需预聚合）
CREATE TABLE energy_agg_daily (
    project_id      uuid NOT NULL,
    meter_function  text NOT NULL,        -- 如 'hvac', 'lighting', 'it_room'
    day             date NOT NULL,
    energy_kwh      double precision NOT NULL,
    PRIMARY KEY (project_id, meter_function, day)
);
```

> 实际实现时可用 TimescaleDB hypertable + continuous aggregates 优化。

### 2.3 电表主数据与功能分项

新增或约定：

```sql
CREATE TABLE meters (
    id              uuid PRIMARY KEY,
    project_id      uuid NOT NULL,
    meter_code      text NOT NULL,    -- 与表格中列/行的标识对应
    name            text,
    level           text,             -- main / sub / tenant / virtual
    energy_type     text,             -- electricity / chilled_water / hot_water
    function_tags   text[]            -- ['hvac', 'lighting', 'it_room']
);
```

- 通过 `function_tags` 实现 **电表功能分项匹配**
- 后续可支持一表多标签（如一个电表既供 HVAC 又供通风），按权重分摊

---

## 3. 能耗表流水线（V1 详细）

### 3.1 总体流程

以 `upload_table_asset` 为入口，能耗表的处理链路：

1. **资产入库**：
   - 用户上传表格文件 → 创建 `Asset(modality="table", content_role="energy_table")`
2. **数据规范（标准化）**：
   - 解析 Excel/CSV → pandas DataFrame
   - 识别时间列、读数列、电表标识列 → 转成统一中间结构
3. **数据清洗**：
   - 时间规范化（时区、格式）
   - 去重、缺失值处理、异常值检测
4. **电表功能分项匹配**：
   - 将每条读数关联到 `meter_id`，并通过 `meters.function_tags` 得到功能分项
5. **分项能耗统计分析**：
   - 按天/周/月 & 分项聚合能耗
   - 写入 `energy_agg_daily` 或等价视图
6. **绘图输出（接口层）**：
   - 提供 API 返回适合前端绘图的序列数据
   - 可选：在 Notebook / 报表中用 matplotlib/seaborn 渲染图像

### 3.2 数据规范（标准化）

#### 3.2.1 列角色识别

- 时间列（必选）：通过列名/样例匹配：
  - 关键词：`time, timestamp, datetime, 日期, 时间`
- 电表列：
  - 可能在：
    - 行：一行一个电表，多列为不同时间
    - 列：一列一个电表
  - V1 限制：
    - **优先支持“每行一个时间点，多列为不同电表读数”的纵向表结构**
- 数值列：
  - 列名中包含 `kWh, active_energy, 电量` 等

#### 3.2.2 项目级映射配置（必需）

每个项目维护一份 JSON 配置，示例：

```json
{
  "schema_type": "energy_table_v1",
  "time_column": "记录时间",
  "value_columns": [
    {"column": "CH-01_kWh", "meter_code": "CH-01", "unit": "kWh", "value_type": "cumulative"},
    {"column": "LGT-1_kWh", "meter_code": "LGT-1", "unit": "kWh", "value_type": "interval"}
  ],
  "timezone": "Asia/Shanghai"
}
```

流程：

1. 先尝试自动推断 → 提示工程师确认 / 编辑配置
2. 确认后的配置写入 `AssetStructuredPayload(schema_type="energy_table_v1")`
3. 后续同类表格可直接复用该配置

### 3.3 数据清洗

典型规则：

- **时间轴**：
  - 统一转换为 `UTC` 存库，保留原始时区信息
  - 去除明显错误时间（如未来时间、过旧时间）
- **缺失值**：
  - 缺行：按项目策略标记 `quality_flag='missing'`，不强行插值
  - 多个读数重叠：保留最新或平均（配置驱动）
- **异常值检测**：
  - 规则 1：相邻累计读数差为负 → 标记为 `outlier`
  - 规则 2：单时段增量超出正常上限（例如 > 合理最大负荷 × 时长）
  - 规则 3：连续零值但设备被标记为“常开” → 告警

所有清洗操作要可追踪：

- 在 `energy_readings.quality_flag` 标记
- 在 `AssetStructuredPayload` 中追加“质量报告”摘要

### 3.4 电表功能分项匹配

核心目标：**把电表读数映射到“功能分项”维度**，如：

- `hvac`（暖通空调）
- `lighting`（照明）
- `it_room`（机房 IT 设备）
- `lift`（电梯）等

流程：

1. 基于配置/主数据将 `meter_code` → `meter_id`
2. 从 `meters.function_tags` 拿到一个或多个功能标签
3. 写入 `energy_readings` 时附带 `meter_id`，功能分项在聚合阶段使用

> V1 可先支持“一表一分项”，V2 再扩展为“多分项+权重分摊”。

### 3.5 分项能耗统计分析

以日维度为例：

1. 根据 `value_type` 统一转换为区间能耗：
   - `cumulative`：按同一电表 `ts` 排序，使用差分获得每个区间的 kWh
   - `interval`：直接按时段汇总
2. 按需聚合：
   - 维度：`project_id, meter_function, day`
   - 指标：`sum(energy_kwh)`
3. 将结果写入 `energy_agg_daily` 或使用视图/连续聚合

### 3.6 绘图接口设计

后端主要提供**数据接口**，前端负责可视化。典型 API：

```http
GET /api/v1/projects/{project_id}/energy/agg
  ?group_by=function&bucket=day
  &start=2025-01-01&end=2025-01-31
```

返回：

```json
{
  "bucket": "day",
  "series": [
    {
      "name": "hvac",
      "points": [
        {"ts": "2025-01-01", "value": 1234.5},
        {"ts": "2025-01-02", "value": 1100.2}
      ]
    },
    {
      "name": "lighting",
      "points": [ ... ]
    }
  ]
}
```

前端自由选择折线图、堆叠柱状图等展示。

---

## 4. 运行表流水线（预留设计）

运行表同样是时序数据，但关注点是：

- 设备开/关状态、负荷水平
- 故障/告警事件
- **稳定运行时间段的识别**（后续分析 COP、效率等）

V1 先约定：

- `runtime_table_v1` 中，将原始行标准化为：

```sql
CREATE TABLE runtime_events (
    id              uuid PRIMARY KEY,
    project_id      uuid NOT NULL,
    device_id       uuid NOT NULL,
    ts              timestamptz NOT NULL,
    state           text NOT NULL,  -- on/off/fault/standby 等
    load_ratio      double precision NULL, -- 0~1
    source_asset_id uuid NOT NULL
);
```

- “稳定运行时间段”的识别规则（暂定）：
  - `state='on'` 且连续时间 ≥ N 分钟
  - `load_ratio` 在某个区间内波动较小（例如 0.6~0.9 且方差较低）

后续针对运行表再写一份专门的设计文档，细化：

- 稳定段抽取算法
- 与能耗数据联动（如：在稳定段内计算 COP）

---

## 5. 实施优先级（V1）

1. **数据模型落地**：
   - `energy_readings` / `energy_agg_daily` / `meters` 表
   - `schema_type=energy_table_v1` 的 `AssetStructuredPayload` 结构
2. **能耗表解析服务**：
   - pandas 解析 + 项目级配置
   - 写入 `energy_readings`
3. **清洗与分项聚合**：
   - 质量标记 + 日/周/月分项能耗聚合
4. **查询与绘图接口**：
   - 提供 `project_id` 维度的分项能耗 API
5. **运行表占位实现**：
   - `runtime_events` 基础表结构 + 简单入库逻辑

在 V1 稳定后，再引入大模型做：

- 自动推断/推荐表格列映射配置
- 生成数据质量报告、诊断提示
- 对话式能耗分析（调已有 API 作为“Tools/Skills”）
