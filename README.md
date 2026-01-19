# BDC-AI 建筑节能多模态数据中心与 Agent 平台

## 📋 项目简介

BDC-AI (Building Data Center AI) 是一个面向建筑节能诊断与能源管理的多模态"数据中心 + Agent + 专家库"平台。该平台通过大模型（GLM-4V、Claude 等）与工具链构建智能 Agent，自动处理建筑项目中的多模态资料（图片、表格、文本、音频、时序能耗数据等），结合专家知识库与历史案例，输出节能诊断和策略建议。

### 核心能力

- **多模态数据管理**: 统一管理项目相关的图片、表格、文本、音频、时序能耗数据
- **AI 智能分析**: 集成 PaddleOCR 和 GLM-4V 实现图片文本提取和场景问题智能诊断
- **自动化工作流**: Worker 后台自动处理待分析图片，生成结构化诊断报告
- **版本化管理**: 所有分析结果版本化存储，支持追溯和对比
- **多端接入**: 支持 PC 端分析决策、手机端现场采集、服务器统一调度

---

## 🏗️ 系统架构

### 技术栈

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 后端框架 | FastAPI | 0.104.1 | 高性能异步 Web 框架 |
| 数据库 ORM | SQLAlchemy | 2.0.23 | Python SQL 工具包和 ORM |
| 数据库 | PostgreSQL | 18.1 | 关系型数据库，支持 UUID、JSON |
| 数据库扩展 | pgvector | - | PostgreSQL 向量扩展（预留） |
| 数据库扩展 | TimescaleDB | - | 时序数据扩展（预留） |
| 对象存储 | 本地文件系统 | - | 本地开发使用（生产环境建议 MinIO） |
| Web 服务器 | Uvicorn | - | ASGI 服务器 |
| OCR 引擎 | PaddleOCR | 2.7.0.3 | 百度开源 OCR 工具包 |
| 深度学习框架 | PaddlePaddle | 2.6.2 | PaddleOCR 后端 |
| 视觉大模型 | GLM-4V | - | 智谱 AI 多模态大模型 |
| PDF 处理 | PyMuPDF | 1.26.7 | PDF 文档解析 |
| 测试框架 | Pytest | - | Python 测试框架 |

### 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                         客户端层                             │
├──────────────────────┬──────────────────────────────────────┤
│   PC Web UI          │    移动端 App / 小程序               │
│   (Swagger/Streamlit)│    (现场采集 + 上传)                 │
└──────────────────────┴──────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                         │
│                   (http://localhost:8000)                   │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Project  │  Asset   │  OCR     │ GLM-4V   │ Expert Rule     │
│ Service  │ Service  │ Service  │ Worker   │ Service (TODO)   │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                         数据层                                │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│ PostgreSQL   │ 本地文件     │ pgvector     │ TimescaleDB     │
│ 18.1         │ 存储         │ (预留)       │ (预留)          │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 📁 项目结构

```
program-bdc-ai/
├── services/                      # 后端服务
│   ├── backend/                   # FastAPI 后端服务
│   │   ├── app/
│   │   │   ├── api/               # API 路由
│   │   │   │   └── v1/
│   │   │   │       ├── health.py      # 健康检查
│   │   │   │       ├── projects.py    # 项目管理
│   │   │   │       └── assets.py      # 资产管理（上传/OCR/GLM）
│   │   │   ├── schemas/           # Pydantic 模型
│   │   │   ├── services/          # 业务逻辑
│   │   │   │   └── image_pipeline.py  # 图片处理流水线
│   │   │   └── main.py            # FastAPI 应用入口
│   │   └── requirements.txt       # Python 依赖
│   └── worker/                    # GLM Worker 后台服务
│       ├── scene_issue_glm_worker.py  # GLM-4V 场景问题分析
│       └── test_scene_issue_pipeline.py  # 完整流程测试
├── shared/                        # 共享代码
│   ├── config/
│   │   └── settings.py            # Settings 配置类
│   └── db/                        # 数据库
│       ├── base.py                # SQLAlchemy 声明式基类
│       ├── session.py             # 数据库会话管理
│       ├── models_project.py      # 项目相关模型
│       └── models_asset.py        # 资产相关模型
├── tests/                         # 测试目录
│   ├── integration/               # 集成测试
│   └── README.md
├── data/                          # 本地数据目录
│   ├── assets/                    # 上传的文件存储
│   └── bdc_ai.db                  # SQLite 数据库（已废弃，仅作备份）
├── docs/                          # 文档目录
│   ├── API_EXAMPLES.md            # API 使用示例
│   ├── POSTGRESQL_MIGRATION_ASSESSMENT.md  # 迁移评估
│   └── SQLITE_UUID_ISSUES.md      # UUID 问题记录
├── GUIDEBOOK/                     # 指南文档
│   ├── PLAN.md                    # 项目详细规划
│   ├── TECHNICAL_GUIDES.md        # 技术解析
│   └── OPEN_SOURCE_RECOMMENDATIONS.md  # 开源推荐
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量示例
├── README.md                      # 本文件
├── PROJECT_PROGRESS_SUMMARY.md    # 项目进度总结
├── POSTGRESQL_MIGRATION_SUMMARY.md  # PostgreSQL 迁移总结
└── GLM_WORKER_TEST_REPORT.md      # GLM Worker 测试报告
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 14+ （推荐 18.1）
- GLM API Key （用于场景问题分析）

### 安装依赖

```bash
# 安装后端依赖
cd services/backend
pip install -r requirements.txt

# 或安装核心依赖
pip install fastapi uvicorn sqlalchemy psycopg2-binary paddleocr python-dotenv openai
```

### 配置环境变量

创建 `.env` 文件（可参考 `.env.example`）：

```bash
# 数据库连接 URL
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# 本地文件存储目录
BDC_LOCAL_STORAGE_DIR=data/assets

# GLM API 配置（用于场景问题分析）
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v

# MinIO 对象存储（可选，生产环境推荐）
# BDC_MINIO_ENDPOINT=localhost:9000
# BDC_MINIO_ACCESS_KEY=minioadmin
# BDC_MINIO_SECRET_KEY=minioadmin
```

### 创建数据库

```bash
# 方式 1: 使用 SQL 脚本（Windows）
psql -U postgres -f create_postgres_db.sql

# 方式 2: 使用命令行
psql -U postgres
CREATE DATABASE bdc_ai OWNER admin;
GRANT ALL PRIVILEGES ON DATABASE bdc_ai TO admin;
```

### 启动服务

**启动后端服务**：
```bash
# 方式 1：从项目根目录启动
python -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload

# 方式 2：从 backend 目录启动
cd services/backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload
```

**启动 GLM Worker**（可选，用于自动场景问题分析）：
```bash
cd services/worker
python scene_issue_glm_worker.py
```

服务将在 `http://localhost:8000` 启动。

### 验证服务

```bash
# 测试根路径
curl http://localhost:8000/

# 测试健康检查
curl http://localhost:8000/api/v1/health/

# 预期响应
# {"status":"ok"}
```

### 访问 API 文档

启动服务后，在浏览器中访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 🔌 API 接口

### 核心接口

#### 1. 项目管理

**创建项目**
```http
POST /api/v1/projects/
Content-Type: application/json

{
  "name": "示例项目",
  "client": "客户名称",
  "location": "项目地址",
  "type": "办公楼",
  "status": "active"
}
```

**查询项目列表**
```http
GET /api/v1/projects/
```

**查询单个项目**
```http
GET /api/v1/projects/{project_id}
```

#### 2. 资产管理

**上传图片并触发 OCR**
```http
POST /api/v1/assets/upload_image_with_note?project_id={uuid}&modality=image&source=mobile&content_role=meter&auto_route=true
Content-Type: multipart/form-data

file: <图片文件>
note: "备注信息"
title: "图片标题"
```

**查询资产列表**
```http
GET /api/v1/assets/?project_id={uuid}&modality=image&content_role=scene_issue
```

**查询资产详情**
```http
GET /api/v1/assets/{asset_id}
```

**触发图片智能路由**
```http
POST /api/v1/assets/{asset_id}/route_image
```

**提交场景问题报告（GLM 分析结果）**
```http
POST /api/v1/assets/{asset_id}/scene_issue_report
Content-Type: application/json

{
  "title": "制冷系统效率低下",
  "issue_category": "冷源效率",
  "severity": "high",
  "summary": "冷却塔水位过高，导致换热效率下降",
  "suspected_causes": ["水位控制器故障", "水位传感器失灵"],
  "recommended_actions": ["更换水位控制器", "校准水位传感器"],
  "confidence": 0.8,
  "tags": ["冷却塔", "水位", "效率低下"]
}
```

#### 3. 健康检查

```http
GET /api/v1/health/
```

**响应示例**:
```json
{
  "status": "ok"
}
```

### 完整 API 列表

详见 Swagger 文档: http://localhost:8000/docs

---

## 🖼️ OCR 图片识别功能

### 功能特性

- **多语言支持**：中文、英文混合识别
- **高精度**：平均置信度 > 95%
- **结构化输出**：返回文本、坐标、置信度
- **自动版本管理**：每次解析生成新版本，保留历史

### 使用示例

**完整流程**：
```bash
# 1. 创建项目
PROJECT_ID=$(curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试项目","client":"测试客户","location":"北京","status":"active"}' \
  | jq -r '.id')

# 2. 上传图片（带备注，自动路由）
ASSET_ID=$(curl -X POST "http://localhost:8000/api/v1/assets/upload_image_with_note?project_id=$PROJECT_ID&modality=image&source=mobile&content_role=meter&auto_route=true" \
  -F "file=@/path/to/image.jpg" \
  -F "note=电表读数" \
  -F "title=电表照片" \
  | jq -r '.id')

# 3. 查询资产详情（含 OCR 结果）
curl http://localhost:8000/api/v1/assets/$ASSET_ID | jq
```

### OCR 数据结构

```json
{
  "image_meta": {
    "path": "data/assets/.../image.jpg"
  },
  "annotations": {
    "ocr_lines": [
      {
        "text": "识别的文本",
        "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
        "confidence": 0.98
      }
    ],
    "global_tags": []
  },
  "derived_text": "完整文本内容",
  "stats": {
    "avg_confidence": 0.967,
    "engine": "paddleocr"
  }
}
```

### 性能指标

- **检测速度**：~0.6 秒/张
- **识别速度**：~3.3 秒/张
- **总耗时**：~4.2 秒/张（含路由判断）

---

## 🤖 GLM-4V 场景问题分析

### 功能特性

- **智能问题诊断**：自动识别现场问题类别
- **严重程度评估**：low/medium/high 三级评估
- **原因分析**：提供可能的原因列表
- **建议措施**：给出具体的改进建议
- **置信度评分**：0.0-1.0 置信度

### Worker 自动处理

GLM Worker 会自动轮询待处理的图片（`content_role='scene_issue'` 且 `status=None`），调用 GLM-4V API 进行分析，并提交结果。

### 使用示例

```bash
# 上传场景问题图片
curl -X POST "http://localhost:8000/api/v1/assets/upload_image_with_note?project_id=$PROJECT_ID&modality=image&source=mobile&content_role=scene_issue" \
  -F "file=@/path/to/scene_issue.jpg" \
  -F "note=管道接口处有渗漏" \
  -F "title=管道漏水"

# Worker 会自动处理，或手动触发
curl -X POST http://localhost:8000/api/v1/assets/$ASSET_ID/route_image
```

### GLM 分析结果示例

```json
{
  "title": "制冷系统效率低下",
  "issue_category": "冷源效率",
  "severity": "high",
  "summary": "冷却塔水位过高，导致换热效率下降",
  "suspected_causes": [
    "水位控制器故障",
    "水位传感器失灵"
  ],
  "recommended_actions": [
    "更换水位控制器",
    "校准水位传感器"
  ],
  "confidence": 0.8,
  "tags": [
    "冷却塔",
    "水位",
    "效率低下"
  ]
}
```

### 性能指标

- **API 响应时间**：~10-30 秒
- **Worker 轮询间隔**：60 秒（可配置）

---

## 📊 核心数据模型

### 项目与空间模型

- **Project（项目）**: 项目基础信息、客户、位置、类型、状态
- **Building（建筑）**: 建筑名称、用途类型、建筑面积、建设年份、能效等级
- **Zone（区域）**: 楼层、房间、功能区域划分
- **BuildingSystem（系统）**: HVAC、照明、给排水、电梯等系统
- **Device（设备）**: 冷机、风机盘管、灯具等具体设备

### 多模态资产模型

- **Asset（资产）**: 统一抽象的多模态数据（图片、表格、文本、音频、文档）
- **FileBlob（文件）**: 原始文件物理存储信息
- **AssetStructuredPayload（结构化数据）**: 解析后的结构化内容（支持多版本）
- **AssetFeature（特征）**: 向量特征，用于语义检索（预留）

### 支持的模态类型

- `image` - 图片（含 OCR、目标检测）
- `table` - 表格（能耗日志、资产盘点、巡检记录等）
- `text` - 文本（现场记录、诊断结论等）
- `audio` - 音频（含 ASR 转写）
- `document` - 文档（PDF、Word 等，含章节结构）
- `timeseries_snapshot` - 时序数据快照

---

## 🧪 测试

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

### 测试覆盖

- ✅ 项目创建 API 测试
- ✅ Asset 上传 API 测试
- ✅ PaddleOCR 流水线测试
- ✅ GLM-4V 场景问题分析测试
- ✅ 完整业务流程测试（创建项目 → 上传 → OCR/GLM）
- ✅ PostgreSQL UUID 查询测试
- ✅ 数据库持久化验证

---

## 📈 开发路线图

### 阶段 1: MVP（已完成 85%）

- [x] 搭建基础后端架构
- [x] 实现健康检查接口
- [x] 实现项目管理（Project CRUD API）
- [x] 实现资产管理（Asset 上传 + OCR + GLM）
- [x] 集成 PaddleOCR 图片识别
- [x] 实现 OCR 文本提取（第一层解析）
- [x] 实现 GLM-4V 场景问题分析（第二层解析）
- [x] PostgreSQL 数据库迁移（SQLite → PostgreSQL 18.1）
- [x] GLM Worker 后台自动处理
- [ ] 实现 Building/Zone/System/Device 管理（部分完成，模型已有）
- [ ] 简单 PC 端浏览界面（Swagger 已可用）

### 阶段 2: 多模态与专家库（未开始）

- [ ] 专家规则引擎（JSONLogic / 自研 DSL）
- [ ] Agent 工作流编排（LangChain / 自研）
- [ ] 向量检索实现（pgvector）
- [ ] 完整诊断流程：数据 → 规则 → 建议 → 报告
- [ ] 时序数据管理（TimescaleDB）

### 阶段 3: 优化与扩展（未开始）

- [ ] 正式 PC 前端（React + Ant Design）
- [ ] 扩展专家规则库
- [ ] 手机端离线缓存
- [ ] 性能优化（异步处理、缓存）
- [ ] 权限控制与审计日志

---

## 🔧 配置说明

### Settings 配置类

位于 `shared/config/settings.py`，使用 `lru_cache` 实现单例模式：

```python
from shared.config.settings import get_settings

settings = get_settings()
print(settings.database_url)
```

### 数据库会话

位于 `shared/db/session.py`，使用 SQLAlchemy 2.0 语法：

```python
from shared.db.session import get_db
from sqlalchemy.orm import Session

@app.get("/api/v1/projects/")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects
```

---

## 📚 相关文档

- **PROJECT_PROGRESS_SUMMARY.md** - 项目进度总结
- **POSTGRESQL_MIGRATION_SUMMARY.md** - PostgreSQL 迁移总结
- **GLM_WORKER_TEST_REPORT.md** - GLM Worker 测试报告
- **GUIDEBOOK/PLAN.md** - 项目详细规划
- **GUIDEBOOK/TECHNICAL_GUIDES.md** - 技术解析文档
- **GUIDEBOOK/OPEN_SOURCE_RECOMMENDATIONS.md** - 开源技术栈推荐
- **docs/API_EXAMPLES.md** - API 使用示例

---

## 🤝 贡献指南

本项目目前处于初期开发阶段，欢迎贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

待定

---

## 📮 联系方式

项目相关问题，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 加入讨论组

---

## 🙏 致谢

- FastAPI 框架
- SQLAlchemy ORM
- PostgreSQL 数据库
- GLM-4V 视觉大模型（智谱 AI）
- PaddleOCR（百度）

---

**最后更新**: 2025-01-19
**当前版本**: 0.3.0
**开发状态**: MVP 阶段 - OCR + GLM 功能已完成，生产就绪
