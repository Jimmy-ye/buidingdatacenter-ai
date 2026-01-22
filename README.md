# BDC-AI 建筑节能多模态数据中心与 Agent 平台

## 📋 项目简介

BDC-AI (Building Data Center AI) 是一个面向建筑节能诊断与能源管理的多模态"数据中心 + Agent + 专家库"平台。该平台通过大模型（GLM-4V、Claude 等）与工具链构建智能 Agent，自动处理建筑项目中的多模态资料（图片、表格、文本、音频、时序能耗数据等），结合专家知识库与历史案例，输出节能诊断和策略建议。

### 核心能力

- **🏗️ 工程结构管理**: 完整的 Project/Building/Zone/System/Device 层级管理，支持树形结构视图和多维度查询
- **🖥️ PC 端可视化界面**: 基于 NiceGUI 3.5.0 的桌面应用，支持工程结构树浏览、资产列表、图片预览和 OCR/LLM 结果查看 ✨
- **📱 多模态数据管理**: 统一管理项目相关的图片、表格、文本、音频、时序能耗数据
- **🔗 智能关联**: Asset 资产与工程结构自动双向关联，支持从任意工程节点查询相关资料
- **🤖 AI 智能分析**: 集成 PaddleOCR 和 GLM-4V 实现图片文本提取和场景问题智能诊断
- **⚙️ 自动化工作流**: Worker 后台自动处理待分析图片，生成结构化诊断报告
- **🏷️ 灵活标签系统**: JSONB 标签支持，方便业务分类和检索
- **📝 版本化管理**: 所有分析结果版本化存储，支持追溯和对比

---

## 🏗️ 系统架构

### 技术栈

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 后端框架 | FastAPI | 0.104.1 | 高性能异步 Web 框架 |
| PC UI | NiceGUI | 3.5.0 | Python 原生 UI 框架 ✨ |
| 数据库 ORM | SQLAlchemy | 2.0.23 | Python SQL 工具包和 ORM |
| 数据库 | PostgreSQL | 18.1 | 关系型数据库，支持 UUID、JSON |
| 数据库扩展 | pgvector | - | PostgreSQL 向量扩展（预留） |
| 数据库扩展 | TimescaleDB | - | 时序数据扩展（预留） |
| 对象存储 | 本地文件系统 | - | 本地开发使用（生产环境建议 MinIO） |
| Web 服务器 | Uvicorn | - | ASGI 服务器 |
| OCR 引擎 | PaddleOCR | 2.7.0.3 | 百度开源 OCR 工具包 |
| 深度学习框架 | PaddlePaddle | 2.6.2 | PaddleOCR 后端 |
| 视觉大模型 | GLM-4V | - | 智谱 AI 多模态大模型 |
| PDF 处理 | PyMuPDF | 1.23.26 | PDF 文档解析 |
| 测试框架 | Pytest | - | Python 测试框架 |
| 树形结构 | bigtree | 0.16.4 | Python 树形结构处理库 |

### 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                         客户端层                             │
├──────────────────────┬──────────────────────────────────────┤
│   PC Web UI          │    移动端 App / 小程序               │
│   (NiceGUI 3.5.0)   │    (现场采集 + 上传)                 │
│   桌面分析决策界面   │                                      │
└──────────────────────┴──────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                         │
│                   (http://localhost:8000)                   │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Project  │Engineering│ Asset   │  OCR     │ GLM-4V          │
│ Service  │ Service  │ Service  │ Service  │ Worker          │
│          │(Building/│          │          │                 │
│          │Zone/     │          │          │                 │
│          │System/   │          │          │                 │
│          │Device)   │          │          │                 │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                         数据层                                │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│ PostgreSQL   │ 本地文件     │ pgvector     │ TimescaleDB     │
│ 18.1         │ 存储         │ (预留)       │ (预留)          │
│ (UUID/JSONB) │             │              │                 │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 📁 项目结构

```
program-bdc-ai/
├── desktop/                       # PC 桌面应用 ✨
│   └── nicegui_app/
│       └── pc_app.py            # NiceGUI PC 端主程序
├── services/                     # 后端服务
│   ├── backend/                 # FastAPI 后端服务
│   │   ├── app/
│   │   │   ├── api/             # API 路由
│   │   │   │   └── v1/
│   │   │   │       ├── health.py       # 健康检查
│   │   │   │       ├── projects.py    # 项目管理
│   │   │   │       ├── engineering.py # 工程结构管理 ✨
│   │   │   │       └── assets.py      # 资产管理（上传/OCR/GLM）
│   │   │   ├── schemas/         # Pydantic 模型
│   │   │   │   ├── asset.py
│   │   │   │   └── engineering.py  # 工程结构模型 ✨
│   │   │   ├── services/        # 业务逻辑
│   │   │   │   ├── image_pipeline.py  # 图片处理流水线
│   │   │   │   └── tree_service.py    # 树形结构服务 ✨
│   │   │   └── main.py          # FastAPI 应用入口
│   │   └── requirements.txt     # Python 依赖
│   └── worker/                  # GLM Worker 后台服务
│       ├── scene_issue_glm_worker.py  # GLM-4V 场景问题分析
│       └── test_scene_issue_pipeline.py  # 完整流程测试
├── shared/                       # 共享代码
│   ├── config/
│   │   └── settings.py         # Settings 配置类
│   └── db/                     # 数据库
│       ├── base.py             # SQLAlchemy 声明式基类
│       ├── session.py          # 数据库会话管理
│       ├── models_project.py   # 项目相关模型（含工程结构）
│       └── models_asset.py    # 资产相关模型
├── data/                        # 本地数据目录
│   └── assets/                # 上传的文件存储
├── docs/                       # 文档目录
│   ├── 00-项目总览/
│   │   ├── README.md           # 项目总览
│   │   ├── 项目总结.md         # 项目进度总结 ✨
│   │   └── 项目规划.md         # 项目规划文档
│   ├── 01-开发指南/
│   │   ├── 工程结构测试指南.md # 测试指南 ✨
│   │   ├── Asset与工程结构测试指南.md # 集成测试指南 ✨
│   │   └── API使用示例.md      # API 使用示例
│   ├── 02-技术文档/
│   │   ├── 工程结构API设计.md  # API 设计文档 ✨
│   │   ├── 技术指南.md         # 技术深度解析
│   │   ├── 技术栈选型.md       # 技术栈选型
│   │   └── 表格处理管道设计.md  # 表格处理设计
│   ├── 03-优化记录/
│   │   ├── pc-ui-enhancement-plan.md # PC UI 优化方案 ✨
│   │   └── pc-ui-layout-optimization.md # PC UI 布局优化 ✨
│   └── 04-迁移记录/
│       ├── PostgreSQL迁移总结.md # 迁移记录 ✨
│       └── 项目清理与安全加固总结.md # 安全总结 ✨
├── .env                        # 环境变量配置
├── .env.example               # 环境变量示例
├── README.md                  # 本文件
└── CLAUDE.md                  # Claude AI 开发指南 ✨
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
pip install fastapi uvicorn sqlalchemy psycopg2-binary paddleocr python-dotenv openai nicegui
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
# 从项目根目录启动
python -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload
```

**启动 PC UI**：
```bash
# 启动桌面应用
python desktop/nicegui_app/pc_app.py
```

**启动 GLM Worker**（可选，用于自动场景问题分析）：
```bash
cd services/worker
python scene_issue_glm_worker.py
```

### 访问界面

- **后端 API**: http://localhost:8000
- **PC UI**: http://localhost:8080
- **Swagger 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

---

## 🖥️ PC UI 功能特性

### 核心功能

1. **项目管理条** ✨
   - 顶部项目选择器，快速切换不同项目
   - 实时加载项目列表
   - 自动加载选中项目的工程结构树

2. **工程结构树**
   - 左侧树形结构展示 Building → System → Device 层级
   - 点击节点加载对应资产列表
   - Zone 作为独立节点显示

3. **资产管理**
   - 表格视图展示资产列表
   - 支持按 device_id 过滤
   - 点击行显示资产详情

4. **资产详情面板**
   - 基础信息：标题、类型、采集时间、描述
   - 图片预览：支持大图预览对话框
   - OCR/LLM 识别结果：
     - 表具类型：只显示 LLM 分析结果
     - 其他类型：显示 OCR 详细信息 + LLM 分析

5. **智能提示**
   - 操作反馈通知（成功/失败/警告）
   - 加载状态提示
   - 错误处理提示

### 技术亮点

- **懒加载优化**: 图片组件设置 `loading=eager` 避免浏览器懒加载问题
- **按需加载**: 点击资产时调用详情 API 获取完整数据
- **双表模式**: List API + Detail API 分离，提升性能
- **响应式布局**: 自适应窗口大小

---

## 🔌 API 接口

### 核心接口

#### 0. 工程结构管理 ✨

**创建建筑**
```http
POST /api/v1/projects/{project_id}/buildings
Content-Type: application/json

{
  "name": "A座办公楼",
  "usage_type": "office",
  "floor_area": 8000.0,
  "gfa_area": 8000.0,
  "year_built": 2018
}
```

**创建区域/楼层**
```http
POST /api/v1/buildings/{building_id}/zones
Content-Type: application/json

{
  "name": "5F办公区",
  "type": "office"
}
```

**创建系统**
```http
POST /api/v1/buildings/{building_id}/systems
Content-Type: application/json

{
  "type": "HVAC",
  "name": "HVAC系统",
  "description": "空调系统"
}
```

**创建设备**
```http
POST /api/v1/systems/{system_id}/devices
Content-Type: application/json

{
  "zone_id": "uuid",
  "device_type": "fcu",
  "model": "风机盘管FCU-03",
  "rated_power": 1.5,
  "serial_no": "FCU-03"
}
```

**获取项目工程结构树**
```http
GET /api/v1/projects/{project_id}/structure_tree
```

**扁平化设备查询**
```http
GET /api/v1/projects/{project_id}/devices/flat?device_type=fcu&min_rated_power=1.0&tags=高能耗
```

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

#### 2. 资产管理

**上传图片并触发 OCR**
```http
POST /api/v1/assets/upload_image_with_note?project_id={uuid}&modality=image&content_role=meter
Content-Type: multipart/form-data

file: <图片文件>
note: "备注信息"
title: "图片标题"
```

**查询资产列表**
```http
GET /api/v1/assets/?device_id={uuid}
```

**查询资产详情**
```http
GET /api/v1/assets/{asset_id}
```

#### 3. 健康检查

```http
GET /api/v1/health/
```

### 完整 API 列表

详见 Swagger 文档: http://localhost:8000/docs

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定标记的测试
pytest tests/ -m integration
```

### 测试覆盖

- ✅ 项目创建 API 测试
- ✅ 工程结构 CRUD 测试（Building/Zone/System/Device）✨
- ✅ 工程结构树视图测试 ✨
- ✅ Asset-工程结构双向关联测试 ✨
- ✅ PC UI 功能测试 ✨
- ✅ PostgreSQL 数据库迁移验证

---

## 📈 开发路线图

### 阶段 1: MVP（已完成 95% ✨）

- [x] 搭建基础后端架构
- [x] 实现健康检查接口
- [x] 实现项目管理（Project CRUD API）
- [x] **实现工程结构管理（Building/Zone/System/Device CRUD）✨**
- [x] **实现工程结构树视图（bigtree）✨**
- [x] **实现 Asset ↔ 工程结构双向关联 ✨**
- [x] **实现 PC 端可视化界面（NiceGUI）✨**
- [x] **实现项目管理条功能 ✨**
- [x] **实现图片预览功能（修复懒加载问题）✨**
- [x] **实现表具类型智能 LLM 结果展示 ✨**
- [x] **支持 JSONB tags 字段 ✨**
- [x] 实现资产管理（Asset 上传 + OCR + GLM）
- [x] 集成 PaddleOCR 图片识别
- [x] 实现 GLM-4V 场景问题分析
- [x] PostgreSQL 数据库迁移（SQLite → PostgreSQL 18.1）
- [x] GLM Worker 后台自动处理
- [x] 完整测试框架
- [ ] 表格流水线（下一步优先级 1）
- [ ] 诊断问题清单（下一步优先级 2）
- [ ] Claude/问答入口（下一步优先级 3）

### 阶段 2: 多模态与专家库（未开始）

- [ ] 表格解析与统计指标
- [ ] 专家规则引擎
- [ ] Agent 工作流编排
- [ ] 向量检索实现（pgvector）
- [ ] 时序数据管理（TimescaleDB）

### 阶段 3: 优化与扩展（未开始）

- [ ] 正式 Web 前端（React + Ant Design）
- [ ] 扩展专家规则库
- [ ] 性能优化（异步处理、缓存）
- [ ] 权限控制与审计日志

---

## 📚 相关文档

### 📖 项目文档（已中文化 ✨）

**docs/ 目录**：
- **00-项目总览/** - 项目总览和规划
- **01-开发指南/** - 开发指南和测试文档
- **02-技术文档/** - 技术深度解析

### 🔗 快速链接

- 快速了解项目 → **docs/00-项目总览/项目规划.md**
- PC UI 优化方案 → **docs/03-优化记录/pc-ui-enhancement-plan.md**
- API 接口设计 → **docs/02-技术文档/工程结构API设计.md**
- 测试指南 → **docs/01-开发指南/工程结构测试指南.md**

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
- NiceGUI UI 框架
- SQLAlchemy ORM
- PostgreSQL 数据库
- GLM-4V 视觉大模型（智谱 AI）
- PaddleOCR（百度）

---

**最后更新**: 2026-01-21
**当前版本**: 1.0.0
**开发状态**: MVP 阶段 - PC 端可视化界面已完成，95% 完成度 ✨

**核心里程碑**:
- ✅ PostgreSQL 18.1 迁移完成
- ✅ 工程结构管理 API 100% 完成
- ✅ Asset ↔ 工程结构双向关联 100% 完成
- ✅ PC 端可视化界面（NiceGUI）100% 完成 ✨
- ✅ 图片预览功能优化 100% 完成 ✨
- ✅ 文档体系全面优化（中文化）
- 🚀 下一步：表格流水线 / 诊断清单 / Claude 问答入口
