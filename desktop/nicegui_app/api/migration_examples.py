"""
API 调用迁移示例

展示如何将旧的 API 调用方式迁移到新的 BackendClient

版本: v1.0
"""

# ==================== 旧方式（保留但不推荐）====================

# 示例 1: 获取项目列表
async def old_list_projects():
    """旧方式：直接调用 fetch_json"""
    from desktop.nicegui_app.pc_app import fetch_json
    return await fetch_json("/projects/")


# 示例 2: 获取工程结构树
async def old_get_tree(project_id: str):
    """旧方式：直接调用 fetch_json"""
    from desktop.nicegui_app.pc_app import fetch_json
    return await fetch_json(f"/projects/{project_id}/structure_tree")


# 示例 3: 上传文件
async def old_upload_file(file_data, filename):
    """旧方式：手动构造 httpx 请求"""
    import httpx
    BACKEND_BASE_URL = "http://127.0.0.1:8000/api/v1"

    files = {"file": (filename, file_data, "image/jpeg")}
    data = {"device_id": "xxx", "content_role": "meter"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BACKEND_BASE_URL}/assets/upload_image_with_note",
            data=data,
            files=files
        )
        resp.raise_for_status()
        return resp.json()


# ==================== 新方式（推荐）====================

# 示例 1: 获取项目列表
async def new_list_projects():
    """新方式：使用 BackendClient"""
    from desktop.nicegui_app.api.client import BackendClient
    client = BackendClient()
    return await client.list_projects()


# 示例 2: 获取工程结构树
async def new_get_tree(project_id: str):
    """新方式：使用 BackendClient"""
    from desktop.nicegui_app.api.client import BackendClient
    client = BackendClient()
    return await client.get_structure_tree(project_id)


# 示例 3: 上传文件
async def new_upload_file(file_data, filename, device_id: str):
    """新方式：使用 BackendClient"""
    from desktop.nicegui_app.api.client import BackendClient
    client = BackendClient()
    return await client.upload_image(
        file_data=file_data,
        filename=filename,
        content_type="image/jpeg",
        device_id=device_id,
        content_role="meter"
    )


# ==================== 迁移对比表 ====================

"""
| 功能 | 旧方式 | 新方式 | 优势 |
|------|--------|--------|------|
| 获取项目列表 | fetch_json("/projects/") | client.list_projects() | ✅ 更清晰 |
| 获取项目详情 | fetch_json(f"/projects/{id}") | client.get_project(id) | ✅ 类型安全 |
| 创建项目 | 手动构造 POST | client.create_project(data) | ✅ 参数明确 |
| 删除项目 | 手动构造 DELETE | client.delete_project(id) | ✅ 统一接口 |
| 上传文件 | 手动 httpx 请求 | client.upload_image(...) | ✅ 简化代码 |
| 错误处理 | 自己处理 try-except | 统一处理 | ✅ 一致性 |
"""

# ==================== 实际迁移步骤 ====================

"""
步骤 1: 在函数顶部导入 BackendClient
```python
from desktop.nicegui_app.api.client import BackendClient

# 创建全局实例（推荐）
backend_client = BackendClient()
```

步骤 2: 找到使用 fetch_json 的地方
```python
# 旧代码
projects = await fetch_json("/projects/")

# 新代码
projects = await backend_client.list_projects()
```

步骤 3: 找到使用 httpx 直接请求的地方
```python
# 旧代码
async with httpx.AsyncClient() as client:
    resp = await client.post(f"{BACKEND_BASE_URL}/assets", data=data)
    resp.raise_for_status()
    return resp.json()

# 新代码
result = await backend_client.post("/assets", data=data)
```

步骤 4: 测试功能是否正常
- 运行 PC UI
- 验证相关功能
- 确认无异常

步骤 5: 提交代码
```bash
git add .
git commit -m "refactor: 迁移 X 功能到 BackendClient"
```
"""

# ==================== 兼容性处理 ====================

"""
如果某些旧代码暂时无法迁移，可以保留兼容层：

```python
# 在 pc_app.py 中保留旧函数，但内部调用新客户端
async def fetch_json(path: str, params: Optional[Dict] = None) -> Any:
    \"\"\"向后兼容的 fetch_json 函数\"\"\"
    # 添加警告日志
    import warnings
    warnings.warn("fetch_json 已废弃，请使用 backend_client", DeprecationWarning)

    # 内部调用新客户端
    return await backend_client.get(path, params=params)
```

这样新旧代码可以共存，逐步迁移。
"""

if __name__ == "__main__":
    import asyncio

    # 测试新方式
    async def test_new_way():
        print("测试新方式...")
        projects = await new_list_projects()
        print(f"获取到 {len(projects)} 个项目")

        if projects:
            tree = await new_get_tree(projects[0]["id"])
            print(f"工程结构树节点数: {len(tree.get('nodes', []))}")

    asyncio.run(test_new_way())
