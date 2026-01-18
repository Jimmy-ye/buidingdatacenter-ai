# 建筑节能多模态AI平台 - 开源仓库推荐清单

> 基于 `PLAN.md` 项目规划文档整理的开源技术栈选型方案
>
> 整理时间：2026-01-17

---

## 📋 目录

- [一、多模态数据处理与RAG框架](#一多模态数据处理与rag框架)
- [二、Agent编排与工作流框架](#二agent编排与工作流框架)
- [三、向量数据库](#三向量数据库)
- [四、文档解析与OCR工具](#四文档解析与ocr工具)
- [五、建筑能耗分析专用工具](#五建筑能耗分析专用工具)
- [六、规则引擎与专家系统](#六规则引擎与专家系统)
- [七、时序数据库](#七时序数据库)
- [八、后端架构模板](#八后端架构模板)
- [九、对象存储集成](#九对象存储集成)
- [十、移动端/手机端开发库](#十移动端手机端开发库) 📱
- [十一、推荐技术栈组合](#十一推荐技术栈组合)
- [十二、服务映射表]( #十二服务映射表)

---

## 一、多模态数据处理与RAG框架

### 🔹 LlamaIndex ⭐ 强烈推荐

**GitHub**: https://github.com/run-llama/llama_index

**适用场景**:
- ✅ 你的 `SearchService` 检索服务
- ✅ 多模态RAG（支持图片、文档、表格混合检索）
- ✅ 与你的 `AssetStructuredPayload` schema完美契合

**核心功能**:
- 多模态文档解析（PDF、图片、表格）
- 向量检索集成（支持Qdrant、Weaviate、pgvector等）
- 与Claude等LLM无缝集成

**对应你的服务**: `AI-OrchestratorService`、`SearchService`

**示例代码**:
```python
from llama_index.core import VectorStoreIndex, Document
from llama_index.vector_stores.qdrant import QdrantVectorStore

# 创建多模态索引
documents = [
    Document(text="建筑能耗分析报告...", metadata={"modality": "document"}),
    Document(text="图片OCR内容...", metadata={"modality": "image"}),
]

vector_store = QdrantVectorStore(host="localhost", port=6333)
index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)
```

---

### 🔹 LangChain + LangGraph

**GitHub**:
- https://github.com/langchain-ai/langchain
- https://github.com/langchain-ai/langgraph

**适用场景**:
- ✅ Agent工作流编排
- ✅ 工具链管理（数据准备→推理→规则校验）

**核心优势**:
- LangGraph提供可视化工作流定义
- 丰富的集成生态（Claude、向量库、数据库）

**对应你的服务**: `AI-OrchestratorService`

**LangGraph工作流示例**:
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    project_id: str
    assets: list
    analysis_result: dict

# 定义工作流
workflow = StateGraph(AgentState)

workflow.add_node("data_prep", prepare_data_node)
workflow.add_node("model_inference", claude_inference_node)
workflow.add_node("rule_check", expert_rule_node)
workflow.add_node("result_summary", summary_node)

workflow.set_entry_point("data_prep")
workflow.add_edge("data_prep", "model_inference")
workflow.add_edge("model_inference", "rule_check")
workflow.add_edge("rule_check", "result_summary")
workflow.add_edge("result_summary", END)

app = workflow.compile()
```

---

### 🔹 Unstructured.io

**GitHub**: https://github.com/Unstructured-IO/unstructured

**适用场景**:
- ✅ 你的 `AssetStructuredPayload` 自动解析
- ✅ PDF、Word、Excel、图片统一处理

**核心功能**:
- 表格提取（对应 `table_data` schema）
- OCR集成（Tesseract、EasyOCR）
- 文档分章节解析（对应 `document_outline` schema）

**对应你的服务**: `AssetService` 的解析Pipeline

**使用示例**:
```python
from unstructured.partition.auto import partition

# 自动识别文件类型并解析
elements = partition(filename="energy_report.pdf")

for element in elements:
    if element.category == "Table":
        # 存储为 table_data schema
        save_table_data(element.to_json())
    elif element.category == "Title":
        # 构建文档大纲
        add_to_outline(element.text)
```

---

## 二、Agent编排与工作流框架

### 🔹 CrewAI

**GitHub**: https://github.com/joaomdmoura/crewAI

**适用场景**:
- ✅ 角色化Agent（诊断Agent、分析Agent、报告Agent）
- ✅ 任务协作编排

**核心特点**:
- 基于角色的Agent定义
- 任务依赖与流程控制

**对应你的需求**: "数据准备 → 模型推理 → 规则校验 → 结果汇总"

**示例代码**:
```python
from crewai import Agent, Task, Crew

# 定义诊断专家Agent
diagnosis_agent = Agent(
    role="建筑节能诊断专家",
    goal="分析建筑能耗数据，识别节能潜力",
    backstory="你拥有20年建筑节能诊断经验...",
    llm=claude_llm
)

# 定义分析任务
analysis_task = Task(
    description="分析项目 {project_id} 的能耗数据",
    expected_output="节能诊断报告",
    agent=diagnosis_agent
)

# 创建Crew
crew = Crew(
    agents=[diagnosis_agent, analysis_agent, report_agent],
    tasks=[analysis_task, report_task],
    verbose=True
)

result = crew.kickoff()
```

---

### 🔹 LangGraph

**GitHub**: https://github.com/langchain-ai/langgraph

**适用场景**:
- ✅ 复杂分支与错误处理
- ✅ 状态机式Agent流程

**优势**:
- 可视化工作流调试
- 支持循环、条件分支

---

### 🔹 AutoGen (微软开源)

**GitHub**: https://github.com/microsoft/autogen

**适用场景**:
- ✅ 多Agent对话协作
- ✅ 人机交互模式

---

## 三、向量数据库

### 🔹 Qdrant ⭐ 推荐（易用性强）

**GitHub**: https://github.com/qdrant/qdrant

**适用场景**:
- ✅ 你的 `AssetFeature` 向量存储
- ✅ 多模态向量检索（文本+图片embedding）

**优势**:
- Rust编写，高性能
- 支持过滤查询（可按 `project_id`、`modality` 过滤）
- 提供Docker部署方案

**对应你的服务**: `SearchService`

**部署示例**:
```bash
# Docker部署
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

**Python集成**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(host="localhost", port=6333)

# 创建collection
client.create_collection(
    collection_name="asset_features",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# 插入向量
client.upsert(
    collection_name="asset_features",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],  # 1536维向量
            payload={
                "project_id": "proj-001",
                "modality": "image",
                "asset_id": "asset-123"
            }
        )
    ]
)

# 检索（带过滤）
results = client.search(
    collection_name="asset_features",
    query_vector=[...],
    query_filter={
        "must": [
            {"key": "project_id", "match": {"value": "proj-001"}},
            {"key": "modality", "match": {"value": "image"}}
        ]
    }
)
```

---

### 🔹 Weaviate

**GitHub**: https://github.com/weaviate/weaviate

**适用场景**:
- ✅ 原生多模态支持（`text2vec-openai`、`nearText`等模块）
- ✅ GraphQL API

---

### 🔹 pgvector（轻量方案）

**GitHub**: https://github.com/pgvector/pgvector

**适用场景**:
- ✅ 如果不想额外部署向量库，直接用PostgreSQL
- ✅ 适合MVP阶段

**SQL示例**:
```sql
-- 创建扩展
CREATE EXTENSION vector;

-- 创建表
CREATE TABLE asset_features (
    id SERIAL PRIMARY KEY,
    asset_id UUID,
    feature vector(1536),
    modality VARCHAR(50),
    project_id UUID
);

-- 创建索引
CREATE INDEX ON asset_features USING ivfflat (feature vector_cosine_ops);

-- 查询最相似的5个
SELECT asset_id, modality FROM asset_features
ORDER BY feature <=> '[0.1,0.2,...]'
LIMIT 5;
```

---

## 四、文档解析与OCR工具

### 🔹 Unstructured (已介绍，重点)

**对应你的Schema**:
- `table_data` → 表格提取
- `document_outline` → 分章节解析
- `image_annotation` → OCR文字提取

---

### 🔹 PyMuPDF (fitz)

**GitHub**: https://github.com/pymupdf/PyMuPDF

**适用场景**:
- ✅ PDF表格提取（2024版本已内置）
- ✅ 高性能PDF解析

**代码示例**:
```python
import fitz  # PyMuPDF

doc = fitz.open("energy_report.pdf")

# 提取表格
for page in doc:
    tables = page.find_tables()
    for table in tables:
        df = table.to_pandas()
        # 存储为 table_data schema
        save_table_data({
            "table_type": "energy_log",
            "headers": df.columns.tolist(),
            "rows": df.to_dict("records")
        })

# 提取文本
text = doc.get_text()
```

---

### 🔹 Tesseract OCR

**GitHub**: https://github.com/tesseract-ocr/tesseract

**适用场景**:
- ✅ 图片文字识别（仪表读数、铭牌信息）
- ✅ 配合PyMuPDF使用

**Python集成**:
```python
import pytesseract
from PIL import Image

# 读取图片中的文字
text = pytesseract.image_to_string(Image.open("meter.jpg"))

# 识别数字（仪表读数）
digits = pytesseract.image_to_string(
    Image.open("meter.jpg"),
    config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789.'
)
```

---

### 🔹 PaddleOCR (国产优秀方案)

**GitHub**: https://github.com/PaddlePaddle/PaddleOCR

**适用场景**:
- ✅ 中文OCR效果好
- ✅ 支持表格识别

**示例**:
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')
result = ocr.ocr("meter.jpg", cls=True)

for line in result:
    text = line[1][0]  # 识别的文字
    confidence = line[1][1]  # 置信度
```

---

## 五、建筑能耗分析专用工具

### 🔹 OpenStudio ⭐ 行业标准

**官网**: https://www.openstudio.net/
**GitHub**: https://github.com/NREL/OpenStudio

**适用场景**:
- ✅ 建筑能耗建模
- ✅ HVAC系统仿真

**集成方式**: 通过命令行调用，将仿真结果存入你的 `SensorData`

**CLI调用示例**:
```python
import subprocess

# 运行OpenStudio仿真
def run_energy_simulation(osm_file_path):
    cmd = [
        "openstudio",
        "run",
        "-w", osm_file_path,
        "-m", "/path/to/weather.epw"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # 解析结果并存储到时序数据库
    parse_and_store_simulation_results(result.stdout)

    return result.returncode == 0
```

---

### 🔹 EnergyPlus

**官网**: https://energyplus.net/
**GitHub**: https://github.com/NREL/EnergyPlus

**适用场景**:
- ✅ 建筑全能耗分析
- ✅ 节能措施评估

---

### 🔹 OCHRE (Python库)

**GitHub**: https://github.com/NREL/OCHRE

**适用场景**:
- ✅ 住宅建筑能耗建模
- ✅ Python原生集成

**对应你的需求**: 可直接嵌入你的后端服务

**示例**:
```python
import ochre

# 创建建筑模型
building = ochre.Building(
    name="test_building",
    hvac_mode="Heat Pump",
    location={"climate_zone": "5A"}
)

# 运行仿真
results = building.run_simulation(duration="1 year")

# 导入到你的SensorData表
for timestamp, data in results.items():
    save_sensor_data(
        sensor_point_id="energy_consumption",
        ts=timestamp,
        value=data["total_energy"]
    )
```

---

### 🔹 pyBuildingEnergy

**官网**: https://pybuildingenergy.readthedocs.io/

**适用场景**:
- ✅ 建筑性能评估
- ✅ 能耗与舒适度计算

---

## 六、规则引擎与专家系统

### 🔹 Drools (Java生态)

**官网**: https://drools.org/
**GitHub**: https://github.com/kiegroup/drools

**适用场景**:
- ✅ 复杂业务规则（`ExpertRule.condition_expr`）
- ✅ 规则版本管理

**注意事项**: 需要Python桥接（可用Py4J或REST API）

**规则示例**:
```
rule "HVAC系统高能耗诊断"
when
    $building: Building(energy_grade == "C" || energy_grade == "D")
    $system: System(type == "HVAC")
    $avg: Double() from accumulate(
        SensorData(sensor_point.system == $system,
                   value > 1000),
        avg($value)
    )
then
    insert(new Recommendation(
        type="HVAC优化",
        priority="HIGH",
        description="HVAC系统平均能耗(" + $avg + ")偏高，建议检查设备效率"
    ));
end
```

---

### 🔹 Business Rules Engine (Python)

**GitHub**: https://github.com/venmo/business-rules

**适用场景**:
- ✅ 纯Python规则引擎
- ✅ 简单的if-then规则

**对应你的服务**: `ExpertRuleService`

**示例**:
```python
from business_rules import run

# 定义规则
rules = [
    {
        "conditions": {
            "all": [
                {"field": "energy_grade", "operator": "equal_to", "value": "C"},
                {"field": "floor_area", "operator": "greater_than", "value": 5000}
            ]
        },
        "actions": [
            {"name": "recommend_hvac_upgrade"}
        ]
    }
]

# 执行规则
result = run(rules, building_data)
```

---

### 🔹 自建规则引擎推荐（JSONLogic）

基于你的 `ExpertRule` 表设计，建议自建轻量规则引擎：

```python
import jsonlogic

class RuleEngine:
    def evaluate(self, condition_expr, context):
        """
        condition_expr 示例:
        {
            "and": [
                {"==": [{"var": "energy_grade"}, "C"]},
                {">": [{"var": "floor_area"}, 5000]}
            ]
        }
        """
        return jsonlogic.apply(condition_expr, context)

    def check_rules(self, project_id):
        # 获取项目上下文
        context = self.get_project_context(project_id)

        # 获取启用的规则
        rules = self.get_active_rules(project_id)

        results = []
        for rule in rules:
            if self.evaluate(rule.condition_expr, context):
                # 生成建议
                recommendation = self.render_recommendation(
                    rule.recommendation_template,
                    context
                )
                results.append({
                    "rule_id": rule.id,
                    "recommendation": recommendation
                })

        return results
```

**安装**: `pip install jsonlogic`

---

## 七、时序数据库

### 🔹 TimescaleDB ⭐ 推荐（PostgreSQL扩展）

**GitHub**: https://github.com/timescale/timescaledb

**适用场景**:
- ✅ 基于PostgreSQL，无需额外维护
- ✅ 支持SQL查询（与你的关系数据库打通）

**对应你的表**: `SensorData`

**安装**:
```sql
-- PostgreSQL中安装扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建时序表（自动分区）
CREATE TABLE sensor_data (
    time TIMESTAMPTZ NOT NULL,
    sensor_point_id INTEGER NOT NULL,
    value DOUBLE PRECISION,
    quality_flag VARCHAR(10)
);

-- 转换为hypertable（按时间分区）
SELECT create_hypertable('sensor_data', 'time');

-- 创建索引
CREATE INDEX ON sensor_data (sensor_point_id, time DESC);

-- 自动压缩历史数据
SELECT add_compression_policy('sensor_data', INTERVAL '30 days');
```

**查询示例**:
```sql
-- 时间范围查询（自动使用分区裁剪）
SELECT time_bucket('1 hour', time) AS hour,
       sensor_point_id,
       avg(value) AS avg_value
FROM sensor_data
WHERE time >= NOW() - INTERVAL '7 days'
  AND sensor_point_id = 123
GROUP BY hour, sensor_point_id;

-- 连续聚合（预计算，加速查询）
CREATE MATERIALIZED VIEW hourly_energy
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS hour,
       sensor_point_id,
       avg(value) AS avg_value,
       max(value) AS max_value
FROM sensor_data
GROUP BY hour, sensor_point_id;
```

---

### 🔹 InfluxDB

**GitHub**: https://github.com/influxdata/influxdb

**适用场景**:
- ✅ 高性能时序写入
- ✅ 类SQL查询语言

**Flux查询示例**:
```flux
from(bucket: "building_energy")
  |> range(start: -7d)
  |> filter(fn: (r) => r.sensor_point_id == "123")
  |> aggregateWindow(every: 1h, fn: mean)
```

---

### 🔹 VictoriaMetrics

**GitHub**: https://github.com/VictoriaMetrics/VictoriaMetrics

**适用场景**:
- ✅ 资源占用低
- ✅ 兼容InfluxDB协议

---

## 八、后端架构模板

### 🔹 FastAPI Boilerplate

**GitHub**: https://github.com/benavlabs/FastAPI-boilerplate

**技术栈**:
- FastAPI + Pydantic V2 + SQLAlchemy 2.0
- PostgreSQL + Redis
- Docker + Docker Compose
- JWT认证 + RBAC权限

**适用场景**:
- ✅ 你的微服务架构模板
- ✅ 包含认证、CRUD、Docker配置

**项目结构**:
```
.
├── app/
│   ├── api/              # API路由
│   ├── core/             # 核心配置
│   ├── db/               # 数据库Session
│   ├── models/           # SQLAlchemy模型
│   ├── schemas/          # Pydantic schemas
│   └── services/         # 业务逻辑
├── tests/
├── alembic/              # 数据库迁移
├── docker-compose.yml
└── requirements.txt
```

---

### 🔹 FastAPI Microservice Template

**GitHub**: https://github.com/MahirMahbub/fastapi-microservice-with-mongodb

**特点**:
- ✅ 清洁架构
- ✅ Repository模式

---

### 🔹 推荐的项目结构（基于你的服务）

```
program-bdc-ai/
├── services/
│   ├── auth_service/             # Auth/UserService
│   ├── project_service/          # ProjectService
│   ├── asset_service/            # AssetService
│   ├── timeseries_service/       # TimeSeriesService
│   ├── ai_orchestrator_service/  # AI-OrchestratorService
│   ├── expert_rule_service/      # ExpertRuleService
│   └── search_service/           # SearchService
├── shared/
│   ├── db/                       # 共享数据库模型
│   ├── utils/                    # 通用工具
│   └── config/                   # 配置管理
├── frontend/
│   ├── pc_web/                   # React前端
│   └── mobile_app/               # Flutter/React Native
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/               # K8s配置
│   └── monitoring/               # Prometheus + Grafana
├── scripts/
│   ├── setup.sh                  # 环境初始化
│   └── deploy.sh                 # 部署脚本
└── docs/
    ├── API.md
    └── DEPLOYMENT.md
```

---

## 九、对象存储集成

### 🔹 MinIO ⭐ 推荐

**GitHub**: https://github.com/minio/minio

**适用场景**:
- ✅ 你的 `FileBlob` 存储
- ✅ S3兼容API

**部署**: Docker一键部署

**Docker部署**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"  # Console
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  minio_data:
```

**Python集成**:
```python
from minio import Minio
from minio.error import S3Error

client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

# 创建bucket
client.make_bucket("asset-files")

# 上传文件
def upload_file(file_path, object_name):
    client.fput_object(
        "asset-files",
        object_name,
        file_path
    )
    return f"http://localhost:9000/asset-files/{object_name}"

# 生成预签名URL（7天有效）
url = client.presigned_get_object("asset-files", "image.jpg", expires=timedelta(days=7))
```

**对应你的表**: `FileBlob`

---

### 🔹 S3FS (挂载到本地)

**GitHub**: https://github.com/s3fs-fuse/s3fs-fuse

**适用场景**:
- ✅ 云存储挂载为本地文件系统

---

## 十、移动端/手机端开发库 📱

> **详细文档**: 请查看 [MOBILE_RECOMMENDATIONS.md](./MOBILE_RECOMMENDATIONS.md) 获取完整的移动端开发指南

### 核心需求回顾（来自PLAN.md）
- **手机端**: 现场采集图片 + 语音/文字说明，并上传到项目库
- **功能**: 登录 + 项目选择 + 图片 + 文字/语音上传

### 🔹 跨平台框架选型

| 框架 | 推荐度 | 技术栈 | 适用场景 |
|-----|-------|-------|---------|
| **React Native** | ⭐⭐⭐ | JavaScript/TypeScript | React技术栈团队 |
| **Flutter** | ⭐⭐⭐ | Dart | 追求性能，自定义UI |
| **uni-app** | ⭐⭐⭐⭐ | Vue.js | 小程序优先（国内） |
| **Taro** | ⭐⭐ | React | React + 小程序 |

**快速决策**:
- 国内用户 + 需要小程序 → **uni-app**（最推荐）
- React技术栈 → **React Native + Expo**
- 追求极致性能 → **Flutter**

---

### 🔹 关键功能开源库

#### 图片采集
- **React Native**: https://github.com/mrousavy/react-native-vision-camera
- **Flutter**: https://pub.dev/packages/camera

#### 语音识别（ASR）
- **离线方案**（推荐）: https://github.com/israr002/rn-whisper-stt（RN）
- **在线方案**（中文更好）: 百度语音识别、阿里云ASR

#### 二维码扫描
- **RN**: Vision Camera内置
- **Flutter**: https://github.com/juliansteenbakker/mobile_scanner

#### GPS定位
- **RN**: https://github.com/michalchudziak/react-native-geolocation-service
- **Flutter**: https://pub.dev/packages/geolocator

#### 离线存储
- **简单存储**: AsyncStorage / SharedPreferences
- **关系数据库**: SQLite (react-native-quick-sqlite / sqflite)

---

### 🔹 推荐技术栈组合（移动端）

#### 方案1: React Native + Expo（最简单）
```bash
npx create-expo-app bdc-ai-app
npm install react-native-paper @tanstack/react-query
npm install expo-camera expo-location expo-av
```

#### 方案2: Flutter（性能优先）
```bash
flutter create bdc_ai_app
flutter pub add dio provider camera geolocator
flutter pub add whisper_kit mobile_scanner
```

#### 方案3: uni-app（小程序优先）
```bash
# 使用HBuilderX创建
# 或CLI
npx @dcloudio/uvm create bdc-ai-miniprogram
```

---

### 🔹 核心功能快速实现

#### 图片上传 + GPS定位
```typescript
import Geolocation from 'react-native-geolocation-service';
import axios from 'axios';

async function uploadImageWithLocation(projectId: string, imageUri: string) {
  // 1. 获取GPS
  const location = await getCurrentLocation();

  // 2. 上传
  const formData = new FormData();
  formData.append('file', { uri: imageUri, type: 'image/jpeg' });
  formData.append('project_id', projectId);
  formData.append('location_meta', JSON.stringify(location));

  await axios.post('/api/v1/assets/upload', formData);
}
```

#### 语音录制 + 转文字
```typescript
// 离线方案（Whisper）
import WhisperSTT from 'rn-whisper-stt';

const whisper = new WhisperSTT({ model: 'tiny', language: 'zh' });
const transcript = await whisper.transcribe(audioFile);

// 在线方案（百度ASR）- 中文效果更好
const transcript = await transcribeWithBaidu(audioFile);
```

---

### 🔹 离线优先架构

```typescript
// 离线上传队列
class OfflineQueue {
  static async add(assetData: any) {
    const queue = await AsyncStorage.getItem('upload_queue');
    const newQueue = [...JSON.parse(queue || '[]'), assetData];
    await AsyncStorage.setItem('upload_queue', JSON.stringify(newQueue));
  }

  static async sync() {
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) return;

    const queue = await this.getQueue();
    for (const item of queue) {
      await uploadToServer(item);
    }
  }
}
```

---

### 🔹 移动端与后端API对接

#### API接口设计
```typescript
interface AssetUploadRequest {
  project_id: string;
  modality: 'image' | 'audio' | 'text';
  file: File;
  location_meta?: {
    latitude: number;
    longitude: number;
  };
  tags: string[];
  source: 'mobile_app';
}
```

#### RESTful调用
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://your-server:8000/api/v1'
});

// 上传Asset
await api.post('/assets/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

// 获取项目列表
const { data } = await api.get('/projects');
```

---

### 🔹 UI组件库推荐

| 框架 | UI库 | 特点 |
|-----|------|------|
| React Native | React Native Paper | Material Design |
| React Native | NativeBase | 组件丰富 |
| Flutter | Material (内置) | Google官方 |
| uni-app | uni-ui | 官方组件 |

---

### 🔹 关键仓库快速链接（移动端）

#### 跨平台框架
- https://github.com/facebook/react-native
- https://github.com/flutter/flutter
- https://github.com/dcloudio/uni-app ⭐
- https://github.com/NervJS/taro

#### React Native核心库
- https://github.com/mrousavy/react-native-vision-camera（相机）
- https://github.com/react-native-image-picker/react-native-image-picker（图片选择）
- https://github.com/TanStack/query（React Query）
- https://github.com/axios/axios（HTTP客户端）

#### Flutter核心库
- https://pub.dev/packages/camera（相机）
- https://github.com/juliansteenbakker/mobile_scanner（二维码）
- https://pub.dev/packages/whisper_kit（语音识别）

#### 语音识别
- https://github.com/israr002/rn-whisper-stt（RN Whisper）
- https://pub.dev/packages/whisper_kit（Flutter Whisper）

---

### 🔹 技术选型决策树

```
团队有React经验？
├─ 是 → React Native
│   ├─ 需要小程序？
│   │   ├─ 是 → Taro
│   │   └─ 否 → React Native + Expo
│   └─ 追求快速开发？
│       ├─ 是 → Expo ⭐
│       └─ 否 → React Native CLI
└─ 否 → 团队熟悉Vue？
    ├─ 是 → uni-app（多端）⭐⭐⭐
    └─ 否 → Flutter（性能优先）
```

---

### 🔹 Week 9+: 移动端开发建议

- [ ] 选择技术栈（推荐：uni-app 或 React Native + Expo）
- [ ] 实现登录 + 项目选择
- [ ] 实现图片拍照 + GPS定位 + 上传
- [ ] 集成语音录制 + 转文字
- [ ] 实现离线队列 + 自动同步
- [ ] 实现二维码扫描（设备识别）
- [ ] UI优化 + 测试

---

## 十一、推荐技术栈组合

### 阶段1 MVP（4-6周）

```yaml
后端框架: FastAPI + SQLAlchemy 2.0
数据库: PostgreSQL + pgvector (向量)
对象存储: MinIO
多模态解析: Unstructured.io
LLM集成: LangChain + Claude
Agent框架: LangGraph (简单工作流)
前端: Streamlit (快速原型)
时序数据: PostgreSQL + TimescaleDB扩展
```

**Docker Compose示例**:
```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: bdc_ai
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  backend:
    build: ./services
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - minio
      - qdrant

volumes:
  postgres_data:
  minio_data:
  qdrant_data:
```

---

### 阶段2 正式版

```yaml
向量库: Qdrant (替换pgvector)
规则引擎: 自建基于jsonlogic + Drools (复杂规则)
文档解析: Unstructured + PyMuPDF + PaddleOCR
能耗分析: OpenStudio CLI集成
Agent: CrewAI (多Agent协作)
前端: React + Ant Design
移动端: Flutter/React Native
```

---

## 十二、服务映射表

| 你的服务 | 推荐开源仓库 | 优先级 | 说明 |
|---------|------------|--------|------|
| `AI-OrchestratorService` | LangChain/LangGraph | ⭐⭐⭐ | Agent工作流编排 |
| `AssetService` (解析) | Unstructured.io + PyMuPDF | ⭐⭐⭐ | 多模态自动解析 |
| `SearchService` | LlamaIndex + Qdrant | ⭐⭐⭐ | 向量检索服务 |
| `ExpertRuleService` | Drools + 自建jsonlogic | ⭐⭐ | 规则引擎 |
| `TimeSeriesService` | TimescaleDB | ⭐⭐⭐ | 时序数据存储 |
| `ProjectService` | FastAPI Boilerplate | ⭐⭐ | 项目管理CRUD |
| `Auth/UserService` | FastAPI + JWT | ⭐⭐ | 认证授权 |
| **手机端App** | **uni-app / React Native** | **⭐⭐⭐** | **现场采集（详见MOBILE_RECOMMENDATIONS.md）** |
| 手机端-相机 | react-native-vision-camera | ⭐⭐⭐ | 图片拍照 |
| 手机端-语音 | rn-whisper-stt / 百度ASR | ⭐⭐⭐ | 语音转文字 |
| 手机端-GPS | react-native-geolocation-service | ⭐⭐ | GPS定位 |
| 手机端-离线 | AsyncStorage + SQLite | ⭐⭐ | 离线缓存 |
| PC前端 | FastAPI Boilerplate (后端模板) | ⭐⭐ | 后端API模板 |
| 建筑能耗分析 | OpenStudio CLI | ⭐⭐ | 能耗仿真 |
| 文档解析OCR | PaddleOCR (中文) | ⭐⭐ | 图片文字识别 |

---

## 十三、快速开始指南

### 1. 基础环境搭建

```bash
# 克隆FastAPI模板
git clone https://github.com/benavlabs/FastAPI-boilerplate.git services

# 安装依赖
cd services
pip install -r requirements.txt

# 添加项目依赖
pip install \
    langchain \
    langchain-anthropic \
    langgraph \
    llama-index \
    qdrant-client \
    unstructured[all] \
    pymupdf \
    paddleocr \
    psycopg2-binary \
    sqlalchemy \
    timescaledb-psycopg2
```

---

### 2. Docker一键部署（基础设施）

```bash
# 创建docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: bdc_ai
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  minio_data:
  qdrant_data:
EOF

# 启动服务
docker-compose up -d
```

---

### 3. 初始化数据库

```python
# scripts/init_db.py
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://admin:password@localhost:5432/bdc_ai")

# 创建扩展
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
    conn.commit()

# 导入表结构（参考PLAN.md中的表设计）
# ...

print("Database initialized!")
```

---

### 4. 实现第一个Agent

```python
# services/ai_orchestrator_service/agents/diagnosis_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_anthropic import ChatAnthropic
from langchain import tools

# 初始化Claude
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# 定义工具
@tool
def search_similar_cases(project_id: str):
    """检索相似的建筑节能案例"""
    # 调用SearchService
    pass

@tool
def analyze_energy_data(building_id: str):
    """分析建筑能耗数据"""
    # 调用TimeSeriesService
    pass

@tool
def apply_expert_rules(building_id: str):
    """应用专家规则"""
    # 调用ExpertRuleService
    pass

tools = [search_similar_cases, analyze_energy_data, apply_expert_rules]

# 创建Agent
agent = create_openai_functions_agent(llm, tools)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 运行
result = agent_executor.invoke({
    "input": "分析项目XXX的能耗问题并给出节能建议"
})
```

---

## 十四、关键仓库快速链接

### 多模态RAG
- https://github.com/run-llama/llama_index
- https://github.com/Unstructured-IO/unstructured

### Agent框架
- https://github.com/langchain-ai/langgraph
- https://github.com/joaomdmoura/crewAI
- https://github.com/microsoft/autogen

### 向量库
- https://github.com/qdrant/qdrant
- https://github.com/pgvector/pgvector
- https://github.com/weaviate/weaviate

### 文档解析
- https://github.com/PaddlePaddle/PaddleOCR
- https://github.com/pymupdf/PyMuPDF
- https://github.com/tesseract-ocr/tesseract

### 建筑能耗
- https://github.com/NREL/OpenStudio
- https://github.com/NREL/OCHRE
- https://github.com/NREL/EnergyPlus

### 后端模板
- https://github.com/benavlabs/FastAPI-boilerplate
- https://github.com/MahirMahbub/fastapi-microservice-with-mongodb

### 时序数据库
- https://github.com/timescale/timescaledb
- https://github.com/VictoriaMetrics/VictoriaMetrics
- https://github.com/influxdata/influxdb

### 规则引擎
- https://github.com/kiegroup/drools
- https://github.com/venmo/business-rules

### 对象存储
- https://github.com/minio/minio
- https://github.com/s3fs-fuse/s3fs-fuse

---

## 十五、下一步行动建议

### Week 1-2: 基础架构
- [ ] 部署Docker Compose环境（PostgreSQL + MinIO + Qdrant）
- [ ] 使用FastAPI Boilerplate搭建基础服务骨架
- [ ] 实现ProjectService的CRUD（参考PLAN.md表设计）

### Week 3-4: 多模态解析
- [ ] 集成Unstructured.io实现文件上传与解析
- [ ] 实现AssetService的基础功能
- [ ] 测试PDF表格提取和图片OCR

### Week 5-6: AI集成
- [ ] 集成LangChain + Claude
- [ ] 实现第一个简单的Agent（单项目问答）
- [ ] 搭建LlamaIndex + Qdrant检索服务

### Week 7-8: 工作流与规则
- [ ] 使用LangGraph实现完整工作流
- [ ] 实现ExpertRuleService（基于jsonlogic）
- [ ] 创建第一批专家规则（HVAC诊断）

### Week 9+: 扩展与优化
- [ ] 集成OpenStudio能耗仿真
- [ ] 开发React前端
- [ ] 开发移动端App
- [ ] 性能优化与安全加固

---

## 十六、参考资源

### 文档
- LlamaIndex文档: https://docs.llamaindex.ai/
- LangChain文档: https://python.langchain.com/
- Qdrant文档: https://qdrant.tech/documentation/
- TimescaleDB文档: https://docs.timescale.com/

### 教程
- 多模态RAG教程: https://www.llamaindex.ai/blog/multimodal-rag-pipeline-with-llamaindex-and-neo4j-a2c542eb0206
- LangGraph教程: https://langchain-ai.github.io/langgraph/
- FastAPI生产级部署: https://dev.to/fastapi

### 社区
- LangChain Discord: https://discord.gg/langchain
- LlamaIndex Discord: https://discord.gg/4EGcWXk
- Qdrant Discord: https://discord.gg/PzE9XS7u

---

**文档版本**: v1.0
**最后更新**: 2026-01-17
**维护者**: BDC-AI项目组

---

## 附录：快速命令参考

### Docker常用命令
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f postgres

# 停止服务
docker-compose down

# 清理数据（危险！）
docker-compose down -v
```

### Python依赖安装
```bash
# 核心依赖
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic

# AI/ML
pip install langchain langchain-anthropic langgraph llama-index

# 向量库
pip install qdrant-client pgvector

# 文档解析
pip install "unstructured[all]" pymupdf paddleocr

# 时序数据库
pip install timescaledb-psycopg2

# 对象存储
pip install minio

# 规则引擎
pip install jsonlogic
```

### 数据库操作
```bash
# 连接PostgreSQL
psql -h localhost -U admin -d bdc_ai

# 备份数据库
pg_dump -U admin bdc_ai > backup.sql

# 恢复数据库
psql -U admin bdc_ai < backup.sql
```
