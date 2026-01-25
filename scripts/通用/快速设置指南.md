# API KEY 快速配置指南

## 🎯 配置目标

为 BDC-AI 后端服务和 Worker 服务配置安全的 API KEY 和 JWT 密钥。

---

## ⚠️ 重要提醒

### 🔴 立即执行：撤销旧 API KEY

您当前的 `.env` 文件包含已暴露的 API KEY：
```
GLM_API_KEY=1118ea2937584ae694baeb0a6319204f.fBTpVqtJR4gMmGgr
```

**请立即执行**：
1. 访问：https://open.bigmodel.cn/apikeys
2. 找到此 KEY 并删除/禁用
3. 生成新的 API KEY

---

## 📋 方案选择

### 方案 A：自动化配置脚本（推荐）⭐⭐⭐⭐⭐

**优点**：
- ✅ 自动生成强随机 JWT 密钥
- ✅ 交互式配置向导
- ✅ 自动备份旧配置
- ✅ 自动设置文件权限

**执行步骤**：

```bash
# 1. 运行配置脚本
python scripts/setup_api_keys.py

# 2. 按照提示操作
# - 脚本会生成新的 JWT 密钥
# - 提示输入后端 API KEY
# - 提示输入 Worker API KEY（可选，可使用同一个）

# 3. 确认配置
# 脚本会显示配置摘要，确认后自动生成配置文件

# 4. 验证配置
cat .env
cat services/worker/.env
```

**预计时间**：5 分钟

---

### 方案 B：手动配置（备选）

**步骤 1：生成 JWT 密钥**

```bash
# Windows (PowerShell)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})

# Linux/Mac
openssl rand -hex 32
```

**新生成的 JWT 密钥**：
```
17ca5cc6344fc107fd0a95f24db39299a8650170123b50a23d9bf4e708f9553f
```

**步骤 2：编辑根目录 `.env`**

```bash
# Windows
notepad .env

# Linux/Mac
nano .env
```

更新以下内容：
```bash
BDC_JWT_SECRET_KEY=17ca5cc6344fc107fd0a95f24db39299a8650170123b50a23d9bf4e708f9553f
GLM_API_KEY=<新的后端API KEY>
```

**步骤 3：Worker 配置已自动创建**

`services/worker/.env` 已创建，只需更新 API KEY：

```bash
# Windows
notepad services\worker\.env

# Linux/Mac
nano services/worker/.env
```

更新：
```bash
GLM_API_KEY=<新的Worker API KEY>
```

**步骤 4：设置文件权限**

```bash
# Linux/Mac
chmod 600 .env
chmod 600 services/worker/.env

# Windows (使用文件属性)
# 右键文件 → 属性 → 安全 → 高级 → 禁用继承
# 仅保留自己的访问权限
```

---

## 🔑 API KEY 获取指南

### 1. 访问智谱 AI 开放平台

**网址**：https://open.bigmodel.cn/

### 2. 登录/注册

- 使用手机号注册
- 或使用微信扫码登录

### 3. 创建 API KEY

**导航**：
```
控制台 → API KEY → 创建新的 API KEY
```

**建议创建两个独立的 KEY**：

| KEY 名称 | 用途 | 权限 |
|---------|------|------|
| BDC-AI-Backend | 后端服务 | 完整权限 |
| BDC-AI-Worker | Worker 服务 | 完整权限 |

### 4. 复制 API KEY

- 点击 KEY 右侧的"复制"按钮
- 粘贴到配置文件中
- ⚠️ **重要**：将 KEY 保存到密码管理器

---

## ✅ 配置验证

### 验证后端配置

```bash
# 1. 检查配置文件
cat .env

# 应该包含：
# BDC_JWT_SECRET_KEY=<64字符hex>
# GLM_API_KEY=<您的API KEY>

# 2. 启动后端服务
python -m uvicorn services.backend.app.main:app --host localhost --port 8000

# 3. 测试健康检查
curl http://localhost:8000/health

# 预期输出：
# {"status": "healthy"}
```

### 验证 Worker 配置

```bash
# 1. 检查配置文件
cat services/worker/.env

# 应该包含：
# GLM_API_KEY=<您的API KEY>
# BDC_BACKEND_BASE_URL=http://localhost:8000

# 2. 启动 Worker（新终端）
python services/worker/scene_issue_glm_worker.py

# 3. 观察日志
# 应该看到：
# Starting GLM-4V Scene Issue Worker...
# Worker initialized successfully
```

---

## 🚨 故障排查

### 问题 1：JWT 密钥无效

**错误信息**：
```
Error: Invalid JWT secret key
```

**解决方案**：
1. 检查 `.env` 中的 `BDC_JWT_SECRET_KEY` 是否为 64 字符
2. 确保没有多余的空格或引号
3. 重新生成密钥

### 问题 2：API KEY 无效

**错误信息**：
```
Error: 401 Unauthorized
GLM API key is invalid
```

**解决方案**：
1. 访问 https://open.bigmodel.cn/apikeys
2. 验证 KEY 是否正确
3. 检查 KEY 是否被禁用
4. 尝试重新生成 KEY

### 问题 3：Worker 无法连接后端

**错误信息**：
```
Error: Connection refused
```

**解决方案**：
1. 确认后端服务已启动
2. 检查 `BDC_BACKEND_BASE_URL` 是否正确
3. 尝试使用 `127.0.0.1` 而非 `localhost`

### 问题 4：文件权限错误（Linux/Mac）

**错误信息**：
```
Permission denied: .env
```

**解决方案**：
```bash
chmod 600 .env
chmod 600 services/worker/.env
```

---

## 📊 配置文件对比

### 后端配置 (.env)

```bash
# 必须配置
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai
BDC_LOCAL_STORAGE_DIR=data/assets
BDC_JWT_SECRET_KEY=<64字符hex>
GLM_API_KEY=<后端API KEY>

# 可选配置
BDC_MINIO_ENDPOINT=localhost:9000
BDC_MINIO_ACCESS_KEY=minioadmin
BDC_MINIO_SECRET_KEY=minioadmin
BDC_MINIO_BUCKET=bdc-assets
```

### Worker 配置 (services/worker/.env)

```bash
# 必须配置
BDC_BACKEND_BASE_URL=http://localhost:8000
BDC_LOCAL_STORAGE_DIR=../data/assets
GLM_API_KEY=<Worker API KEY>

# 可选配置
BDC_SCENE_WORKER_POLL_INTERVAL=60
BDC_SCENE_PROJECT_ID=<特定项目ID>
```

---

## 🔐 安全最佳实践

### 1. 永不提交 .env 到 git

```bash
# 确认 .gitignore 包含
.env
.env.local
.env.*.local
services/worker/.env
```

### 2. 使用独立的 API KEY

- 后端和 Worker 使用不同的 KEY
- 便于监控和故障隔离

### 3. 定期轮换密钥

- 每季度更换 API KEY
- 每半年更换 JWT 密钥

### 4. 监控 API 使用量

```bash
# 访问：https://open.bigmodel.cn/apikeys
# 查看各 KEY 的调用量和费用
```

### 5. 备份配置

```bash
# 将敏感配置保存到密码管理器
# 标注版本和更新日期
```

---

## 📚 相关文档

- **API KEY 安全管理方案**：`docs/02-技术文档/API-KEY安全管理方案.md`
- **配置模板**：`.env.example`
- **Worker 配置模板**：`services/worker/.env.example`
- **自动化脚本**：`scripts/setup_api_keys.py`

---

## 🎉 下一步

配置完成后，您可以：

1. **启动后端服务**
   ```bash
   python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000
   ```

2. **启动 Worker 服务**
   ```bash
   python services/worker/scene_issue_glm_worker.py
   ```

3. **测试认证**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   ```

4. **访问 API 文档**
   ```
   http://localhost:8000/docs
   ```

---

**文档维护**：BDC-AI 开发团队
**最后更新**：2026-01-24
**版本**：v1.0.0
