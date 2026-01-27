# BDC-AI Worker 服务部署完成

## 部署时间
2026-01-25 15:20

## 部署状态
✅ **Worker 服务部署成功**

---

## 环境配置

### Python 环境
| 环境 | 路径 | Python 版本 | 用途 |
|------|------|------------|------|
| 主虚拟环境 | `D:\BDC-AI\venv` | 3.9.13 | 后端服务 |
| Worker 虚拟环境 | `D:\BDC-AI\venv311` | 3.11.9 | Worker 服务 |

**说明**：Worker 代码使用 `str \| None` 类型注解，需要 Python 3.10+，因此创建了独立的 Python 3.11 虚拟环境。

### 依赖安装
已安装到 `venv311`：
- ✅ requests >= 2.31.0
- ✅ openai >= 1.0.0 (2.15.0)
- ✅ Pillow >= 10.0.0 (12.1.0)
- ✅ python-dotenv (1.2.1)

---

## 配置文件

### 环境变量 (`.env`)
位置：`services\worker\.env`

```bash
# 后端连接
BDC_BACKEND_BASE_URL=http://localhost:8000

# 本地存储
BDC_LOCAL_STORAGE_DIR=../data/assets

# GLM API 配置
GLM_API_KEY=2534e2ce7188483d8eee5feca552f1b6.sskMwroqUers9UM7
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v

# Worker 配置
BDC_SCENE_WORKER_POLL_INTERVAL=60
```

---

## 启动脚本

### 1. 启动Worker.bat（推荐）
**位置**：`services\worker\启动Worker.bat`

**功能**：
- 自动检查 Python 版本
- 验证依赖安装
- 检查后端服务状态
- 显示配置信息
- 启动 Worker

**使用**：
```bash
# 双击运行
services\worker\启动Worker.bat

# 或命令行
cd services\worker
启动Worker.bat
```

### 2. 测试配置.bat
**位置**：`services\worker\测试配置.bat`

**功能**：
- 测试 Python 版本
- 验证依赖安装
- 检查环境变量
- 测试后端连接
- 验证 Worker 脚本

**使用**：
```bash
cd services\worker
测试配置.bat
```

---

## Worker 功能

### 工作流程
```
1. 轮询后端（每 60 秒）
   ↓
2. 查找 pending_scene_llm 状态的图片
   ↓
3. 调用 GLM-4V API 分析
   ↓
4. 回写分析结果
   ↓
5. 更新状态为 parsed_scene_llm
```

### 处理内容
- **图片类型**：现场问题照片（scene_issue）
- **AI 模型**：GLM-4V（智谱视觉大模型）
- **输出格式**：结构化 JSON 报告

### 分析结果示例
```json
{
  "schema_type": "scene_issue_report_v1",
  "payload": {
    "title": "管道保温层破损",
    "issue_category": "设备维护",
    "severity": "medium",
    "summary": "现场管道保温层存在明显破损...",
    "suspected_causes": [
      "保温材料老化",
      "外力损伤"
    ],
    "recommended_actions": [
      "更换破损保温层",
      "检查相邻管道"
    ],
    "confidence": 0.85,
    "tags": ["保温", "管道", "维护"]
  }
}
```

---

## 使用步骤

### 前提条件
1. ✅ 后端服务运行在 http://localhost:8000
2. ✅ Python 3.11 虚拟环境已创建
3. ✅ Worker 依赖已安装
4. ✅ GLM API Key 已配置

### 启动 Worker

**步骤 1**：启动后端服务（如果未启动）
```bash
cd D:\BDC-AI
scripts\Windows\启动后端服务.bat
```

**步骤 2**：测试 Worker 配置
```bash
cd services\worker
测试配置.bat
```

**步骤 3**：启动 Worker
```bash
启动Worker.bat
```

**步骤 4**：观察输出
```
========================================
GLM-4V Scene Issue Worker
========================================

Using Python 3.11 Virtual Environment
Python 3.11.9

Checking dependencies...
[OK] Dependencies installed

Checking backend service...
[OK] Backend service is running

========================================
Configuration:
- Backend: http://localhost:8000
- Poll interval: 60 seconds
- GLM Model: glm-4v
========================================

Press Ctrl+C to stop Worker

[2025-01-25 15:20:00] Starting GLM-4V Scene Issue Worker...
[2025-01-25 15:20:00] Backend: http://localhost:8000
[2025-01-25 15:20:00] Poll interval: 60 seconds
[2025-01-25 15:21:00] Checking for pending scene_issue assets...
[2025-01-25 15:21:00] No pending assets found
```

---

## 测试 Worker

### 方法 1：上传测试图片

```bash
# 1. 创建项目
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Worker 测试",
    "client": "测试",
    "location": "测试",
    "status": "active"
  }'

# 2. 上传图片（替换 {PROJECT_ID}）
curl -X POST "http://localhost:8000/api/v1/assets/upload_image_with_note?project_id={PROJECT_ID}&source=mobile&content_role=scene_issue&auto_route=true" \
  -F "file=@test.jpg" \
  -F "note=管道保温层破损"
```

### 方法 2：查看 Worker 处理结果

```bash
# Worker 自动处理后，查看结果
curl "http://localhost:8000/api/v1/assets/{ASSET_ID}"
```

---

## 文件结构

```
services/worker/
├── scene_issue_glm_worker.py    # Worker 主程序
├── requirements.txt              # 依赖列表
├── .env                         # 环境变量配置
├── .env.example                 # 配置模板
├── README.md                    # 说明文档
├── 启动Worker.bat                # 启动脚本 ⭐
├── 测试配置.bat                  # 测试脚本 ⭐
├── WORKER_DEPLOYMENT.md         # 部署文档
└── test_*.py                    # 测试脚本
```

---

## 监控与管理

### 查看运行状态
```bash
# 查看 Python 进程
tasklist | findstr python

# 查看网络连接
netstat -ano | findstr :8000
```

### 日志管理
当前输出到控制台，可重定向到文件：
```bash
启动Worker.bat > worker.log 2>&1
```

### 停止 Worker
在 Worker 窗口按 `Ctrl+C`

### 后台运行
```bash
start /B 启动Worker.bat > worker.log 2>&1
```

---

## Tailscale 远程部署

如需从 Tailscale 网络访问：

### 1. 修改 Worker 配置
```bash
# 编辑 .env
BDC_BACKEND_BASE_URL=http://100.93.101.76:8000
```

### 2. 在服务器上运行 Worker
```bash
cd services\worker
启动Worker.bat
```

### 3. Worker 自动处理后端任务
- 通过 Tailscale 连接后端
- 定期轮询待处理任务
- 处理完成后自动更新

---

## 常见问题

### Q: Worker 提示 "ModuleNotFoundError"
**A**:
```bash
# 重新安装依赖
D:\BDC-AI\venv311\Scripts\pip.exe install -r services/worker/requirements.txt
```

### Q: Worker 无法连接后端
**A**:
1. 确认后端服务运行：`curl http://localhost:8000/api/v1/health`
2. 检查 .env 中的 BDC_BACKEND_BASE_URL
3. 检查防火墙设置

### Q: GLM API 调用失败
**A**:
1. 检查 API Key 是否正确
2. 确认网络可以访问 open.bigmodel.cn
3. 检查 API 额度是否充足

### Q: Worker 没有处理任务
**A**:
1. 确认上传图片时使用了 `content_role=scene_issue`
2. 检查资产状态是否为 `pending_scene_llm`
3. 查看 Worker 日志输出

---

## 维护建议

### 日常检查
- [ ] Worker 进程是否运行
- [ ] 后端服务是否正常
- [ ] GLM API 额度是否充足
- [ ] 磁盘空间是否充足

### 日志管理
建议定期备份日志文件：
```bash
# 创建带时间戳的日志
copy worker.log worker_%date:~0,10%.log
```

### 更新流程
1. 停止 Worker
2. 拉取最新代码：`git pull`
3. 更新依赖：`pip install -r requirements.txt`
4. 重新启动 Worker

---

## 总结

✅ **Worker 服务已完全部署**

| 项目 | 状态 |
|------|------|
| Python 3.11 虚拟环境 | ✅ 已创建 |
| 依赖安装 | ✅ 已完成 |
| 环境配置 | ✅ 已设置 |
| 启动脚本 | ✅ 已创建 |
| 测试脚本 | ✅ 已创建 |
| 文档 | ✅ 已完成 |

---

## 下一步

1. **启动后端服务**：`scripts\Windows\启动后端服务.bat`
2. **测试配置**：`services\worker\测试配置.bat`
3. **启动 Worker**：`services\worker\启动Worker.bat`
4. **上传测试图片**验证功能

---

**部署完成！** 🎉

Worker 服务已就绪，可以开始处理现场问题图片分析任务。

详细文档：`services\worker\WORKER_DEPLOYMENT.md`
