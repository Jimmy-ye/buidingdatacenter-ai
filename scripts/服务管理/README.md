# BDC-AI 服务管理脚本

**最后更新**: 2026-01-25

---

## 📋 脚本列表

### 后端服务管理

| 脚本 | 说明 | 使用方式 |
|------|------|----------|
| `启动后端服务.bat` | 启动 FastAPI 后端服务 | 双击运行 |
| `监控后端服务.py` | 实时监控后端服务状态 | Python 脚本 |
| `启动服务监控.bat` | 启动监控工具 | 双击运行 |

### Worker 服务管理

| 脚本 | 说明 | 使用方式 |
|------|------|----------|
| `启动Worker.bat` | 启动 GLM-4V Worker（Python 3.11） | 双击运行 |
| `启动Worker_Python311.bat` | 启动 Worker（Python 3.11 专用） | 双击运行 |
| `启动Worker测试.bat` | 测试 Worker 配置 | 双击运行 |
| `测试配置.bat` | 验证 Worker 环境配置 | 双击运行 |
| `监控Worker.bat` | 监控 Worker 运行状态 | 双击运行 |

---

## 🚀 快速启动

### 启动后端服务

```bash
# 双击运行
scripts\服务管理\启动后端服务.bat

# 或命令行
cd D:\BDC-AI
venv\Scripts\python.exe -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动 Worker 服务

```bash
# 双击运行
scripts\服务管理\启动Worker.bat

# 或命令行
cd D:\BDC-AI\services\worker
D:\BDC-AI\venv311\Scripts\python.exe scene_issue_glm_worker.py
```

### 启动监控

```bash
# 监控后端
scripts\服务管理\启动服务监控.bat

# 监控 Worker
scripts\服务管理\监控Worker.bat
```

---

## 📊 服务架构

```
BDC-AI 系统服务
│
├── 后端服务（FastAPI）
│   ├── 端口: 8000
│   ├── Python: 3.9 (venv)
│   └── 监听: 0.0.0.0
│
└── Worker 服务（GLM-4V）
    ├── 端口: -
    ├── Python: 3.11 (venv311)
    └── 轮询间隔: 60 秒
```

---

## 🔧 配置说明

### 后端服务配置

**环境变量**: `.env`
```bash
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai
BDC_LOCAL_STORAGE_DIR=data/assets
GLM_API_KEY=your_api_key_here
```

**启动参数**:
```bash
--host 0.0.0.0       # 允许外部访问
--port 8000          # 监听端口
--reload             # 自动重载（开发模式）
```

### Worker 服务配置

**环境变量**: `services/worker/.env`
```bash
BDC_BACKEND_BASE_URL=http://localhost:8000
GLM_API_KEY=your_glm_api_key_here
BDC_SCENE_WORKER_POLL_INTERVAL=60
```

**Python 版本要求**: Python 3.11+（需要支持 `str | None` 类型注解）

---

## 🧪 测试脚本

### 后端测试

```bash
# 测试图片路由
cd services/backend
python test_image_routing_smoke.py
```

### Worker 测试

```bash
# 测试场景处理流程
python scripts/测试/test_scene_issue_pipeline.py

# 测试 Worker 工作流
python scripts/测试/test_worker_flow.py
```

---

## 📝 服务检查清单

### 启动前检查

- [ ] PostgreSQL 服务运行中
- [ ] 数据库 `bdc_ai` 已创建
- [ ] 虚拟环境已创建（venv 和 venv311）
- [ ] 依赖已安装
- [ ] 环境变量已配置

### 后端服务检查

- [ ] 服务启动成功
- [ ] 端口 8000 监听正常
- [ ] 健康检查返回 OK
- [ ] API 文档可访问

### Worker 服务检查

- [ ] Python 3.11 环境正常
- [ ] 依赖安装完整
- [ ] 环境变量配置正确
- [ ] 后端连接成功
- [ ] GLM API 可用

---

## 🔍 故障排查

### 后端服务无法启动

**问题**: 端口被占用
```bash
# 查找占用进程
netstat -ano | findstr :8000

# 终止进程
taskkill /PID <PID> /F
```

**问题**: 数据库连接失败
```bash
# 检查 PostgreSQL 服务
# Windows 服务管理器 → PostgreSQL 18

# 测试连接
psql -U admin -d bdc_ai
```

### Worker 无法启动

**问题**: Python 版本不兼容
```bash
# 检查版本
venv311\Scripts\python.exe --version
# 应该是 Python 3.11.x

# 重新安装依赖
venv311\Scripts\pip.exe install -r services/worker/requirements.txt
```

**问题**: 后端连接失败
```bash
# 测试后端服务
curl http://localhost:8000/api/v1/health

# 检查 .env 配置
# BDC_BACKEND_BASE_URL=http://localhost:8000
```

### 监控工具无响应

**问题**: 脚本编码错误
```bash
# 使用英文版启动脚本
scripts\服务管理\start_monitor.bat

# 或直接运行 Python
venv\Scripts\python.exe scripts\Windows/监控后端服务.py
```

---

## 📚 相关文档

### 部署文档
- **README.md** - 项目总览
- **部署完成总结.md** - 系统部署总结
- **TAILSCALE通讯指南.md** - 远程访问配置

### 技术文档
- **后端服务器部署完整指南.md** - 后端部署文档
- **Worker 部署指南** - Worker 部署文档

### 使用文档
- **快速设置指南** - 快速上手
- **API 使用指南** - API 开发指南

---

## 🎯 日常工作流程

### 启动所有服务

```bash
# 1. 启动后端服务
scripts\服务管理\启动后端服务.bat

# 2. 启动 Worker 服务（新窗口）
scripts\服务管理\启动Worker.bat

# 3. 启动监控（新窗口）
scripts\服务管理\启动服务监控.bat
```

### 停止所有服务

```bash
# 在各个服务窗口按 Ctrl+C

# 或查找并终止 Python 进程
tasklist | findstr python
taskkill /PID <PID> /F
```

### 查看服务状态

```bash
# 查看端口占用
netstat -ano | findstr :8000

# 查看进程
tasklist | findstr python

# 测试服务
curl http://localhost:8000/api/v1/health
```

---

**服务管理脚本已集中管理！** 🚀
