# BDC-AI 测试脚本

**最后更新**: 2026-01-26

---

## 📋 测试脚本列表

### 1️⃣ 权限系统测试

**test_yerui_permissions.py** - 权限系统验证脚本

**功能**:
- 测试 yerui 用户登录
- 验证权限列表（26 个权限）
- 检查 PC-UI 关键权限

**运行方式**:
```bash
python scripts/测试/test_yerui_permissions.py
```

**预期输出**:
```
[OK] 登录
[OK] 获取用户信息
[OK] is_superuser = True
[OK] 权限列表不为空 (26)
[OK] PC-UI 关键权限完整
[SUCCESS] 所有测试通过！
```

---

### 2️⃣ Worker 流程测试

**test_worker_flow.py** - Worker 服务流程测试

**功能**:
- 测试 Worker 轮询机制
- 验证场景问题分析流程
- 检查 GLM-4V 调用

**运行方式**:
```bash
python scripts/测试/test_worker_flow.py
```

---

### 3️⃣ 场景管道测试

**test_scene_issue_pipeline.py** - 场景问题分析管道测试

**功能**:
- 端到端测试场景问题分析
- 验证资产路由
- 检查 GLM-4V 响应

**运行方式**:
```bash
python scripts/测试/test_scene_issue_pipeline.py
```

---

## 📚 测试文档

### test_permission_control.md

**内容**: 前端权限控制测试完整指南

**适用场景**:
- PC-UI 权限功能测试
- 按钮显示/隐藏验证
- 不同权限用户测试

---

## 🚀 快速测试流程

### 测试权限系统（最常用）

```bash
# 1. 确保后端运行
双击: scripts\快速启动\启动后端服务.bat

# 2. 运行权限测试
python scripts/测试/test_yerui_permissions.py

# 3. 验证输出
# 应看到 [SUCCESS] 所有测试通过！
```

---

### 测试 Worker 服务

```bash
# 1. 启动后端和 Worker
双击: scripts\快速启动\启动后端服务.bat
双击: scripts\快速启动\启动Worker.bat

# 2. 运行测试
python scripts/测试/test_worker_flow.py
```

---

## ⚠️ 常见问题

### 问题 1: Connection refused

**原因**: 后端服务未启动

**解决**:
```bash
双击运行: scripts\快速启动\启动后端服务.bat
```

---

### 问题 2: 权限测试失败

**原因**: 权限未初始化

**解决**:
```bash
# 重新初始化权限
python scripts/Windows/init_auth_data.py

# 验证权限
python scripts/测试/test_yerui_permissions.py
```

---

### 问题 3: Worker 测试超时

**原因**: Worker 服务未启动或配置错误

**解决**:
1. 检查 Worker 是否运行
2. 验证 GLM API Key 配置
3. 查看后端日志

---

## 📊 测试结果记录

### 权限系统测试

| 测试项 | 状态 | 备注 |
|--------|------|------|
| 登录 | ✅ | yerui/admin 都可登录 |
| 权限列表 | ✅ | 26 个权限 |
| PC-UI 权限 | ✅ | 所有关键权限存在 |
| 超级用户标志 | ✅ | is_superuser=True |

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
| 权限验证 | ✅/❌ | 说明 |
| Worker 启动 | ✅/❌ | 说明 |
| GLM API 调用 | ✅/❌ | 说明 |

### 发现的问题

1. **问题描述**
   - 重现步骤
   - 错误信息
   - 严重程度

---

## 📚 相关文档

- **快速启动/README.md** - 服务启动脚本
- **docs/04-使用指南/账号权限系统使用指南.md** - 权限系统指南
- **docs/03-优化记录/权限初始化修复计划.md** - 权限修复记录
- **API 文档** - http://localhost:8000/docs

---

**测试脚本已集中管理！** 🧪

**维护**: BDC-AI 开发团队
**最后更新**: 2026-01-26
