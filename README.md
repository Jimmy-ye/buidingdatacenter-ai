# BDC-AI 建筑节能多模态数据中心与 Agent 平台

## 📋 项目简介

BDC-AI (Building Data Center AI) 是一个面向建筑节能诊断与能源管理的多模态"数据中心 + Agent + 专家库"平台。该平台旨在通过大模型（Claude 等）与工具链构建智能 Agent，自动处理建筑项目中的多模态资料（图片、表格、文本、音频、时序能耗数据等），结合专家知识库与历史案例，输出节能诊断和策略建议。

### 核心能力

- **多模态数据管理**: 统一管理项目相关的图片、表格、文本、音频、时序能耗数据
- **AI Agent 编排**: 封装大模型调用与工具链，实现自动化工作流
- **专家决策中心**: 基于专家知识与历史案例的规则引擎
- **多端接入**: 支持 PC 端分析决策、手机端现场采集、服务器统一调度

---

## 🏗️ 系统架构

### 技术栈（阶段 1 MVP）

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI 0.104.1 | 高性能异步 Web 框架 |
| 数据库 ORM | SQLAlchemy 2.0.23 | Python SQL 工具包和 ORM |
| 数据库 | PostgreSQL + TimescaleDB / SQLite | 关系型数据库 + 时序扩展（开发环境使用 SQLite） |
| 向量检索 | pgvector | PostgreSQL 向量扩展 |
| 对象存储 | 本地文件系统 / MinIO | 本地开发使用文件系统（生产环境 S3 兼容） |
| Web 服务器 | Uvicorn | ASGI 服务器 |
| OCR 引擎 | PaddleOCR 2.7.0.3 | 百度开源 OCR 工具包 |
| 深度学习框架 | PaddlePaddle 2.6.2 | PaddleOCR 后端 |
| PDF 处理 | PyMuPDF 1.26.7 | PDF 文档解析 |
| 测试框架 | Pytest | Python 测试框架 |

### 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                         客户端层                             │
├──────────────────────┬──────────────────────────────────────┤
│   PC Web UI          │    移动端 App / 小程序               │
│   (浏览器/Streamlit) │    (现场采集 + 上传)                 │
└──────────────────────┴──────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       API 网关 / 认证                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                        服务层 (FastAPI)                       │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Project  │  Asset   │TimeSeries│ AI Agent │ Expert Rule     │
│ Service  │ Service  │ Service  │Service   │ Service          │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                         数据层                                │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│ PostgreSQL   │ MinIO        │ pgvector     │ TimescaleDB     │
│ (元数据)     │ (文件存储)   │ (向量检索)   │ (时序数据)      │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 📁 项目结构

```
program-bdc-ai/
├── services/                      # 后端服务
│   └── backend/                   # 统一后端服务（阶段 1 MVP）
│       ├── app/
│       │   ├── api/               # API 路由
│       │   │   └── v1/
│       │   │       ├── health.py  # 健康检查接口
│       │   │       ├── projects.py # 项目管理接口
│       │   │       └── assets.py  # 资产管理接口（上传/OCR）
│       │   ├── schemas/           # Pydantic 模型
│       │   │   ├── project.py     # 项目 Schema
│       │   │   └── asset.py       # 资产 Schema
│       │   ├── services/          # 业务逻辑
│       │   │   └── image_pipeline.py  # 图片 OCR 流水线
│       │   └── main.py            # FastAPI 应用入口
│       └── requirements.txt       # Python 依赖
├── shared/                        # 共享代码
│   ├── config/                    # 配置管理
│   │   └── settings.py            # Settings 配置类
│   └── db/                        # 数据库
│       ├── base.py                # SQLAlchemy 声明式基类
│       ├── session.py             # 数据库会话管理
│       ├── models_project.py      # 项目相关模型
│       └── models_asset.py        # 资产相关模型
├── tests/                         # 测试目录
│   ├── integration/               # 集成测试
│   └── README.md                  # 测试文档
├── data/                          # 本地数据目录
│   ├── assets/                    # 上传的文件存储
│   └── bdc_ai.db                  # SQLite 数据库（开发环境）
├── .env                           # 环境变量配置（需创建）
├── view_ocr_results.py            # OCR 结果查看工具
├── PLAN.md                        # 项目详细规划文档
├── OPEN_SOURCE_RECOMMENDATIONS.md # 开源技术栈推荐
├── TECHNICAL_GUIDES.md            # 技术解析文档
└── README.md                      # 本文件
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 14+ （推荐）
- MinIO （可选，用于对象存储）

### 安装依赖

```bash
# 安装后端依赖
cd services/backend
pip install -r requirements.txt

# 或安装核心依赖
pip install fastapi uvicorn sqlalchemy
```

### 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 数据库连接 URL
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# MinIO 对象存储地址
BDC_MINIO_ENDPOINT=localhost:9000
```

### 启动服务

```bash
# 方式 1：使用 uvicorn 直接启动
python -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload

# 方式 2：从 backend 目录启动
cd services/backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload
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

### 当前可用接口

#### 1. 根路径
```http
GET /
```

**响应示例**:
```json
{
  "status": "ok"
}
```

#### 2. 健康检查
```http
GET /api/v1/health/
```

**响应示例**:
```json
{
  "status": "ok"
}
```

#### 3. 项目管理

**创建项目**
```http
POST /api/v1/projects/
Content-Type: application/json

{
  "name": "示例项目",
  "client": "客户名称",
  "location": "项目地址",
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

#### 4. 资产管理

**上传图片**
```http
POST /api/v1/assets/upload?project_id={uuid}&modality=image&source=mobile
Content-Type: multipart/form-data

file: <图片文件>
```

**触发 OCR 解析**
```http
POST /api/v1/assets/{asset_id}/parse_image
```

**查询资产列表**
```http
GET /api/v1/assets/?project_id={uuid}
```

### 即将实现的接口

- `/api/v1/buildings/` - 建筑管理
- `/api/v1/assets/{id}` - 资产详情查询
- `/api/v1/timeseries/` - 时序数据管理
- `/api/v1/analysis/` - AI 诊断分析
- `/api/v1/search/` - 多模态检索
- `/api/v1/rules/` - 专家规则管理

---

## 📊 核心数据模型

### 项目与空间模型

- **Project（项目）**: 项目基础信息、客户、位置、类型、状态
- **Building（建筑）**: 建筑名称、用途类型、建筑面积、建设年份、能效等级
- **Zone（区域）**: 楼层、房间、功能区域划分

### 系统与设备模型

- **System（系统）**: HVAC、照明、给排水、电梯等系统
- **Device（设备）**: 冷机、风机盘管、灯具等具体设备
- **SensorPoint（监测点）**: 电表、热量表、温度传感器等

### 多模态资产模型

- **Asset（资产）**: 统一抽象的多模态数据（图片、表格、文本、音频、文档）
- **FileBlob（文件）**: 原始文件物理存储信息
- **AssetStructuredPayload（结构化数据）**: 解析后的结构化内容
- **AssetFeature（特征）**: 向量特征，用于语义检索

### 任务与专家库

- **AnalysisTask（分析任务）**: 能耗基准、节能诊断、改造评估
- **AnalysisResult（分析结果）**: 诊断结论、策略建议、估算节能量
- **ExpertRule（专家规则）**: 节能诊断规则条件与推荐模板
- **CaseLibrary（案例库）**: 历史案例与效果数据

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
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试项目","client":"测试客户","location":"北京","status":"active"}'

# 2. 上传图片
curl -X POST "http://localhost:8000/api/v1/assets/upload?project_id=<uuid>&modality=image&source=test" \
  -F "file=@/path/to/image.jpg"

# 3. 触发 OCR 解析
curl -X POST http://localhost:8000/api/v1/assets/<asset_id>/parse_image
```

**查看 OCR 结果**：
```bash
# 使用查看工具
python view_ocr_results.py

# 或查看生成的 JSON 文件
cat latest_ocr_result.json
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
- **总耗时**：~4.2 秒/张（含分类）

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
- ✅ 完整业务流程测试（创建项目 → 上传 → OCR 解析）
- ✅ 数据库持久化验证

---

## 📈 开发路线图

### 阶段 1: MVP（4-6 周）- 当前阶段

- [x] 搭建基础后端架构
- [x] 实现健康检查接口
- [x] 实现项目管理（Project CRUD API）
- [x] 实现资产管理（Asset 上传 + OCR 解析）
- [x] 集成 PaddleOCR 图片识别
- [x] 实现第一层解析（OCR 文本提取）
- [ ] 实现 Building/Zone/System/Device 管理（部分完成）
- [ ] 接入 Claude 实现基础问答与诊断
- [ ] 简单 PC 端浏览界面

### 阶段 2: 多模态与专家库（下一阶段）

- [ ] 第二层解析（Claude Vision 多模态理解）
- [ ] 专家规则引擎（JSONLogic / 自研 DSL）
- [ ] Agent 工作流编排
- [ ] 向量检索实现（pgvector）
- [ ] 完整诊断流程：数据 → 规则 → 建议 → 报告

### 阶段 3: 优化与扩展

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
class Settings:
    def __init__(self) -> None:
        # 数据库连接 URL
        self.database_url = os.getenv(
            "BDC_DATABASE_URL",
            "postgresql://admin:password@localhost:5432/bdc_ai"
        )
        # MinIO 对象存储地址
        self.minio_endpoint = os.getenv("BDC_MINIO_ENDPOINT", "localhost:9000")
```

### 数据库会话

位于 `shared/db/session.py`，使用 SQLAlchemy 2.0 语法：

```python
from shared.db.session import get_db

# 依赖注入使用
@app.get("/api/v1/projects/")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects
```

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
- Claude AI 模型

---

**最后更新**: 2025-01-18
**当前版本**: 0.2.0
**开发状态**: MVP 阶段 - OCR 功能已完成
