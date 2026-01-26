# PC-UI 认证功能测试指南

## 📋 测试概述

本测试用于验证 PC-UI 认证系统是否正常工作，包括：
- 后端认证 API
- 登录/登出功能
- Token 管理
- 会话持久化
- 401 错误处理

---

## 🚀 快速开始

### 方法 1：自动化测试（推荐）

#### 步骤 1：启动后端服务

打开**第一个**终端窗口：

```bash
# Windows CMD
cd "D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai"
scripts\start_backend.bat

# 或手动启动
python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

等待看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

#### 步骤 2：运行自动化测试

打开**第二个**终端窗口：

```bash
cd "D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai"
scripts\测试\run_auth_test.bat
```

测试将自动检查：
- ✅ 后端健康状态
- ✅ 登录接口（admin/admin123）
- ✅ 错误凭证处理
- ✅ Token 访问受保护接口
- ✅ 未授权访问拦截

---

### 方法 2：完整 UI 测试

#### 步骤 1：启动后端服务

同方法 1

#### 步骤 2：启动 PC-UI

打开**第三个**终端窗口：

```bash
cd "D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai"
scripts\start_pcui.bat

# 或手动启动
python -m desktop.nicegui_app.pc_app
```

等待看到：
```
INFO:     Started application
INFO:     Uvicorn running on http://0.0.0.0:8080
```

#### 步骤 3：浏览器测试

运行测试辅助脚本：

```bash
scripts\测试\test_pc_ui_auth_flow.bat
```

脚本会自动打开浏览器并显示测试步骤。

---

## 📝 手动测试清单

### A. 登录功能测试

1. **访问登录页**
   - [ ] 打开浏览器访问 http://localhost:8080
   - [ ] 自动跳转到 http://localhost:8080/login
   - [ ] 看到登录界面（BDC-AI 标题、用户名/密码输入框）
   - [ ] 看到环境标识（"开发环境"）

2. **正确凭证登录**
   - [ ] 输入用户名: `admin`
   - [ ] 输入密码: `admin123`
   - [ ] 点击"登录"按钮
   - [ ] 看到绿色通知："登录成功"
   - [ ] 自动跳转到主页

3. **验证登录状态**
   - [ ] 页面右上角显示："用户: admin"
   - [ ] 页面右上角显示登出按钮（logout 图标）
   - [ ] 能看到项目列表（如果有数据）
   - [ ] 没有 401 错误

### B. 会话持久化测试

1. **刷新页面**
   - [ ] 按 F5 刷新浏览器
   - [ ] 仍然保持登录状态
   - [ ] 用户信息仍然显示
   - [ ] 不需要重新登录

2. **关闭重开**
   - [ ] 关闭浏览器标签页
   - [ ] 重新打开 http://localhost:8080
   - [ ] 自动进入主页（不需要登录）

### C. 登出功能测试

1. **点击登出**
   - [ ] 点击右上角的登出按钮
   - [ ] 看到蓝色通知："已登出"
   - [ ] 自动跳转到登录页

2. **验证登出后状态**
   - [ ] 刷新页面
   - [ ] 仍然在登录页
   - [ ] 无法直接访问主页

### D. 错误处理测试

1. **错误密码**
   - [ ] 在登录页输入: admin / wrong_password
   - [ ] 点击"登录"按钮
   - [ ] 看到红色错误消息
   - [ ] 不登录成功

2. **空输入**
   - [ ] 不输入用户名和密码
   - [ ] 点击"登录"按钮
   - [ ] 看到错误提示："用户名和密码不能为空"

### E. 401 自动处理测试

1. **模拟 Token 过期**
   - [ ] 登录系统
   - [ ] 打开浏览器开发工具（F12）
   - [ ] Application → Local Storage → 删除 token
   - [ ] 尝试访问需要认证的页面（如刷新主页）
   - [ ] 自动跳转到登录页
   - [ ] 看到"登录已过期"提示（如果实现）

---

## 🐛 故障排查

### 问题 1：后端连接失败

**错误信息**：
```
ConnectionRefusedError: [WinError 10061] 目标计算机积极拒绝无法连接
```

**解决方法**：
1. 确认后端服务已启动
2. 检查端口 8000 是否被占用：`netstat -ano | findstr :8000`
3. 查看后端日志是否有错误

### 问题 2：PC-UI 无法启动

**错误信息**：
```
ModuleNotFoundError: No module named 'desktop'
```

**解决方法**：
1. 确保在项目根目录运行命令
2. 检查 PYTHONPATH 设置
3. 尝试使用 `-m` 方式运行：`python -m desktop.nicegui_app.pc_app`

### 问题 3：登录后 401 错误

**可能原因**：
1. Token 未正确保存
2. 请求头未包含 Authorization
3. 后端认证中间件配置错误

**调试步骤**：
1. 打开浏览器开发工具（F12）
2. 查看 Network 标签
3. 检查请求头是否有 `Authorization: Bearer <token>`
4. 查看后端日志

### 问题 4：编码问题（乱码）

**解决方法**：
- 确保批处理文件以 `chcp 65001` 开头
- 确保终端使用 UTF-8 编码
- Python 文件保存为 UTF-8 格式

---

## 📊 测试结果记录

### 后端 API 测试

| 测试项 | 预期结果 | 实际结果 | 状态 |
|-------|---------|---------|------|
| 健康检查 | 200 OK | | ⬜ |
| 正确登录 | 200 + token | | ⬜ |
| 错误密码 | 401 Unauthorized | | ⬜ |
| Token 访问 | 200 + 数据 | | ⬜ |
| 无 Token 访问 | 401 Unauthorized | | ⬜ |

### UI 功能测试

| 测试项 | 预期结果 | 实际结果 | 状态 |
|-------|---------|---------|------|
| 登录页显示 | 跳转到 /login | | ⬜ |
| 登录成功 | 跳转到主页 | | ⬜ |
| 用户信息显示 | 显示用户名 | | ⬜ |
| 刷新保持登录 | 不需要重新登录 | | ⬜ |
| 登出功能 | 跳转回登录页 | | ⬜ |
| 错误凭证 | 显示错误消息 | | ⬜ |

---

## 🎯 下一步

测试通过后，可以继续：

### 阶段 3（当前）
- [ ] 完成 401 自动处理测试
- [ ] 验证 Token 过期场景

### 阶段 4
- [ ] 添加 refresh_token 支持
- [ ] 实现前端权限控制

### 阶段 1
- [ ] 移动端认证整合

---

## 📚 相关文档

- **认证方案**: `docs/02-技术文档/pc-ui/PC-UI和移动端认证整合实施方案.md`
- **编码规则**: `.claude/CODING_RULES.md`
- **NiceGUI 规则**: `.claude/NICEGUI_API_MIGRATION.md`

---

**文档维护**: BDC-AI 开发团队
**最后更新**: 2026-01-26
