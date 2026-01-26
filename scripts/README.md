# Scripts 脚本工具集

**最后更新**: 2026-01-25

---

## 📂 目录结构

```
scripts/
├── Windows/              # Windows 平台脚本
│   ├── 启动后端服务.bat
│   ├── 监控后端服务.py
│   └── 启动服务监控.bat
│
├── Linux/                # Linux 平台脚本
│   └── (待添加)
│
├── 数据库/               # 数据库管理脚本
│   ├── 初始化数据库.py
│   ├── 创建管理员用户.py
│   ├── 初始化认证数据库.py
│   └── 检查外键约束.py
│
├── 服务管理/            # 服务启动和管理脚本
│   ├── README.md
│   ├── 启动Worker.bat
│   ├── 启动Worker_Python311.bat
│   ├── 启动Worker测试.bat
│   ├── 测试配置.bat
│   └── 监控Worker.bat
│
├── 测试/                # 正式测试脚本
│   ├── README.md
│   ├── test_image_routing_smoke.py
│   ├── test_scene_issue_pipeline.py
│   └── test_worker_flow.py
│
├── 调试工具/            # 开发调试工具（新增）
│   ├── README.md
│   ├── check_assets_status.py
│   ├── check_db_payloads.py
│   ├── check_new_asset.py
│   ├── check_worker_status.py
│   ├── manual_update_status.py
│   ├── rerun_project_images.py
│   ├── update_asset_status.py
│   ├── test_engineer_note.py
│   ├── test_single_meter.py
│   └── upload_meter_with_auto_route.py
│
└── 通用/                # 通用工具脚本
    ├── README.md
    ├── 快速设置指南.md
    ├── 清理测试项目.py
    └── 配置API密钥.py
```

---

## 🚀 快速开始

### 启动后端服务

```bash
# Windows
scripts\Windows\启动后端服务.bat

# 或手动启动
cd D:\BDC-AI
venv\Scripts\python.exe -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动 Worker 服务

```bash
# Windows
scripts\服务管理\启动Worker.bat
```

### 初始化数据库

```bash
# 自动初始化
python scripts/数据库/初始化数据库.py

# 创建管理员用户
python scripts/数据库/创建管理员用户.py
```

---

## 📋 脚本分类说明

### 1. 平台脚本 (Windows/, Linux/)

**用途**: 特定平台的启动和管理脚本

**主要脚本**:
- `启动后端服务.bat` - 启动 FastAPI 后端
- `监控后端服务.py` - 实时监控服务状态
- `启动服务监控.bat` - 启动监控工具

### 2. 数据库脚本 (数据库/)

**用途**: 数据库初始化、用户管理、维护

**主要脚本**:
- `初始化数据库.py` - 创建数据库和表结构
- `创建管理员用户.py` - 创建管理员账户
- `初始化认证数据库.py` - 初始化认证相关表
- `检查外键约束.py` - 检查数据库外键

### 3. 服务管理 (服务管理/)

**用途**: Worker 服务的启动、配置和监控

**主要脚本**:
- `启动Worker.bat` - 启动 GLM-4V Worker
- `测试配置.bat` - 验证 Worker 配置
- `监控Worker.bat` - 监控 Worker 运行状态

详细说明: [服务管理/README.md](服务管理/README.md)

### 4. 测试脚本 (测试/)

**用途**: 自动化测试、功能验证

**主要脚本**:
- `test_image_routing_smoke.py` - 后端图片路由测试
- `test_scene_issue_pipeline.py` - Worker 场景处理测试
- `test_worker_flow.py` - Worker 工作流测试

详细说明: [测试/README.md](测试/README.md)

### 5. 调试工具 (调试工具/)

**用途**: 开发过程中的快速状态检查和问题排查

**主要脚本**:
- `check_assets_status.py` - 查询项目下所有资产状态
- `check_worker_status.py` - 检查 Worker 进程状态
- `manual_update_status.py` - 手动更新资产状态
- `rerun_project_images.py` - 批量重新处理图片
- `check_db_payloads.py` - 检查资产数据存储
- `test_engineer_note.py` - 测试工程师备注功能

详细说明: [调试工具/README.md](调试工具/README.md)

### 6. 通用工具 (通用/)

**用途**: 通用工具和配置

**主要脚本**:
- `配置API密钥.py` - 配置 GLM API Key
- `清理测试项目.py` - 清理测试数据
- `快速设置指南.md` - 快速上手文档

详细说明: [通用/README.md](通用/README.md)

---

## 🛠️ 常用操作

### 日常开发

```bash
# 1. 启动后端服务
scripts\Windows\启动后端服务.bat

# 2. 启动 Worker（新窗口）
scripts\服务管理\启动Worker.bat

# 3. 启动监控（新窗口）
scripts\Windows\启动服务监控.bat
```

### 数据库维护

```bash
# 初始化数据库
python scripts/数据库/初始化数据库.py

# 创建管理员
python scripts/数据库/创建管理员用户.py

# 检查外键
python scripts/数据库/检查外键约束.py
```

### 配置管理

```bash
# 配置 API 密钥
python scripts/通用/配置API密钥.py

# 清理测试数据
python scripts/通用/清理测试项目.py
```

### 测试验证

```bash
# 后端测试
python scripts/测试/test_image_routing_smoke.py

# Worker 测试
python scripts/测试/test_worker_flow.py
```

### 调试工具

```bash
# 检查资产状态
python scripts/调试工具/check_assets_status.py

# 检查 Worker 状态
python scripts/调试工具/check_worker_status.py

# 手动更新资产状态
python scripts/调试工具/manual_update_status.py
```

---

## 📝 脚本开发规范

### 命名规范

- **中文脚本**: 使用中文名称，清晰描述功能
- **英文脚本**: 使用小写字母和下划线
- **批处理文件**: 使用 `.bat` 扩展名（Windows）
- **Python 脚本**: 使用 `.py` 扩展名

### 文件头注释

```python
"""
脚本名称
功能描述
作者: XXX
日期: YYYY-MM-DD
"""
```

### 编码规范

```python
# 设置 UTF-8 编码（解决 Windows 中文显示问题）
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 错误处理

```python
try:
    # 主要逻辑
    pass
except Exception as e:
    print(f"[ERROR] {str(e)}")
    sys.exit(1)
```

---

## 🔧 脚本依赖

### Python 版本要求

| 脚本类型 | Python 版本 | 虚拟环境 |
|---------|------------|---------|
| 后端相关脚本 | 3.9+ | venv |
| Worker 相关脚本 | 3.11+ | venv311 |
| 数据库脚本 | 3.9+ | venv |
| 通用脚本 | 3.9+ | venv |

### 依赖安装

```bash
# 后端依赖
venv\Scripts\pip.exe install -r services/backend/requirements.txt

# Worker 依赖
venv311\Scripts\pip.exe install -r services/worker/requirements.txt

# 通用依赖
venv\Scripts\pip.exe install requests python-dotenv psycopg2-binary
```

---

## 📊 使用统计

### 脚本使用频率

| 脚本类型 | 使用频率 | 说明 |
|---------|---------|------|
| 启动后端服务 | 每日多次 | 开发必需 |
| 启动 Worker | 每日 1-2 次 | 图片处理 |
| 初始化数据库 | 部署时 | 一次性 |
| 配置 API 密钥 | 配置时 | 一次性 |
| 测试脚本 | 发布前 | 质量保证 |

### 维护状态

| 脚本 | 状态 | 维护者 |
|------|------|--------|
| 启动后端服务.bat | ✅ 活跃 | Jimmy |
| 监控后端服务.py | ✅ 活跃 | Jimmy |
| 启动Worker.bat | ✅ 活跃 | Jimmy |
| 初始化数据库.py | ✅ 稳定 | Jimmy |
| 配置API密钥.py | ✅ 稳定 | Jimmy |

---

## 🐛 已知问题和限制

### Windows 编码问题

**问题**: 中文路径和输出可能显示乱码

**解决方案**:
```batch
@echo off
chcp 65001 >nul
```

### 路径问题

**问题**: 相对路径在不同位置运行时可能出错

**解决方案**:
```python
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
```

### 权限问题

**问题**: 某些脚本需要管理员权限

**解决方案**: 右键 "以管理员身份运行"

---

## 📚 相关文档

- **项目 README**: `../README.md`
- **部署指南**: `../docs/02-技术文档/后端服务器部署完整指南.md`
- **Tailscale 指南**: `../TAILSCALE通讯指南.md`

---

## 🔄 更新日志

### 2026-01-26

- ✅ 整合 tests/scripts 文件夹到 scripts/调试工具/
- ✅ 创建独立的调试工具分类
- ✅ 更新文档结构和说明
- ✅ 添加调试工具使用示例

### 2026-01-25

- ✅ 整合 services 文件夹脚本到 scripts
- ✅ 创建服务管理和测试文件夹
- ✅ 添加脚本分类和组织
- ✅ 更新文档结构

---

**脚本工具集已完整组织！** 🎯
