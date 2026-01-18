# GLM-4V Scene Issue Worker

基于 GLM-4V 视觉大模型的现场问题分析 Worker，自动处理 `content_role=scene_issue` 的图片资产。

## 功能说明

Worker 会轮询后端服务，查找状态为 `pending_scene_llm` 的 scene_issue 图片，然后：

1. 从本地存储目录读取图片文件
2. 调用 GLM-4V API 进行视觉分析
3. 将分析结果规范化并回写到后端
4. 更新资产状态为 `parsed_scene_llm`

## 前置条件

### 1. 后端服务运行

确保后端服务已启动：

```bash
cd services/backend
python -m uvicorn app.main:app --host localhost --port 8000
```

### 2. GLM API Key

访问 [智谱 AI 开放平台](https://open.bigmodel.cn/) 注册并获取 API Key。

### 3. Python 依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 方法一：使用配置向导（推荐）

1. 运行配置脚本设置环境变量：

```powershell
.\setup_env.ps1
```

2. 启动 Worker：

```powershell
.\start_worker.ps1
```

### 方法二：手动设置环境变量

```powershell
# 设置后端地址
$env:BDC_BACKEND_BASE_URL = "http://127.0.0.1:8000"

# 设置本地存储目录（必须与 settings.local_storage_dir 一致）
$env:BDC_LOCAL_STORAGE_DIR = "d:\Huawei Files\华为家庭存储\Programs\program-bdc-ai\data\local_storage"

# 设置 GLM API Key
$env:GLM_API_KEY = "your-glm-api-key-here"

# 可选：仅处理指定项目
# $env:BDC_SCENE_PROJECT_ID = "your-project-uuid"

# 可选：设置轮询间隔（默认 60 秒）
$env:BDC_SCENE_WORKER_POLL_INTERVAL = "60"

# 启动 Worker
python scene_issue_glm_worker.py
```

## 环境变量说明

| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| `BDC_BACKEND_BASE_URL` | ✓ | 后端服务地址 | `http://127.0.0.1:8000` |
| `BDC_LOCAL_STORAGE_DIR` | ✓ | 本地存储目录 | `./data/local_storage` |
| `GLM_API_KEY` | ✓ | GLM API Key | - |
| `BDC_SCENE_PROJECT_ID` | ✗ | 仅处理指定项目 | 处理所有项目 |
| `BDC_SCENE_WORKER_POLL_INTERVAL` | ✗ | 轮询间隔（秒） | `60` |
| `GLM_BASE_URL` | ✗ | GLM API 地址 | `https://open.bigmodel.cn/api/paas/v4/` |
| `GLM_VISION_MODEL` | ✗ | GLM 视觉模型 | `glm-4v` |

## 测试流程

### 1. 创建测试项目

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GLM Worker 测试项目",
    "client": "测试客户",
    "location": "测试地点",
    "status": "active"
  }'
```

### 2. 上传 scene_issue 图片（自动路由）

```bash
curl -X POST "http://localhost:8000/api/v1/assets/upload_image_with_note?project_id={PROJECT_ID}&source=mobile&content_role=scene_issue&auto_route=true" \
  -F "file=@path/to/scene_image.jpg" \
  -F "note=管道保温层破损，需要检查"
```

### 3. 观察 Worker 输出

Worker 会自动检测到新上传的图片并开始处理：

```
[2025-01-18 15:30:00] Checking for pending scene_issue assets...
Processing asset abc123...
[OK] Reported scene_issue_report_v1 for asset abc123
```

### 4. 查看分析结果

```bash
curl "http://localhost:8000/api/v1/assets/{ASSET_ID}"
```

返回的 `structured_payloads` 中会包含 `schema_type=scene_issue_report_v1` 的分析结果。

## Worker 输出示例

### 成功处理

```
[2025-01-18 15:30:00] Checking for pending scene_issue assets...
Processing asset 3a4f5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c...
[OK] Reported scene_issue_report_v1 for asset 3a4f5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c
```

### 分析结果结构

```json
{
  "schema_type": "scene_issue_report_v1",
  "payload": {
    "title": "管道保温层破损",
    "issue_category": "设备维护",
    "severity": "medium",
    "summary": "现场管道保温层存在明显破损，可能导致能量损失和冷凝水问题。",
    "suspected_causes": [
      "保温材料老化",
      "外力损伤",
      "施工质量问题"
    ],
    "recommended_actions": [
      "更换破损保温层",
      "检查相邻管道保温状况",
      "加强定期巡检"
    ],
    "confidence": 0.85,
    "tags": ["保温", "管道", "维护"]
  },
  "version": 1.0,
  "created_by": "glm-4v-worker"
}
```

## 常见问题

### Q: Worker 提示 "Local image file not found"

**A:** 检查 `BDC_LOCAL_STORAGE_DIR` 环境变量是否与后端的 `settings.local_storage_dir` 一致。

### Q: GLM API 调用失败

**A:** 检查：
1. API Key 是否正确
2. 网络是否能访问 `https://open.bigmodel.cn`
3. API 额度是否充足

### Q: Worker 无法连接后端

**A:** 确保：
1. 后端服务正在运行
2. `BDC_BACKEND_BASE_URL` 地址正确
3. 防火墙未阻止连接

### Q: 如何让 Worker 只处理某个项目？

**A:** 设置环境变量 `BDC_SCENE_PROJECT_ID` 为目标项目的 UUID。

## 生产环境部署建议

1. **使用进程管理器**：使用 `supervisord` 或 `systemd` 管理 Worker 进程
2. **日志文件**：将 Worker 输出重定向到日志文件
3. **监控告警**：监控 Worker 进程状态和 API 调用成功率
4. **多实例部署**：根据负载启动多个 Worker 实例

## 许可证

MIT License
