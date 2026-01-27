# 账号管理插件调试指南

## 已添加的调试功能

### 前端调试 (API 客户端)

所有 API 请求现在都会输出详细的调试信息：

```
[API RESPONSE] URL: http://localhost:8000/api/v1/auth/users
[API RESPONSE] Status: 200
[API RESPONSE] Content-Type: application/json
[API SUCCESS] Data keys: ['id', 'username', 'email', ...]
```

### 后端调试 (FastAPI)

#### 1. 全局异常处理器

所有未处理的异常都会显示完整的堆栈跟踪：

```
============================================================
[SERVER ERROR] TypeError: Type is not JSON serializable: function
[SERVER ERROR] Method: GET
[SERVER ERROR] URL: http://localhost:8000/api/v1/auth/users
[SERVER ERROR] Client: ('127.0.0.1', 55978)
[SERVER ERROR] Traceback:
  (完整的堆栈跟踪)
============================================================
```

#### 2. API 端点调试

每个端点都会输出关键信息：

- `/me` - 用户信息获取
```
[DEBUG] /me called for user: yerui
[DEBUG] Found 1 roles
[DEBUG] Superuser yerui, permissions count: 33
[DEBUG] Returning user_dict for yerui
```

- `/users` - 用户列表
```
[DEBUG] list_users called: skip=0, limit=100
[DEBUG] Found 2 users
[DEBUG] Returning 2 users
```

- `/roles` - 角色列表
```
[DEBUG] /roles called
[DEBUG] Found 5 roles
[DEBUG] Returning 5 roles as dicts
```

- `/permissions` - 权限列表
```
[DEBUG] /permissions called
[DEBUG] Found 33 permissions
[DEBUG] Returning 33 permissions as dicts
```

- `/audit-logs` - 审计日志
```
[DEBUG] /audit-logs called: skip=0, limit=100
[DEBUG] Found 15 audit logs
[DEBUG] Returning 15 audit logs
```

## 启动服务

### 1. 启动后端服务

```batch
cd D:\BDC-AI
venv\Scripts\python.exe -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload
```

### 2. 启动管理界面

```batch
cd D:\BDC-AI
venv\Scripts\python.exe services\backend\app\admin\main.py
```

## 查看调试信息

### 前端调试信息

查看管理界面的命令行窗口，会显示：
- `[API RESPONSE]` - API 响应信息
- `[API SUCCESS]` - 成功的响应
- `[API ERROR]` - 错误的响应

### 后端调试信息

查看后端服务的命令行窗口，会显示：
- `[DEBUG]` - API 端点调试信息
- `[SERVER ERROR]` - 服务器错误和堆栈跟踪

## 如何使用调试信息定位问题

### 步骤 1: 重现问题

在管理界面中执行导致错误的操作（例如点击某个菜单）

### 步骤 2: 查看前端输出

管理界面窗口会显示类似：
```
[API RESPONSE] URL: http://localhost:8000/api/v1/auth/roles
[API RESPONSE] Status: 500
[API ERROR] Detail: Internal server error
[API ERROR] Full error: {'detail': 'Internal server error', 'error_type': 'TypeError', ...}
```

### 步骤 3: 查看后端输出

后端服务窗口会显示完整的错误堆栈：
```
============================================================
[SERVER ERROR] TypeError: Type is not JSON serializable: function
[SERVER ERROR] Method: GET
[SERVER ERROR] URL: http://localhost:8000/api/v1/auth/roles
[SERVER ERROR] Traceback:
  File "...\auth.py", line 405, in list_roles
    return roles
  ...
============================================================
```

### 步骤 4: 定位问题

根据堆栈跟踪，找到：
- 出错的文件和行号
- 出错的函数名
- 具体的错误原因

## 常见问题

### 1. TypeError: Type is not JSON serializable

**原因**: 返回的数据包含无法序列化的对象（如函数、SQLAlchemy 关系等）

**解决方案**:
- 手动转换为字典，确保所有字段都是基本类型
- UUID → `str(uuid)`
- datetime → `datetime.isoformat()`
- bool/int → 显式转换

### 2. 401 Unauthorized

**原因**: Token 过期或无效

**解决方案**:
- 重新登录获取新 Token
- 检查 Token 是否正确设置

### 3. ModuleNotFoundError

**原因**: Python 路径配置问题

**解决方案**:
- 确保在 `main.py` 开头设置了正确的 `sys.path`
- 确保所有包目录都有 `__init__.py` 文件

## 修复记录

### 已修复的问题

1. ✅ **模块导入错误**
   - 添加了 `services/__init__.py`
   - 添加了 `services/backend/__init__.py`
   - 在 `main.py` 中设置了项目根目录路径

2. ✅ **AdminApp 属性错误**
   - 修复了 `load_statistics` 方法的缩进
   - 在 `__init__` 中初始化统计标签引用

3. ✅ **JSON 序列化错误**
   - 修复了 `/me` 端点
   - 修复了 `/users` 端点
   - 修复了 `/roles` 端点
   - 修复了 `/permissions` 端点
   - 修复了 `/audit-logs` 端点
   - 添加了 `AuditLog` 导入

4. ✅ **添加了详细的调试信息**
   - 前端 API 客户端调试
   - 后端全局异常处理器
   - 各个 API 端点的调试输出

## 技术细节

### 修复策略

所有 API 端点现在都遵循以下模式：

```python
@router.get("/endpoint")
def endpoint_function(...):
    # 1. 添加调试输出
    print(f"[DEBUG] endpoint called")

    # 2. 查询数据
    data = db.query(Model).all()

    # 3. 手动转换为字典
    result = []
    for item in data:
        item_dict = {
            "id": str(item.id),  # UUID → str
            "name": item.name,
            "created_at": item.created_at.isoformat()  # datetime → str
        }
        result.append(item_dict)

    # 4. 返回字典列表
    return result
```

### 为什么不直接返回 SQLAlchemy 对象？

SQLAlchemy 对象包含：
- 关系属性（relationship）- 无法序列化
- 延迟加载属性 - 可能导致序列化错误
- 方法（`__repr__` 等）- 不是数据

手动转换为字典确保：
- 所有字段都是基本类型
- 完全控制返回的数据结构
- 避免意外的序列化错误
