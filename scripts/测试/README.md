# BDC-AI 测试脚本

**最后更新**: 2026-01-25

---

## 📋 测试脚本列表

### 后端测试

| 脚本 | 说明 | 运行方式 |
|------|------|----------|
| `test_image_routing_smoke.py` | 图片路由冒烟测试 | Python 脚本 |

### Worker 测试

| 脚本 | 说明 | 运行方式 |
|------|------|----------|
| `test_scene_issue_pipeline.py` | 场景问题处理流程测试 | Python 脚本 |
| `test_worker_flow.py` | Worker 工作流测试 | Python 脚本 |

---

## 🧪 运行测试

### 后端测试

```bash
# 确保后端服务正在运行
cd D:\BDC-AI

# 运行图片路由测试
venv\Scripts\python.exe scripts/测试/test_image_routing_smoke.py
```

**测试内容**:
- 图片上传接口
- 图片查询接口
- 图片删除接口
- 图片元数据

### Worker 测试

```bash
# 场景处理流程测试
venv311\Scripts\python.exe scripts/测试/test_scene_issue_pipeline.py

# Worker 工作流测试
venv311\Scripts\python.exe scripts/测试/test_worker_flow.py
```

**测试内容**:
- GLM-4V API 连接
- 图片读取和处理
- 结构化报告生成
- 结果回写数据库

---

## 📊 测试结果

### 成功标准

**后端测试**:
- ✅ 所有 API 端点返回 200 状态码
- ✅ 图片可以正常上传和下载
- ✅ 数据库记录正确创建
- ✅ 文件存储正确

**Worker 测试**:
- ✅ GLM API 连接成功
- ✅ 图片可以正常读取
- ✅ 分析报告格式正确
- ✅ 结果成功回写数据库

---

## 🔧 测试配置

### 环境要求

**后端测试**:
- 后端服务运行中（端口 8000）
- PostgreSQL 数据库可用
- 测试数据准备完毕

**Worker 测试**:
- 后端服务运行中
- GLM API Key 有效
- 测试图片文件可用

### 测试数据

**测试图片路径**:
```
data/assets/test/
├── scene_issue_1.jpg
├── scene_issue_2.jpg
└── scene_issue_3.jpg
```

---

## 📝 测试报告模板

### 测试日期
```
日期: YYYY-MM-DD
测试人员: XXX
环境: 开发/测试/生产
```

### 测试结果

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 后端启动 | ✅/❌ | 说明 |
| 图片上传 | ✅/❌ | 说明 |
| Worker 启动 | ✅/❌ | 说明 |
| GLM API 调用 | ✅/❌ | 说明 |

### 发现的问题

1. **问题描述**
   - 重现步骤
   - 错误信息
   - 严重程度

---

## 🐛 已知问题

### 问题 1: 编码错误

**错误**: `UnicodeEncodeError: 'gbk' codec can't encode character`

**解决方案**:
```bash
# 在脚本开头添加
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 问题 2: 路径错误

**错误**: `FileNotFoundError`

**解决方案**:
```bash
# 使用绝对路径
# 或在脚本开头添加
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
```

---

## 🔄 持续集成

### 自动化测试

未来可以集成到 CI/CD 流程：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          python -m pytest scripts/测试/test_image_routing_smoke.py

  test-worker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run worker tests
        run: |
          python -m pytest scripts/测试/test_worker_flow.py
```

---

## 📚 相关文档

- **服务管理/README.md** - 服务启动和管理
- **后端服务器部署完整指南.md** - 部署文档
- **API 文档** - http://localhost:8000/docs

---

**测试脚本已集中管理！** 🧪
