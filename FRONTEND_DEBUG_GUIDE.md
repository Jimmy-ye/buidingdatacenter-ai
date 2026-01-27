# 如何查看管理界面的错误信息

## 问题：浏览器显示 500 Internal Server Error

当您看到 `500 Internal Server Error` 时，这是 NiceGUI 服务器端的错误，不是 API 错误。

## 查看错误信息的方法

### 方法 1: 查看管理界面窗口（推荐）

运行管理界面的命令行窗口会显示所有错误信息：

```batch
cd D:\BDC-AI
venv\Scripts\python.exe services\backend\app\admin\main.py
```

**窗口中会显示**：
```
[FRONTEND] /admin/users page called
[FRONTEND] Loading users...
[FRONTEND ERROR] Page rendering failed: ...
Traceback (most recent call last):
  ...
```

### 方法 2: 运行诊断脚本

```batch
cd D:\BDC-AI
venv\Scripts\python.exe test_frontend_debug.py
```

这会检查所有组件是否正常。

### 方法 3: 查看浏览器控制台

按 `F12` 打开浏览器开发者工具，查看 Console 标签页。

## 常见错误和解决方案

### 错误 1: `KeyError: 'xxx'`

**原因**: 前端尝试访问后端数据中不存在的字段

**解决**:
1. 查看后端返回的实际数据结构
2. 修改前端代码以匹配后端数据结构

### 错误 2: `AttributeError: 'NoneType' object has no attribute 'xxx'`

**原因**: 尝试访问 None 对象的属性

**解决**:
1. 检查 API 是否返回了数据
2. 添加空值检查

### 错误 3: `TypeError: ... is not JSON serializable`

**原因**: 尝试序列化无法转换为 JSON 的对象

**解决**:
1. 确保所有数据都是基本类型（str, int, bool, list, dict）
2. UUID 和 datetime 必须转换为字符串

## 当前添加的调试功能

### 前端页面调试

所有页面现在都会输出详细调试信息：

```python
[FRONTEND] /admin/users page called       # 页面被访问
[FRONTEND] Loading users...                # 开始加载数据
[FRONTEND] Loaded 2 users                  # 加载完成
[FRONTEND] First user data: {...}          # 第一条数据
[FRONTEND] Rendering table...              # 开始渲染表格
[FRONTEND] Table created successfully      # 表格创建成功
```

### 错误捕获

所有页面都有 try-except 块：

```python
try:
    # 页面渲染代码
    ...
except Exception as e:
    print(f"[FRONTEND ERROR] Page rendering failed: {e}")
    traceback.print_exc()  # 打印完整堆栈
    ui.label(f'页面加载错误: {str(e)}')
```

## 调试步骤

### 1. 重启管理界面

确保最新代码生效：

```batch
# 停止当前运行的管理界面（Ctrl+C）
# 重新启动
venv\Scripts\python.exe services\backend\app\admin\main.py
```

### 2. 清除浏览器缓存

按 `Ctrl+Shift+R` 强制刷新页面

### 3. 查看完整错误输出

点击菜单触发错误后，**立即查看管理界面窗口**，会显示：

```
============================================================
[FRONTEND ERROR] Page rendering failed: ...
Traceback (most recent call last):
  File "...", line XXX, in <module>
    ...
  File "...", line YYY, in page_function
    ...
TypeError: ...
============================================================
```

### 4. 复制错误信息

请复制完整的错误输出，包括：
- 错误类型（TypeError, KeyError, AttributeError）
- 错误消息
- 完整的堆栈跟踪（Traceback）

## 示例：完整的调试输出

### 正常情况

```
[FRONTEND] /admin/users page called
[FRONTEND] Loading users...
[API RESPONSE] URL: http://localhost:8000/api/v1/auth/users
[API RESPONSE] Status: 200
[API SUCCESS] Data keys: ['data']
[FRONTEND] Loaded 2 users
[FRONTEND] First user data: {'id': '...', 'username': 'yerui', ...}
[FRONTEND] Rendering table with 2 users
[FRONTEND] Formatted 2 rows for table
[FRONTEND] Table created successfully
```

### 错误情况

```
[FRONTEND] /admin/users page called
[FRONTEND] Loading users...
[FRONTEND] Loaded 2 users
[FRONTEND] Rendering table with 2 users
[FRONTEND ERROR] Table rendering failed: KeyError('code')
Traceback (most recent call last):
  File "users.py", line 38, in format_users_for_table
    roles_str = ', '.join([r.get('code') for r in user.get('roles', [])])
KeyError: 'code'
```

## 需要提供的信息

当报告问题时，请提供：

1. **完整的前端输出**（管理界面窗口的内容）
2. **完整的后端输出**（后端服务窗口的内容）
3. **具体操作**（点击了哪个菜单/按钮）
4. **浏览器显示的错误**（如果有）

这样我就能快速定位和修复问题！
