# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

BDC-AI 是一个面向建筑节能诊断与能源管理的多模态"数据中心 + Agent + 专家库"平台。平台通过大模型与工具链构建智能 Agent，自动处理建筑项目中的多模态资料（图片、表格、文本、音频、时序能耗数据等），结合专家知识库与历史案例，输出节能诊断和策略建议。

## 核心技术栈

- **后端框架**: FastAPI 0.104.1
- **数据库 ORM**: SQLAlchemy 2.0.23
- **数据库**: PostgreSQL + TimescaleDB (关系型 + 时序扩展)
- **向量检索**: pgvector (PostgreSQL 扩展)
- **对象存储**: MinIO (S3 兼容)
- **测试框架**: Pytest

## 常用命令

### 启动服务

```bash
# 从项目根目录启动
python -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload

# 从 backend 目录启动
cd services/backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定标记的测试
pytest tests/ -m unit       # 单元测试
pytest tests/ -m integration # 集成测试
pytest tests/ -m api        # API 测试

# 生成覆盖率报告
pytest tests/ --cov=shared --cov=services --cov-report=html
```

### 安装依赖

```bash
# 安装后端依赖
cd services/backend
pip install -r requirements.txt
```

## 项目架构

### 目录结构

```
program-bdc-ai/
├── services/                      # 后端服务
│   └── backend/                   # 统一后端服务（阶段 1 MVP）
│       ├── app/
│       │   ├── main.py            # FastAPI 应用入口
│       │   ├── api/               # API 路由
│       │   │   └── v1/
│       │   │       ├── health.py  # 健康检查
│       │   │       └── projects.py # 项目管理
│       │   ├── core/              # 服务级配置（待添加）
│       │   ├── models/            # SQLAlchemy 模型（待添加）
│       │   ├── schemas/           # Pydantic 模型（请求/响应）
│       │   │   └── project.py
│       │   └── services/          # 业务逻辑（待添加）
│       └── requirements.txt       # Python 依赖
├── shared/                        # 共享代码
│   ├── config/
│   │   └── settings.py            # Settings 配置类（使用 lru_cache 单例）
│   ├── db/
│   │   ├── base.py                # SQLAlchemy 声明式基类
│   │   ├── session.py             # 数据库会话管理
│   │   └── models_project.py      # 项目相关模型
│   └── utils/                     # 通用工具（待添加）
├── PLAN.md                        # 项目详细规划文档
├── OPEN_SOURCE_RECOMMENDATIONS.md # 开源技术栈推荐
├── TECHNICAL_GUIDES.md            # 技术解析文档
└── README.md                      # 项目说明
```

### 服务架构（阶段 1 MVP）

当前采用单体架构，所有功能模块在 `services/backend/` 中实现。未来阶段（阶段 2+）将拆分为独立微服务：

- **auth_service** - 用户认证与权限
- **project_service** - 项目/建筑/区域/系统/设备管理
- **asset_service** - 多模态资料管理（图片、表格、文本、音频、文档）
- **timeseries_service** - 时序能耗数据管理
- **ai_orchestrator_service** - AI 编排与 Agent 流程
- **expert_rule_service** - 专家规则引擎与案例库
- **search_service** - 多模态检索服务

## 核心数据模型

### 项目与空间模型

- **Project**: 项目基础信息（客户、位置、类型、状态）
- **Building**: 建筑信息（用途类型、建筑面积、建设年份、能效等级）
- **Zone**: 区域/楼层/房间划分
- **System**: 系统（HVAC、照明、给排水、电梯等）
- **Device**: 具体设备（冷机、风机盘管、灯具等）
- **SensorPoint**: 监测点/表计（电表、热量表、温度传感器等）

### 多模态资产模型

- **Asset**: 统一抽象的多模态数据（核心模型）
- **FileBlob**: 原始文件物理存储信息（MinIO）
- **AssetStructuredPayload**: 解析后的结构化内容（支持多种 schema）
- **AssetFeature**: 向量特征，用于语义检索

支持的模态类型（`modality`）：
- `image` - 图片（含 OCR、目标检测）
- `table` - 表格（能耗日志、资产盘点、巡检记录等）
- `text` - 文本（现场记录、诊断结论等）
- `audio` - 音频（含 ASR 转写）
- `document` - 文档（PDF、Word 等，含章节结构）
- `timeseries_snapshot` - 时序数据快照

### 任务与专家库

- **AnalysisTask**: 分析任务（能耗基准、节能诊断、改造评估）
- **AnalysisResult**: 分析结果（诊断结论、策略建议、估算节能量）
- **ExpertRule**: 专家规则（条件表达式 + 推荐模板）
- **CaseLibrary**: 历史案例库

## 统一数据格式

### DataItem 视图

所有多模态数据通过 `AssetService` 聚合为统一的 `DataItem` 视图供 Agent 使用：

```python
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
        "location_meta": {"gps": "...", "room_no": "501"}
    },
    "modality": "image",
    "payload_schema": "image_annotation",
    "raw_url": "https://.../bucket/path.jpg",
    "structured_payload": {...},
    "features": [...]
}
```

### 结构化 Schema 规范

各模态在 `AssetStructuredPayload.payload` 中的结构化格式：

- `image_annotation` - 图片（含 OCR、目标检测、全局标签）
- `table_data` - 表格（表头、行数据、主索引列、单位信息）
- `text_note` - 文本（内容、语言、来源、业务角色）
- `audio_transcript` - 音频（时长、转写文本、时间分段）
- `document_outline` - 文档（章节结构、提取的表格）

## 配置管理

### Settings 配置类

位置：`shared/config/settings.py`

使用 `lru_cache` 实现单例模式：

```python
from shared.config.settings import get_settings

settings = get_settings()
print(settings.database_url)
```

### 环境变量

```bash
# 数据库连接 URL
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# MinIO 对象存储地址
BDC_MINIO_ENDPOINT=localhost:9000
```

## 数据库使用

### ORM 基类

位置：`shared/db/base.py`

所有 SQLAlchemy 模型必须继承自 `Base`：

```python
from shared.db.base import Base
from sqlalchemy import Column, Integer, String

class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
```

### 会话管理

位置：`shared/db/session.py`

使用 SQLAlchemy 2.0 语法，通过依赖注入获取会话：

```python
from shared.db.session import get_db
from sqlalchemy.orm import Session

@app.get("/api/v1/projects/")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects
```

### 表创建

应用启动时自动创建所有表（在 `app/main.py` 的 `on_startup` 事件中）：

```python
@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
```

## API 路由规范

### 路由组织

- API 路由放在 `app/api/v1/` 目录下
- 使用 FastAPI 的 `APIRouter` 模块化路由
- 在 `app/main.py` 中统一注册路由，并添加 prefix 和 tags

### 路由注册示例

```python
# app/main.py
from .api.v1 import health, projects

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
```

### API 文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Agent 开发指南

### Agent 使用规则

Agent 不直接访问底层数据库/文件，只通过：
- `GET /api/v1/data/items` - 返回 `DataItem` 统一视图
- `SearchService` - 语义检索
- `ExpertRuleService` - 规则评估与案例检索

### Agent 工作流

标准 Agent 流程：**数据准备 → 模型推理 → 规则校验 → 结果汇总**

### 多模态处理 Pipeline

1. **原始数据接入** - 落地为 `Asset` + `FileBlob`
2. **解析与标准化** - 生成 `AssetStructuredPayload`
3. **向量化与检索** - 生成 `AssetFeature`，支持语义检索
4. **版本管理** - 每次重新解析生成新版本，保留历史

## 开发阶段

### 当前阶段：阶段 1 MVP（4-6 周）

- [x] 搭建基础后端架构
- [x] 实现健康检查接口
- [ ] 实现 Project/Building/Zone/System/Device 管理
- [ ] 实现 Asset 多模态资料上传与查询
- [ ] 基础手机端上传功能
- [ ] 简单 PC 端浏览界面
- [ ] 接入 Claude 实现基础问答与诊断

### 未来阶段

**阶段 2：多模态与专家库**
- 图片 OCR/特征提取、向量检索、专家规则引擎、完整 Agent 工作流

**阶段 3：优化与扩展**
- 正式 PC 前端（React + Ant Design）、扩展专家规则库、性能优化、权限控制

## 技术栈演进

### MVP 阶段（当前）
- FastAPI + SQLAlchemy
- PostgreSQL + TimescaleDB + pgvector
- MinIO
- 轻量规则引擎（jsonlogic）
- 不引入额外 Agent 框架（使用 FastAPI 路由 + Python 函数 + Claude 工具调用）

### 阶段 2
- Qdrant（高性能向量库）
- LangGraph（工作流编排）
- Unstructured.io + PyMuPDF + PaddleOCR（多模态解析增强）

## 关键文档

- **PLAN.md** - 详细项目规划、数据模型、服务架构、实施路线
- **OPEN_SOURCE_RECOMMENDATIONS.md** - 开源技术栈选型与推荐
- **TECHNICAL_GUIDES.md** - 技术解析文档
- **README.md** - 项目概述与快速开始

## 开发注意事项

1. **单一技术栈优先** - 数据库优先采用 PostgreSQL + 扩展（TimescaleDB / pgvector）
2. **逐步引入复杂组件** - MVP 阶段只依赖核心组件，第二阶段再引入"重型组件"
3. **以数据中心为核心** - 所有组件围绕 `Asset` / `SensorData` / `ExpertRule` 等核心模型服务
4. **版本管理与溯源** - 每次重新解析/清洗/纠错都会生成新版本 `AssetStructuredPayload`
5. **统一数据格式** - Agent 使用统一的 `DataItem` 视图，不直接访问底层表结构
