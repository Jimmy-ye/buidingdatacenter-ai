# 建筑节能多模态数据中心与 Agent 平台规划

## 1. 项目整体目标

- **核心理念**：构建一个面向建筑节能诊断与能源管理的多模态“数据中心 + Agent + 专家库”平台。
- **主要能力**：
  - 汇总管理项目相关的图片、表格、文本、音频、时序能耗数据等多模态资料。
  - 通过大模型（Claude 等）+ 工具链构建“类 Agent”，自动调用和处理这些资料。
  - 结合基于专家知识与历史案例的“决策中心”，输出节能诊断和策略建议。
  - 支持多端接入：
    - PC 端：分析、决策、报告输出（Python 为主）。
    - 手机端：现场采集图片 + 语音/文字说明，并上传到对应项目库。
    - 服务器：统一数据中心与 AI/规则引擎编排。

---

## 2. 整体系统架构

### 2.1 分层视角

- **客户端层**
  - PC Web UI（浏览器访问）：项目管理、数据浏览、任务创建、报告查看。
  - 手机 App / 小程序：现场采集图片、语音/文字说明，上传到项目库。

- **服务层（Python 为主）**
  - API 网关 / 认证服务（如 FastAPI 实现）：统一鉴权、路由入口。
  - 多模态数据中心服务：项目、建筑、设备、资产（Asset）、时序数据管理。
  - AI-Orchestrator（AI 编排服务）：封装 Claude 调用与工具链，管理 Agent 流程。
  - 专家库决策中心：规则引擎 + 案例库，形成结构化节能策略。
  - 检索与向量服务：统一多模态向量检索接口。

- **数据层**
  - 关系数据库（PostgreSQL / MySQL）：项目结构、设备、资产元数据、任务与结果等。
  - 对象存储（MinIO / 云存储）：原始文件（图片、PDF、Excel、音频等）。
  - 向量库（pgvector / Milvus 等）：文本、图片、表格等嵌入向量，用于语义检索。
  - 时序数据存储（可用时序库或 DB 分表）：能耗、电量、温度等传感器数据。

---

## 3. 数据中心与核心表结构草图

### 3.1 工程与空间模型

- **Project（项目）**
  - 字段：`id`, `name`, `client`, `location`（城市/气候区）, `type`（公共建筑/住宅/工业等）, `status`, `start_date`, `end_date`。
  - 关系：1–N `Building`，1–N `AnalysisTask`。

- **Building（建筑）**
  - 字段：`id`, `project_id`, `name`, `usage_type`（办公、商场…）, `floor_area`, `year_built`, `energy_grade`。
  - 关系：1–N `Zone`，1–N `System`。

- **Zone（区域/楼层/房间）**
  - 字段：`id`, `building_id`, `name`, `type`（楼层/房间/功能区）, `geometry_ref`（可选：BIM/平面图坐标引用）。
  - 关系：1–N `Device`，1–N `Asset`。

### 3.2 系统与设备模型

- **System（系统）**
  - 字段：`id`, `building_id`, `type`（HVAC/照明/给排水/电梯…）, `name`, `description`。
  - 关系：1–N `Device`，1–N `SensorPoint`。

- **Device（设备）**
  - 字段：`id`, `system_id`, `zone_id`（可选）, `device_type`（冷机、风机盘管、灯具…）, `model`, `rated_power`, `serial_no`。
  - 关系：1–N `SensorPoint`，1–N `Asset`。

### 3.3 多模态资料模型（以 Asset 为核心）

- **Asset（多模态资产，统一抽象）**
  - 关联维度：`project_id`, `building_id`, `zone_id`, `system_id`, `device_id`（部分可空）。
  - 基本字段：
    - `id`
    - `modality`：`image` / `table` / `text` / `audio` / `document` / `timeseries_snapshot`
    - `source`：`mobile_app` / `pc_upload` / `external_system` / `ai_generated` / `ocr` / `asr`
    - `title`, `description`
    - `file_id`（关联原始文件存储 `FileBlob`）
    - `structured_payload_id`（关联结构化解析结果，可选）
    - `capture_time`（采集/形成时间）
    - `location_meta`（GPS / 楼层 / 房间号等 JSON）
    - `tags`（JSON 数组，如 `["围护结构","渗漏","隐患"]`）
    - `quality_score`, `status`（`raw` / `parsed` / `validated`）

- **FileBlob（文件物理存储信息）**
  - 字段：`id`, `storage_type`（`minio` / `oss` / `local`）, `bucket`, `path`, `file_name`, `content_type`, `size`, `hash`。
  - 功能：描述原始文件在对象存储中的位置和属性，实现去重和完整性校验。

- **AssetStructuredPayload（结构化解析结果）**
  - 字段：`id`, `asset_id`, `schema_type`（`image_annotation` / `table_data` / `text_note` / `audio_transcript` / `document_outline`）, `payload`（JSON）, `version`, `created_by`（`human`/`ai`）, `created_at`。
  - 功能：存放统一 schema 下的结构化内容（见第 4 节）。

- **AssetFeature（向量与特征）**
  - 字段：`id`, `asset_id`, `feature_type`（`text_embedding` / `image_embedding` / `table_key_embedding` 等）, `vector`（向量库存储引用或直接存储）, `metadata`（JSON：段落号、表格行号等）。
  - 功能：支持多模态语义检索和相似案例查找。

### 3.4 时序与点位

- **SensorPoint（监测点/表计）**
  - 字段：`id`, `project_id`, `building_id`, `system_id`, `device_id`, `code`, `name`, `point_type`（电表、热量表、温度、流量…）, `unit`, `location_meta`。
  - 关系：1–N `SensorData`。

- **SensorData（时序数据）**
  - 字段：`id`（可选暴露）, `sensor_point_id`, `ts`（时间戳）, `value`, `quality_flag`。
  - 存储：可使用时序数据库或分表策略，保证高写入和查询性能。

### 3.5 任务、结果与专家库

- **AnalysisTask（分析任务）**
  - 字段：`id`, `project_id`, `building_id`, `target_scope`（系统/设备/全建筑）, `task_type`（能耗基准/节能诊断/改造评估…）, `status`（`pending`/`running`/`done`/`failed`）, `input_refs`（JSON：使用到的 Asset/时序/规则 ID 列表）, `created_by`, `created_at`。

- **AnalysisResult（分析结果）**
  - 字段：`id`, `task_id`, `summary_text`（人可读摘要）, `structured_json`（问题列表、措施、优先级、估算节能量等结构化输出）, `score`（节能潜力评分等）。

- **ExpertRule（专家规则）**
  - 字段：`id`, `scope`（`building` / `system` / `device` / `usage_pattern`）, `name`, `description`, `condition_expr`（DSL/JSON，由规则引擎解释）, `recommendation_template`（可带变量占位）, `enabled`, `version`。

- **CaseLibrary（案例库）**
  - 字段：`id`, `project_ref`（可选：来源项目）, `problem_profile`, `measures`, `effect`（结构化 JSON）, `text_summary`（文本摘要）, `vector`（案例向量）。

---

## 4. 服务划分与职责

### 4.1 服务列表

- **Auth / UserService**
  - 管理用户、角色、项目权限；提供统一鉴权接口。

- **ProjectService**
  - 管理 `Project/Building/Zone/System/Device` 的增删改查。
  - 提供“项目结构树”API（供前端和 AI 使用）。

- **AssetService（多模态资料服务）**
  - 管理 `Asset`、`FileBlob`、`AssetStructuredPayload`、`AssetFeature`。
  - 提供：上传、多条件查询、删除/版本管理、聚合视图。

- **TimeSeriesService**
  - 管理 `SensorPoint`、`SensorData`。
  - 提供：统计/对标/区间查询等接口。

- **AI-OrchestratorService（AI 编排服务）**
  - 封装 Claude（及其他模型）调用，统一接入大模型。
  - 负责 Agent 工作流：数据准备 → 模型推理 → 规则校验 → 结果汇总。

- **ExpertRuleService（专家规则服务）**
  - 维护 `ExpertRule`、`CaseLibrary`。
  - 对外：规则评估 API、案例检索 API。

- **SearchService（检索服务）**
  - 封装底层向量库/全文检索，实现统一搜索接口。

---

## 5. 统一数据格式设计（面向多模态和 Agent）

### 5.1 统一 DataItem 视图（提供给 Agent 使用）

为简化 Agent 逻辑，对上提供统一的 `DataItem` 视图，底层由 AssetService 聚合：

```json
{
  "id": "asset-uuid",
  "project_id": "...",
  "building_id": "...",
  "context": {
    "zone": "5F 西侧办公室",
    "system": "HVAC",
    "device": "风机盘管 FCU-03",
    "capture_time": "2025-11-01T10:23:00Z",
    "source": "mobile_app",
    "tags": ["围护结构", "冷桥", "现场检查"],
    "location_meta": { "gps": "...", "room_no": "501" }
  },
  "modality": "image",
  "payload_schema": "image_annotation",
  "raw_url": "https://.../bucket/path.jpg",
  "structured_payload": { },
  "features": [
    { "type": "image_embedding", "vector_id": "..." },
    { "type": "text_embedding", "vector_id": "..." }
  ]
}
```

- Agent 只依赖 `DataItem`，不直接访问底层表结构。
- `structured_payload` 字段依赖统一 schema（见下文各模态定义）。

### 5.2 通用元数据字段规范

所有模态在结构化层面（`AssetStructuredPayload.payload`）应具备的通用字段：

- `id`：对应 `asset_id` 或逻辑标识。
- `project_id`：所属项目。
- `modality`：模态类型（`image`/`table`/`text`/`audio`/`document` 等）。
- `context`：
  - `building_id`, `zone_id`, `system_id`, `device_id`（可空）
  - `capture_time`
  - `source`（`mobile_app`/`pc_upload`/`external_system`/`ai_generated`/`ocr`/`asr`）
  - `tags`（业务标签，如“围护结构”“空调系统”“设计图纸”等）
- `raw_url`：原始数据访问路径（通过 FileBlob 映射）。
- `schema_version`：结构化 schema 版本号。
- `created_at`, `created_by`：生成时间与责任主体。

### 5.3 各模态结构化 schema 约定

#### 5.3.1 图片：`image_annotation`

示例字段：

```json
{
  "image_meta": {
    "width": 1920,
    "height": 1080,
    "format": "jpeg",
    "exif": { "make": "...", "model": "..." }
  },
  "annotations": {
    "objects": [
      {
        "label": "裂缝",
        "bbox": [100, 200, 400, 600],
        "confidence": 0.92,
        "comment": "外墙保温层开裂"
      }
    ],
    "global_tags": ["围护结构", "缺陷", "维修建议"]
  },
  "derived_text": "仪表读数：1234 kWh"
}
```

- `image_meta`：图片尺寸、格式与可选 EXIF 信息（可做隐私过滤）。
- `annotations.objects`：检测到的目标（可由模型/人工标注产生）。
- `global_tags`：整体标签，方便检索与过滤。
- `derived_text`：OCR 提取的文字，如铭牌、仪表读数等。

#### 5.3.2 表格：`table_data`

```json
{
  "table_type": "energy_log",
  "headers": ["时间", "电表读数(kWh)", "区域"],
  "rows": [
    {"时间": "2025-01-01 00:00", "电表读数(kWh)": 1234.5, "区域": "5F"},
    {"时间": "2025-01-01 01:00", "电表读数(kWh)": 1250.7, "区域": "5F"}
  ],
  "key_columns": ["时间"],
  "unit_info": {
    "电表读数(kWh)": "kWh"
  }
}
```

- `table_type`：表格业务类型（能耗日志、资产盘点、巡检记录等）。
- `headers`：列名。
- `rows`：行数据统一为「列名–值」形式，便于 AI 与统计处理。
- `key_columns`：主索引列（例如 `时间`、`设备编号` 等）。
- `unit_info`：各列单位说明。

#### 5.3.3 文本：`text_note`

```json
{
  "content": "5F 西侧办公室夏季空调用电偏高，怀疑空调设定过低且长时间无人关闭。",
  "language": "zh-CN",
  "source": "manual",
  "role": "field_note",
  "segment_index": 0
}
```

- `content`：文本内容。
- `language`：语言代码。
- `source`：来源（人工录入、ASR、OCR、模型生成等）。
- `role`：文本的业务角色（现场记录、诊断结论、客户需求、报告段落）。
- `segment_index`：如果来自长文拆分，则标记分段序号。

#### 5.3.4 音频：`audio_transcript`

```json
{
  "audio_url": "https://.../audio/xxx.wav",
  "duration": 35.6,
  "format": "wav",
  "transcript": "这里是五楼西侧办公室，空调送风量明显不足，回风口有积灰。",
  "confidence": 0.94,
  "language": "zh-CN",
  "segments": [
    {"start": 0.0, "end": 5.0, "text": "这里是五楼西侧办公室"},
    {"start": 5.0, "end": 12.0, "text": "空调送风量明显不足"}
  ]
}
```

- 保留原始音频路径与转写文本。
- `segments` 支持基于时间戳的精细定位与对应画面。

#### 5.3.5 文档：`document_outline`

```json
{
  "doc_type": "audit_report",
  "sections": [
    {
      "title": "建筑概况",
      "level": 1,
      "text": "本项目位于...",
      "page_range": [1, 2]
    },
    {
      "title": "能耗现状分析",
      "level": 1,
      "text": "近三年用电...",
      "page_range": [3, 5]
    }
  ],
  "extracted_tables": ["asset-id-table-1", "asset-id-table-2"]
}
```

- `doc_type`：文档类型（设计文件、规范、审计报告等）。
- `sections`：分章节结构，便于 Agent 只引用部分内容。
- `extracted_tables`：与表格型 Asset 的关联。

### 5.4 统一多模态处理 Pipeline 规则

#### 5.4.1 原始数据接入规则

- 无论来源（手机/PC/外部系统），所有数据首先落地为：
  - `Asset` + `FileBlob`（原始文件）；
  - 最少字段：`project_id`, `modality`, `capture_time`, `source`。

#### 5.4.2 解析与标准化 Pipeline

- 按模态触发对应处理器，生成 `AssetStructuredPayload`：
  - 图片：压缩 → 去除敏感 EXIF → OCR → 目标检测 → 写 `image_annotation`。
  - 文本：清洗 → 分段 → 语言检测 → 写 `text_note`。
  - 表格：解析表头 → 类型推断 → 列名规范映射 → 写 `table_data`。
  - 音频：ASR 转写 → 写 `audio_transcript`。
  - 文档：分章节 + 表格抽取 → 写 `document_outline`。

#### 5.4.3 向量化与检索规则

- 对所有 `structured_payload` 中可检索文本或特征：
  - 统一抽取成 `AssetFeature`（含 `feature_type` 与 `metadata`）。
  - 底层由向量库实现相似度检索，上层通过 `SearchService` 暴露统一接口。

#### 5.4.4 版本管理与溯源规则

- 每次重新解析/清洗/纠错都会生成新版本 `AssetStructuredPayload`：
  - `version` 字段递增；`asset_id` 不变。
  - 保留历史版本，便于审计与对比。
- Agent 默认使用最新版本，也可按需指定历史版本。

#### 5.4.5 Agent 使用规则

- Agent 不直接访问底层数据库/文件，只通过：
  - `GET /data/items`（返回 `DataItem` 统一视图）、
  - `SearchService`（语义检索）、
  - `ExpertRuleService`（规则评估与案例检索）。
- 这样可以保证：
  - 业务层可演进（底层表结构可优化/拆分），
  - Agent 提示词与工具调用接口保持稳定。

---

## 6. 实施路线概述

### 阶段 1：MVP（4–6 周）

- 搭建基础后端：FastAPI + DB + 对象存储（MinIO）+ 简单向量库。
- 实现：
  - `Project/Building/Zone/System/Device` 基础管理；
  - `Asset` 上传与简单查询；
  - 手机端：登录 + 项目选择 + 图片 + 文字上传；
  - PC 端：简单 Web/Streamlit 页面，浏览项目与资料；
  - 接入 Claude，实现基于单项目文本资料的问答与简单诊断。

### 阶段 2：多模态与专家库雏形

- 增加图片 OCR/特征提取 + 向量检索；
- 设计并实现第一批专家规则（如空调系统节能诊断的典型条件）；
- 建立第一条完整 Agent 流程：年度能耗体检 → 问题诊断 → 策略建议 → 报告草案。

### 阶段 3：优化与扩展

- 完善 PC 端正式前端（React + Ant Design 或类似框架）；
- 扩展更多系统/场景的专家规则与案例库；
- 手机端增加离线缓存、批量上传、定位/二维码设备识别等高级功能；
- 优化性能与安全（权限控制、审计日志、数据脱敏等）。
