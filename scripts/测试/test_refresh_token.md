# Refresh Token 测试指南

## 📋 测试目标

验证 PC-UI 的 refresh_token 自动刷新功能是否正常工作：
1. ✅ 登录时正确保存 refresh_token
2. ✅ access_token 过期时自动刷新
3. ✅ 刷新成功后请求自动重试
4. ✅ 刷新失败时自动登出

---

## 🚀 测试方法

### 方法 1：手动修改 Token 模拟过期

#### 步骤 1：登录系统

1. 访问 http://localhost:8080
2. 使用 admin/admin123 登录
3. 成功进入主页

#### 步骤 2：打开浏览器开发工具

按 `F12` 打开开发工具

#### 步骤 3：查看存储的 Token

```
Application → Local Storage → http://localhost:8080
```

应该看到：
- `auth_token`: 很长的 JWT 字符串
- `auth_refresh_token`: 另一个 JWT 字符串
- `auth_user`: 用户信息

复制并保存这两个 Token 到记事本（备用）。

#### 步骤 4：手动修改 access_token

将 `auth_token` 的值修改为无效值，例如：
```
invalid_token_12345
```

#### 步骤 5：触发 API 请求

在主页上：
- 点击"刷新"按钮
- 或尝试访问项目列表

**预期行为**：
1. 后端日志显示 `401 Unauthorized`
2. PC-UI 控制台显示：
   ```
   [INFO] 检测到 401，尝试刷新 Token...
   [INFO] Token 刷新成功
   [INFO] 请求 /projects/ 重试成功
   ```
3. 页面正常显示数据，**不需要重新登录**
4. Local Storage 中的 `auth_token` 已更新为新的值

---

### 方法 2：使用测试页面（自动化）

访问：http://localhost:8080/test-401

点击"触发场景 1"按钮（使用无效 Token）

**预期行为**：
- 后端日志显示 `401 Unauthorized`
- PC-UI 控制台显示刷新过程
- 自动跳转到登录页（因为 refresh_token 也无效）

---

## ✅ 验证清单

### 存储验证

| 检查项 | 预期结果 | 实际结果 | 状态 |
|--------|---------|---------|------|
| 登录后保存 refresh_token | Local Storage 有值 | | ⬜ |
| refresh_token 格式正确 | JWT 字符串 | | ⬜ |
| 登出后清除 refresh_token | Local Storage 删除 | | ⬜ |

### 自动刷新验证

| 检查项 | 预期结果 | 实际结果 | 状态 |
|--------|---------|---------|------|
| access_token 过期返回 401 | 后端日志显示 401 | | ⬜ |
| 自动调用刷新接口 | 调用 /auth/refresh | | ⬜ |
| 刷新成功更新 Token | Local Storage 更新 | | ⬜ |
| 自动重试原请求 | 请求成功返回数据 | | ⬜ |
| 用户无感知 | 不需要重新登录 | | ⬜ |

### 失败场景验证

| 检查项 | 预期结果 | 实际结果 | 状态 |
|--------|---------|---------|------|
| refresh_token 也无效 | 调用刷新接口失败 | | ⬜ |
| 自动登出 | 跳转到登录页 | | ⬜ |
| 显示错误提示 | "登录已过期" | | ⬜ |

---

## 🔍 调试输出

启用后查看 PC-UI 终端，应该看到类似日志：

**成功场景**：
```
[INFO] 检测到 401，尝试刷新 Token...
[INFO] Token 刷新成功
[INFO] 请求 /projects/ 重试成功
```

**失败场景**：
```
[INFO] 检测到 401，尝试刷新 Token...
[WARNING] Token 刷新失败: 401
[WARNING] Token 刷新失败，执行登出
```

---

## 🐛 故障排查

### 问题 1：没有自动刷新

**可能原因**：
1. 后端登录接口没有返回 refresh_token
2. refresh_token 未正确保存

**调试步骤**：
1. 检查登录响应是否包含 refresh_token
2. 查看 Local Storage 是否有 auth_refresh_token
3. 查看后端日志确认刷新接口被调用

### 问题 2：刷新后仍然 401

**可能原因**：
1. 后端刷新接口返回的 Token 仍然无效
2. 请求重试时没有使用新 Token

**调试步骤**：
1. 查看后端刷新接口响应
2. 确认新 Token 是否正确保存
3. 查看 PC-UI 控制台日志

### 问题 3：刷新失败但没有登出

**可能原因**：
_handle_401 逻辑问题

**调试步骤**：
1. 确认 refresh_token 是否为 None
2. 查看 PC-UI 控制台日志
3. 手动测试直接调用 _do_refresh_token()

---

## 📝 测试结果

请填写实际测试结果：

### 登录和存储
- [ ] 登录成功
- [ ] Local Storage 有 auth_token
- [ ] Local Storage 有 auth_refresh_token
- [ ] Token 格式正确（JWT）

### 自动刷新
- [ ] 手动修改 access_token 后触发 API 请求
- [ ] 后端返回 401
- [ ] PC-UI 自动调用刷新接口
- [ ] 刷新成功并更新 Token
- [ ] 请求自动重试成功
- [ ] 用户无需重新登录

### 失败处理
- [ ] 同时修改 access_token 和 refresh_token
- [ ] 刷新接口失败
- [ ] 自动跳转到登录页
- [ ] 显示"登录已过期"通知

---

## 🎯 下一步

测试通过后：
- [ ] 任务 #3 完成
- [ ] 继续任务 #4：实现前端权限控制

测试未通过：
- [ ] 记录失败场景
- [ ] 查看具体错误信息
- [ ] 修复后重新测试

---

**文档维护**: BDC-AI 开发团队
**最后更新**: 2026-01-26
