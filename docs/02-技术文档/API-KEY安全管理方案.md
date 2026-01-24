# API KEY 安全管理方案

## 📋 目录

1. [当前问题](#当前问题)
2. [API KEY 管理最佳实践](#api-key-管理最佳实践)
3. [本地服务器部署配置](#本地服务器部署配置)
4. [环境变量配置清单](#环境变量配置清单)
5. [安全检查清单](#安全检查清单)

---

## 🔴 当前问题

### ⚠️ 严重安全问题

1. **真实 API KEY 暴露在代码中**
   - 当前 `.env` 包含：`GLM_API_KEY=1118ea2937584ae694baeb0a6319204f.fBTpVqtJR4gMmGgr`
   - **立即行动**：访问 https://open.bigmodel.cn/apikeys 撤销此 KEY！

2. **配置文件未正确管理**
   - `.env` 文件包含敏感信息，但可能被意外提交
   - 缺少环境分离（开发/测试/生产）

---

## 🔐 API KEY 管理最佳实践

### 方案对比

| 方案 | 安全性 | 复杂度 | 推荐度 | 适用场景 |
|------|--------|--------|--------|---------|
| **环境变量 (.env)** | ⭐⭐⭐ | 低 | ⭐⭐⭐⭐ | 开发/测试环境 |
| **密钥管理服务** | ⭐⭐⭐⭐⭐ | 高 | ⭐⭐⭐⭐⭐ | 生产环境 |
| **加密配置文件** | ⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐ | 单服务器部署 |
| **Docker Secrets** | ⭐⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐ | 容器化部署 |

### 推荐：环境变量 + .gitignore（当前方案）

**优点**：
- ✅ 简单易用
- ✅ 支持多环境
- ✅ .gitignore 已正确配置

**注意事项**：
- ⚠️ 确保 `.env` 在 `.gitignore` 中
- ⚠️ 使用 `.env.example` 作为模板
- ⚠️ 定期轮换 API KEY
- ⚠️ 不同环境使用不同的 KEY

---

## 🖥️ 本地服务器部署配置

### 架构设计

```
本地服务器（24/7 运行）
├── FastAPI 后端服务（端口 8000）
│   ├── 配置文件：/opt/bdc-ai/.env
│   ├── 数据库连接：PostgreSQL
│   └── JWT 认证
│
└── Worker 服务（独立进程）
    ├── 配置文件：/opt/bdc-ai/services/worker/.env
    ├── GLM API KEY
    └── 轮询间隔：60秒
```

### 配置文件结构

```
/opt/bdc-ai/                          # 项目根目录
├── .env                              # 后端主配置（不提交）
├── .env.example                      # 配置模板（提交）
├── .gitignore                        # 忽略敏感文件
├── services/
│   ├── backend/
│   │   └── .env                      # 后端服务配置（可选，继承根目录）
│   └── worker/
│       ├── .env.example              # Worker 配置模板
│       └── .env                      # Worker 实际配置（不提交）
```

---

## 📝 环境变量配置清单

### 1️⃣ 根目录 `.env`（后端服务）

**必须配置**：

```bash
# ================= 数据库配置 =================
BDC_DATABASE_URL=postgresql://admin:strong-password@localhost:5432/bdc_ai

# ================= 本地存储 =================
BDC_LOCAL_STORAGE_DIR=/opt/bdc-ai/data/assets

# ================= JWT 认证（安全）=================
# ⚠️ 生产环境必须使用强随机密钥
BDC_JWT_SECRET_KEY=<使用 openssl rand -hex 32 生成>
BDC_ACCESS_TOKEN_EXPIRE_MINUTES=30
BDC_REFRESH_TOKEN_EXPIRE_DAYS=7

# ================= GLM API（后端直接调用）=================
GLM_API_KEY=<从 https://open.bigmodel.cn/ 获取>
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v
```

**可选配置**：

```bash
# ================= MinIO 对象存储（生产环境）=================
BDC_MINIO_ENDPOINT=localhost:9000
BDC_MINIO_ACCESS_KEY=minioadmin
BDC_MINIO_SECRET_KEY=<强密码>
BDC_MINIO_BUCKET=bdc-assets

# ================= 服务配置 =================
BDC_HOST=0.0.0.0
BDC_PORT=8000
BDC_LOG_LEVEL=INFO
BDC_DEBUG=false
```

---

### 2️⃣ Worker `.env`（services/worker/.env）

**必须配置**：

```bash
# ================= 后端连接 =================
BDC_BACKEND_BASE_URL=http://localhost:8000

# ================= 本地存储 =================
# ⚠️ 必须与根目录 .env 中的路径一致
BDC_LOCAL_STORAGE_DIR=/opt/bdc-ai/data/assets

# ================= GLM API（Worker 使用）=================
# ⚠️ 建议使用独立的 API KEY（便于监控和限流）
GLM_API_KEY=<从 https://open.bigmodel.cn/ 获取>
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v

# ================= Worker 配置 =================
BDC_SCENE_WORKER_POLL_INTERVAL=60

# 可选：仅处理特定项目
# BDC_SCENE_PROJECT_ID=<project-uuid>
```

---

## 🔑 API KEY 管理策略

### 策略 1：单 KEY 方案（简单，适合开发/测试）

**配置**：
- 根目录 `.env` 和 `worker/.env` 使用**同一个 API KEY**

**优点**：
- ✅ 配置简单
- ✅ 便于测试

**缺点**：
- ⚠️ 无法区分使用量
- ⚠️ KEY 泄露影响全部服务

---

### 策略 2：双 KEY 方案（推荐）⭐⭐⭐⭐⭐

**配置**：
- 后端服务：使用 `GLM_API_KEY_1`
- Worker 服务：使用 `GLM_API_KEY_2`

**实施步骤**：

1. **在智谱 AI 平台创建两个 API KEY**
   - 访问：https://open.bigmodel.cn/apikeys
   - 创建 KEY 1：命名为 "BDC-AI-Backend"
   - 创建 KEY 2：命名为 "BDC-AI-Worker"

2. **配置根目录 `.env`**
   ```bash
   # 后端服务使用的 KEY
   GLM_API_KEY=<key-1-here>
   ```

3. **配置 Worker `.env`**
   ```bash
   # Worker 使用的独立 KEY
   GLM_API_KEY=<key-2-here>
   ```

**优点**：
- ✅ **隔离故障**：一个 KEY 出问题不影响另一个
- ✅ **独立监控**：可以查看各服务的调用量
- ✅ **细粒度限流**：可以为不同 KEY 设置不同的额度
- ✅ **便于追踪**：通过 KEY 识别哪个服务出现问题

---

### 策略 3：环境隔离（生产推荐）⭐⭐⭐⭐⭐

**配置**：
- 开发环境：`GLM_API_KEY_DEV`
- 测试环境：`GLM_API_KEY_TEST`
- 生产环境：`GLM_API_KEY_PROD`

**实施**：

1. **创建多个环境配置**
   ```
   .env.development   # 开发环境
   .env.staging       # 测试环境
   .env.production    # 生产环境
   ```

2. **启动时加载对应配置**
   ```bash
   # 开发环境
   export BDC_ENV=development
   python -m uvicorn services.backend.app.main:app --reload

   # 生产环境
   export BDC_ENV=production
   python -m uvicorn services.backend.app.main:app --host 0.0.0.0
   ```

---

## 🛡️ 安全检查清单

### 部署前检查

- [ ] **撤销已暴露的 API KEY**
  - 访问 https://open.bigmodel.cn/apikeys
  - 删除或禁用已暴露的 KEY
  - 生成新的 KEY

- [ ] **生成强随机 JWT 密钥**
  ```bash
  openssl rand -hex 32
  ```

- [ ] **修改数据库默认密码**
  ```bash
  # 修改 PostgreSQL admin 密码
  psql -U postgres -c "ALTER USER admin PASSWORD 'new-strong-password';"
  ```

- [ ] **更新 .gitignore**
  ```gitignore
  # 确保包含
  .env
  .env.local
  .env.*.local
  services/worker/.env
  ```

- [ ] **验证 .env 不在 git 历史中**
  ```bash
  git log --all --full-history -- ".env"
  # 如果有输出，说明曾经提交过，需要清理历史
  ```

- [ ] **创建 .env.example 模板**
  - 包含所有必要的配置项
  - 使用占位符而非真实值
  - 添加详细注释

---

### 运行时检查

- [ ] **文件权限**
  ```bash
  # 确保 .env 文件只有所有者可读
  chmod 600 /opt/bdc-ai/.env
  chmod 600 /opt/bdc-ai/services/worker/.env
  ```

- [ ] **服务启动验证**
  ```bash
  # 后端服务
  python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000

  # Worker 服务
  python services/worker/scene_issue_glm_worker.py
  ```

- [ ] **API 连通性测试**
  ```bash
  # 测试后端
  curl http://localhost:8000/health

  # 测试 Worker
  # 检查日志是否正常连接到 GLM API
  ```

---

### 定期维护

- [ ] **每月检查 API 使用量**
  - 访问 https://open.bigmodel.cn/apikeys
  - 查看各 KEY 的调用量和费用
  - 设置告警阈值

- [ ] **每季度轮换 API KEY**
  - 生成新 KEY
  - 更新配置文件
  - 重启服务
  - 撤销旧 KEY

- [ ] **定期审计访问日志**
  - 检查异常 API 调用
  - 监控错误率
  - 记录异常 IP

---

## 🚀 快速部署步骤

### 步骤 1：准备工作（15 分钟）

```bash
# 1. 撤销已暴露的 API KEY
# 访问：https://open.bigmodel.cn/apikeys

# 2. 生成新的 API KEY（建议创建两个）
# KEY 1: BDC-AI-Backend（后端服务）
# KEY 2: BDC-AI-Worker（Worker 服务）

# 3. 生成强随机 JWT 密钥
openssl rand -hex 32
# 输出：9b77e3c8660ee5cf63289ccc797f5f6cab5063e39f31937e00eb8b0689b29248
```

### 步骤 2：配置后端服务（10 分钟）

```bash
# 1. 编辑根目录 .env
cd /opt/bdc-ai
nano .env

# 2. 添加以下内容
BDC_DATABASE_URL=postgresql://admin:strong-password@localhost:5432/bdc_ai
BDC_LOCAL_STORAGE_DIR=/opt/bdc-ai/data/assets
BDC_JWT_SECRET_KEY=<openssl 生成的密钥>
BDC_ACCESS_TOKEN_EXPIRE_MINUTES=30
BDC_REFRESH_TOKEN_EXPIRE_DAYS=7
GLM_API_KEY=<KEY-1>
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v

# 3. 设置文件权限
chmod 600 .env
```

### 步骤 3：配置 Worker 服务（10 分钟）

```bash
# 1. 创建 Worker 配置
cd /opt/bdc-ai/services/worker
cp .env.example .env
nano .env

# 2. 添加以下内容
BDC_BACKEND_BASE_URL=http://localhost:8000
BDC_LOCAL_STORAGE_DIR=/opt/bdc-ai/data/assets
GLM_API_KEY=<KEY-2>
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v
BDC_SCENE_WORKER_POLL_INTERVAL=60

# 3. 设置文件权限
chmod 600 .env
```

### 步骤 4：启动服务（5 分钟）

```bash
# 1. 启动后端服务
cd /opt/bdc-ai
python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000

# 2. 新开终端，启动 Worker
cd /opt/bdc-ai/services/worker
python scene_issue_glm_worker.py
```

### 步骤 5：验证（5 分钟）

```bash
# 1. 测试后端健康检查
curl http://localhost:8000/health
# 预期输出：{"status": "healthy"}

# 2. 测试认证 API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# 预期输出：返回 access_token

# 3. 检查 Worker 日志
# 应该看到 "Starting GLM-4V Scene Issue Worker..."
```

---

## 📊 配置模板参考

### 完整的 `.env` 模板

**项目根目录 `.env.example`**：

```bash
# ================= 数据库配置 =================
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# ================= 本地存储 =================
BDC_LOCAL_STORAGE_DIR=data/assets

# ================= JWT 认证 =================
BDC_JWT_SECRET_KEY=change-this-in-production-use-openssl-rand-hex-32
BDC_ACCESS_TOKEN_EXPIRE_MINUTES=30
BDC_REFRESH_TOKEN_EXPIRE_DAYS=7

# ================= GLM API =================
GLM_API_KEY=your-glm-api-key-here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v

# ================= MinIO（可选）=================
# BDC_MINIO_ENDPOINT=localhost:9000
# BDC_MINIO_ACCESS_KEY=minioadmin
# BDC_MINIO_SECRET_KEY=minioadmin
# BDC_MINIO_BUCKET=bdc-assets

# ================= 服务配置 =================
BDC_HOST=0.0.0.0
BDC_PORT=8000
BDC_LOG_LEVEL=INFO
BDC_DEBUG=false
```

**Worker `.env.example`**：

```bash
# ================= 后端连接 =================
BDC_BACKEND_BASE_URL=http://localhost:8000

# ================= 本地存储 =================
BDC_LOCAL_STORAGE_DIR=data/assets

# ================= GLM API =================
GLM_API_KEY=your-glm-api-key-here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_VISION_MODEL=glm-4v

# ================= Worker 配置 =================
BDC_SCENE_WORKER_POLL_INTERVAL=60

# 可选：仅处理特定项目
# BDC_SCENE_PROJECT_ID=
```

---

## 💡 最佳实践总结

1. **永远不要将 .env 提交到 git**
   - 确保 `.gitignore` 包含 `.env`
   - 使用 `.env.example` 作为模板

2. **使用独立的 API KEY**
   - 后端和 Worker 使用不同的 KEY
   - 便于监控和故障隔离

3. **定期轮换密钥**
   - 每季度更换 API KEY
   - 每半年更换 JWT 密钥

4. **最小权限原则**
   - API KEY 仅授予必要的权限
   - 使用环境变量而非硬编码

5. **监控和告警**
   - 定期检查 API 使用量
   - 设置异常调用告警

6. **备份配置**
   - 将 .env 记录到安全的密码管理器
   - 标注配置版本和更新日期

---

**文档维护**：BDC-AI 开发团队
**最后更新**：2026-01-24
**版本**：v1.0.0
