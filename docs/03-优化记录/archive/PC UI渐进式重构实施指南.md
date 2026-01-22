# PC UI 渐进式重构实施指南

## 🎯 重构原则

### 核心原则

1. **小步快跑**：每次只重构一小部分，立即测试
2. **功能等价**：重构不改变任何外部行为
3. **向后兼容**：新旧代码可以共存
4. **随时可回滚**：每步都可以安全回退
5. **增量交付**：每一步都能产生可工作的代码

### 禁止事项

- ❌ 一次性重写整个文件
- ❌ 同时修改多个不相关的功能
- ❌ 在没有备份的情况下删除旧代码
- ❌ 在周五下午进行大规模重构

---

## ⚠️ 风险识别与规避

### 风险矩阵

| 风险 | 等级 | 影响 | 规避措施 |
|------|------|------|----------|
| 功能回归 | 🔴 高 | 用户无法使用 | 增量测试 + 功能验证清单 |
| 状态丢失 | 🟡 中 | 用户体验下降 | 状态持久化 + 兼容层 |
| 性能下降 | 🟡 中 | 响应变慢 | 性能基准测试 |
| Git 冲突 | 🟢 低 | 开发效率 | 特性分支 + 频繁提交 |

---

## 🪜 阶段 0：准备工作（必做）

### 0.1 创建备份与分支

```bash
# 1. 确保当前代码已提交
git status
git add .
git commit -m "refactor: 重构前快照"

# 2. 创建重构分支
git checkout -b refactor/pc-ui-modularization

# 3. 创建文件备份
cp desktop/nicegui_app/pc_app.py desktop/nicegui_app/pc_app.py.backup
```

### 0.2 建立测试基线

创建功能验证清单：

```python
# desktop/nicegui_app/test_checklist.md

## 功能验证清单

### 项目管理
- [ ] 项目下拉框正常显示
- [ ] 可以切换项目
- [ ] 项目信息正确显示
- [ ] 可以创建项目
- [ ] 可以编辑项目
- [ ] 可以删除项目

### 工程结构树
- [ ] 树形结构正确显示
- [ ] 点击节点可以选中
- [ ] 搜索过滤正常工作
- [ ] 可以创建楼栋
- [ ] 可以编辑节点
- [ ] 可以删除节点

### 资产列表
- [ ] 资产列表正确显示
- [ ] 过滤器正常工作
- [ ] 点击行可以选中
- [ ] 关键词正确提取
- [ ] 可以上传资产
- [ ] 可以删除资产

### 资产详情
- [ ] 详情正确显示
- [ ] 图片预览正常工作
- [ ] OCR/LLM 按钮状态正确
- [ ] 打开原始文件功能正常
```

### 0.3 创建目录结构

```bash
# 创建模块目录
cd desktop/nicegui_app

mkdir -p api
mkdir -p ui/dialogs
mkdir -p state
mkdir -p utils

# 创建 __init__.py
touch api/__init__.py
touch ui/__init__.py
touch ui/dialogs/__init__.py
touch state/__init__.py
touch utils/__init__.py
```

---

## 🪜 阶段 1：API 客户端封装（低风险）

### 为什么从 API 开始？

1. ✅ **无 UI 依赖**：纯后端调用，不影响界面
2. ✅ **易于测试**：可以独立测试
3. ✅ **逐步替换**：可以逐个替换现有调用
4. ✅ **立即受益**：统一错误处理、日志记录

### 1.1 创建 API 客户端（不修改原文件）

**创建** `api/client.py`：

```python
"""
后端 API 客户端封装
提供统一的后端调用接口，便于测试和维护
"""

import httpx
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BackendClient:
    """后端 API 客户端"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Any:
        """
        统一的请求方法

        Args:
            method: HTTP 方法 (GET, POST, PATCH, DELETE)
            path: API 路径
            **kwargs: httpx.request 参数

        Returns:
            响应 JSON 数据

        Raises:
            httpx.HTTPError: 请求失败
        """
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"API 请求失败: {method} {url} - {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"API 请求错误: {method} {url} - {str(e)}")
            raise

    # ==================== 便捷方法 ====================

    async def get(self, path: str, params: Optional[Dict] = None) -> Any:
        """GET 请求"""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: Optional[Dict] = None, **kwargs) -> Any:
        """POST 请求"""
        return await self._request("POST", path, json=data, **kwargs)

    async def patch(self, path: str, data: Optional[Dict] = None) -> Any:
        """PATCH 请求"""
        return await self._request("PATCH", path, json=data)

    async def delete(self, path: str) -> Any:
        """DELETE 请求"""
        return await self._request("DELETE", path)

    # ==================== 项目 API ====================

    async def list_projects(self) -> List[Dict[str, Any]]:
        """
        获取项目列表

        Returns:
            项目列表
        """
        result = await self.get("/projects/")
        return result if isinstance(result, list) else []

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        获取项目详情

        Args:
            project_id: 项目 ID

        Returns:
            项目详情
        """
        return await self.get(f"/projects/{project_id}")

    async def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建项目

        Args:
            data: 项目数据

        Returns:
            创建的项目
        """
        return await self.post("/projects/", data=data)

    async def update_project(
        self,
        project_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新项目

        Args:
            project_id: 项目 ID
            data: 更新数据

        Returns:
            更新后的项目
        """
        return await self.patch(f"/projects/{project_id}", data=data)

    async def delete_project(
        self,
        project_id: str,
        reason: Optional[str] = None
    ) -> None:
        """
        删除项目

        Args:
            project_id: 项目 ID
            reason: 删除原因
        """
        params = {"reason": reason} if reason else None
        await self.delete(f"/projects/{project_id}")

    # ==================== 工程结构 API ====================

    async def get_structure_tree(self, project_id: str) -> Dict[str, Any]:
        """
        获取工程结构树

        Args:
            project_id: 项目 ID

        Returns:
            工程结构树数据
        """
        return await self.get(f"/projects/{project_id}/structure_tree")

    async def create_building(
        self,
        project_id: str,
        name: str
    ) -> Dict[str, Any]:
        """
        创建楼栋

        Args:
            project_id: 项目 ID
            name: 楼栋名称

        Returns:
            创建的楼栋
        """
        return await self.post(
            f"/projects/{project_id}/buildings",
            data={"name": name}
        )

    async def update_node(
        self,
        node_type: str,
        node_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新工程结构节点

        Args:
            node_type: 节点类型 (building/zone/system/device)
            node_id: 节点 ID
            data: 更新数据

        Returns:
            更新后的节点
        """
        return await self.patch(
            f"/engineering/{node_type}s/{node_id}",
            data=data
        )

    async def delete_node(
        self,
        node_type: str,
        node_id: str,
        reason: Optional[str] = None
    ) -> None:
        """
        删除工程结构节点

        Args:
            node_type: 节点类型
            node_id: 节点 ID
            reason: 删除原因
        """
        params = {"reason": reason} if reason else None
        await self.delete(f"/engineering/{node_type}s/{node_id}")

    # ==================== 资产 API ====================

    async def list_assets(
        self,
        device_id: Optional[str] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        获取资产列表

        Args:
            device_id: 设备 ID
            **filters: 过滤条件 (modality, content_role, etc.)

        Returns:
            资产列表
        """
        params = {k: v for k, v in filters.items() if v is not None}
        if device_id:
            params["device_id"] = device_id

        result = await self.get("/assets/", params=params)
        return result if isinstance(result, list) else []

    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        获取资产详情

        Args:
            asset_id: 资产 ID

        Returns:
            资产详情
        """
        return await self.get(f"/assets/{asset_id}")

    async def upload_image(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        device_id: str,
        title: Optional[str] = None,
        content_role: str = "meter",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传图片资产

        Args:
            file_data: 文件二进制数据
            filename: 文件名
            content_type: MIME 类型
            device_id: 关联设备 ID
            title: 资产标题
            content_role: 内容角色
            description: 描述

        Returns:
            上传的资产
        """
        # 构造 multipart/form-data
        files = {
            "file": (filename, file_data, content_type)
        }

        data = {
            "device_id": device_id,
            "content_role": content_role
        }

        if title:
            data["title"] = title
        if description:
            data["description"] = description

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/assets/upload_image_with_note",
                data=data,
                files=files
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_asset(self, asset_id: str) -> None:
        """
        删除资产

        Args:
            asset_id: 资产 ID
        """
        await self.delete(f"/assets/{asset_id}")

    # ==================== AI 分析 API ====================

    async def run_ocr(self, asset_id: str) -> Dict[str, Any]:
        """
        运行 OCR 分析

        Args:
            asset_id: 资产 ID

        Returns:
            OCR 结果
        """
        return await self.post(f"/assets/{asset_id}/run_ocr")

    async def run_scene_llm(self, asset_id: str) -> Dict[str, Any]:
        """
        运行场景 LLM 分析

        Args:
            asset_id: 资产 ID

        Returns:
            LLM 分析结果
        """
        return await self.post(f"/assets/{asset_id}/run_scene_llm")
```

### 1.2 测试 API 客户端

**创建** `tests/test_api_client.py`：

```python
"""
API 客户端单元测试
"""

import pytest
from desktop.nicegui_app.api.client import BackendClient


@pytest.mark.asyncio
async def test_list_projects():
    """测试获取项目列表"""
    client = BackendClient()
    projects = await client.list_projects()
    assert isinstance(projects, list)


@pytest.mark.asyncio
async def test_get_project():
    """测试获取项目详情"""
    client = BackendClient()
    # 假设存在至少一个项目
    projects = await client.list_projects()
    if projects:
        project = await client.get_project(projects[0]["id"])
        assert project["id"] == projects[0]["id"]
```

### 1.3 逐步替换（重要：不删除旧代码）

**策略**：新旧代码共存，逐个替换

```python
# 在 pc_app.py 顶部添加

# ==================== 新增：API 客户端 ====================
from desktop.nicegui_app.api.client import BackendClient

# 创建全局客户端实例
backend_client = BackendClient()

# 旧的 API 函数保留，但标记为 deprecated
async def fetch_json(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    @deprecated 请使用 backend_client.get() 代替
    """
    import warnings
    warnings.warn("fetch_json 已废弃，请使用 backend_client.get()", DeprecationWarning)
    return await backend_client.get(path, params=params)

async def list_projects() -> List[Dict[str, Any]]:
    """@deprecated 请使用 backend_client.list_projects() 代替"""
    return await backend_client.list_projects()

# ... 其他旧函数也保留
```

### 1.4 替换示例

**旧代码**：
```python
async def reload_projects_and_tree(selected_project_id: Optional[str] = None) -> None:
    try:
        projects = await list_projects()  # 旧方式
    except Exception:
        projects = []
```

**新代码**：
```python
async def reload_projects_and_tree(selected_project_id: Optional[str] = None) -> None:
    try:
        projects = await backend_client.list_projects()  # 新方式
    except Exception as e:
        logger.error(f"加载项目失败: {e}")
        projects = []
```

### 1.5 提交第一阶段

```bash
git add desktop/nicegui_app/api/
git add desktop/nicegui_app/pc_app.py
git commit -m "refactor(stage 1): 添加 API 客户端封装

- 创建 BackendClient 类统一 API 调用
- 保留旧函数以确保向后兼容
- 添加详细的错误处理和日志
- 不改变任何外部行为
```

---

## 🪜 阶段 2：状态管理（中风险）

### 2.1 理解当前状态管理

**当前方式**（问题）：
```python
def main_page():
    # 大量闭包变量
    selected_asset = None
    all_assets_for_device = []
    current_device_id = None
    projects_cache = []

    # 嵌套函数通过 nonlocal 修改
    def update_asset_detail():
        nonlocal selected_asset
        # ...
```

**问题**：
- 状态散落在各个闭包中
- 难以追踪状态变化
- 无法跨组件共享状态

### 2.2 创建状态管理（不修改原文件）

**创建** `state/store.py`：

```python
"""
全局状态管理
使用集中式状态管理替代闭包变量
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProjectState:
    """项目相关状态"""
    projects: List[Dict[str, Any]] = field(default_factory=list)
    current_project_id: Optional[str] = None
    loading: bool = False

    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """获取当前选中的项目"""
        if not self.current_project_id:
            return None
        for p in self.projects:
            if str(p.get("id")) == str(self.current_project_id):
                return p
        return None


@dataclass
class TreeState:
    """工程结构树状态"""
    all_nodes: List[Dict[str, Any]] = field(default_factory=list)
    filtered_nodes: List[Dict[str, Any]] = field(default_factory=list)
    search_query: str = ""
    selected_node_type: Optional[str] = None  # 'building', 'zone', 'system', 'device'
    selected_node_id: Optional[str] = None

    def apply_search_filter(self, query: str) -> None:
        """应用搜索过滤"""
        self.search_query = query.lower()

        if not query:
            self.filtered_nodes = self.all_nodes
            return

        def filter_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """递归过滤节点"""
            result = []
            for node in nodes:
                name = node.get("name", "").lower()
                if self.search_query in name:
                    result.append(node)
                elif "children" in node:
                    filtered_children = filter_nodes(node["children"])
                    if filtered_children:
                        # 复制节点并更新 children
                        new_node = node.copy()
                        new_node["children"] = filtered_children
                        result.append(new_node)
            return result

        self.filtered_nodes = filter_nodes(self.all_nodes)


@dataclass
class AssetState:
    """资产相关状态"""
    all_assets: List[Dict[str, Any]] = field(default_factory=list)
    filtered_assets: List[Dict[str, Any]] = field(default_factory=list)
    selected_asset: Optional[Dict[str, Any]] = None

    # 过滤条件
    filter_modality: str = ""
    filter_role: str = ""
    filter_time: str = "all"

    def set_assets(self, assets: List[Dict[str, Any]]) -> None:
        """设置资产列表"""
        self.all_assets = assets
        self.apply_filters()

    def apply_filters(self) -> None:
        """应用所有过滤条件"""
        filtered = self.all_assets.copy()

        # 类型过滤
        if self.filter_modality:
            filtered = [a for a in filtered if a.get("modality") == self.filter_modality]

        # 角色过滤
        if self.filter_role:
            filtered = [a for a in filtered if a.get("content_role") == self.filter_role]

        # 时间过滤
        if self.filter_time != "all":
            from datetime import datetime, timedelta
            now = datetime.now()
            if self.filter_time == "7d":
                cutoff = now - timedelta(days=7)
            elif self.filter_time == "30d":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = None

            if cutoff:
                filtered = [
                    a for a in filtered
                    if a.get("capture_time") and datetime.fromisoformat(a["capture_time"]) > cutoff
                ]

        self.filtered_assets = filtered


@dataclass
class AppState:
    """全局应用状态"""
    project: ProjectState = field(default_factory=ProjectState)
    tree: TreeState = field(default_factory=TreeState)
    asset: AssetState = field(default_factory=AssetState)

    def clear(self) -> None:
        """清空所有状态"""
        self.project = ProjectState()
        self.tree = TreeState()
        self.asset = AssetState()


# 全局单例
app_state = AppState()
```

### 2.3 渐进式迁移（重要：保持兼容）

**策略**：创建适配层，新旧状态共存

```python
# 在 main_page() 中添加

from desktop.nicegui_app.state.store import app_state

def main_page() -> None:
    # ... UI 组件创建 ...

    # 新状态
    # app_state 已经初始化

    # 旧状态保留（向后兼容）
    selected_asset = None
    all_assets_for_device = []
    current_device_id = None
    projects_cache = []

    # 创建适配器函数
    def sync_state_to_old_vars():
        """将新状态同步到旧变量（兼容层）"""
        nonlocal selected_asset, all_assets_for_device, projects_cache

        # 同步项目
        projects_cache = app_state.project.projects

        # 同步资产
        all_assets_for_device = app_state.asset.all_assets
        selected_asset = app_state.asset.selected_asset

    def sync_old_vars_to_state():
        """将旧变量同步到新状态（兼容层）"""
        app_state.project.projects = projects_cache
        app_state.asset.all_assets = all_assets_for_device
        app_state.asset.selected_asset = selected_asset

    # 逐步迁移函数，每次迁移一个
    async def reload_projects_and_tree_v2(selected_project_id: Optional[str] = None) -> None:
        """新版本：使用 app_state"""
        nonlocal projects_cache

        try:
            projects = await backend_client.list_projects()
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            projects = []

        # 更新新状态
        app_state.project.projects = projects

        # 同步到旧变量（兼容）
        projects_cache = projects

        # ... 其余逻辑
```

### 2.4 逐个函数迁移

**优先级**：

1. ✅ **只读函数优先**（不修改状态）
   - `get_current_project()` → `app_state.project.get_current_project()`
   - `apply_tree_filter()` → `app_state.tree.apply_search_filter()`

2. ✅ **简单写入函数**（修改少量状态）
   - `update_project_header()` → 使用 `app_state.project`

3. ⚠️ **复杂写入函数**（修改多个状态）
   - `reload_projects_and_tree()` → 最后迁移

---

## 🪜 阶段 3：UI 组件拆分（高风险）

### 3.1 嵌套函数处理策略

#### 策略 A：提取函数（最小改动）

**旧代码**：
```python
def main_page():
    # ... UI 创建 ...

    async def on_upload_asset_click() -> None:
        """197 行的嵌套函数"""
        dialog = ui.dialog()
        with dialog, ui.card():
            # ... 197 行代码 ...
```

**新代码**（分两步）：

**步骤 1**：提取到模块级函数（保持原有逻辑）
```python
# 在 pc_app.py 顶部添加

async def _handle_upload_asset_click(
    device_id: str,
    app_state: AppState,
    backend_client: BackendClient
) -> None:
    """
    处理上传资产点击事件

    Args:
        device_id: 当前设备 ID
        app_state: 应用状态
        backend_client: API 客户端
    """
    # 将原来的 197 行代码移到这里
    # 只需要修改变量引用

    dialog = ui.dialog()
    with dialog, ui.card():
        ui.label("上传图片资产").classes("text-h6 q-mb-md")

        # ... 其他代码 ...

        async def handle_upload():
            # 使用参数而不是闭包变量
            pass

        confirm_btn.on_click(handle_upload)

    dialog.open()
```

**步骤 2**：在 main_page 中调用
```python
def main_page():
    # ... UI 创建 ...

    upload_asset_button = ui.button("上传图片资产")

    # 旧方式（保留）
    # upload_asset_button.on_click(on_upload_asset_click)

    # 新方式
    upload_asset_button.on_click(
        lambda: _handle_upload_asset_click(
            current_device_id,
            app_state,
            backend_client
        )
    )
```

#### 策略 B：创建组件类（推荐，但改动较大）

**创建** `ui/dialogs/upload_dialog.py`：

```python
"""
上传对话框组件
"""

from nicegui import ui
from typing import Optional, Dict, Any, Callable
import inspect
from ..api.client import BackendClient
from ..state.store import AppState


class UploadDialog:
    """上传对话框组件"""

    def __init__(
        self,
        backend_client: BackendClient,
        app_state: AppState,
        on_success: Optional[Callable] = None
    ):
        """
        初始化对话框

        Args:
            backend_client: API 客户端
            app_state: 应用状态
            on_success: 上传成功回调
        """
        self.backend_client = backend_client
        self.app_state = app_state
        self.on_success = on_success

        # UI 组件
        self.dialog: Optional[ui.dialog] = None
        self.file_info_label: Optional[ui.label] = None

        # 文件缓存
        self.selected_file = {
            "name": None,
            "content": None,
            "type": None
        }

    def show(self, device_id: str) -> None:
        """
        显示对话框

        Args:
            device_id: 关联设备 ID
        """
        self.dialog = ui.dialog()

        with self.dialog, ui.card():
            self._render_content(device_id)

        self.dialog.open()

    def _render_content(self, device_id: str) -> None:
        """渲染对话框内容"""
        ui.label("上传图片资产").classes("text-h6 q-mb-md")

        # 表单
        name_input = ui.input(label="资产标题")
        role_select = ui.select({
            "meter": "仪表",
            "scene_issue": "现场问题",
            "nameplate": "铭牌",
        }, value="meter", label="内容角色")
        note_input = ui.input(label="工程师备注")

        self.file_info_label = ui.label("")

        # 文件上传
        upload_component = ui.upload(
            label="选择图片文件",
            auto_upload=True,
            on_upload=lambda e: self._on_file_upload(e),
        ).props('accept="image/*"')

        # 按钮
        with ui.row().classes("q-mt-md q-gutter-sm justify-end"):
            cancel_btn = ui.button("取消")
            confirm_btn = ui.button("确认上传", color="primary")

        cancel_btn.on_click(self.dialog.close)
        confirm_btn.on_click(
            lambda: self._handle_upload(
                device_id,
                name_input.value,
                role_select.value,
                note_input.value
            )
        )

    async def _on_file_upload(self, e: Any) -> None:
        """文件上传回调"""
        try:
            file_bytes = b""
            file_name = None
            file_type = None

            # 处理不同的 API 版本
            if hasattr(e, "content") and getattr(e, "content") is not None:
                content_obj = getattr(e, "content")
                if hasattr(content_obj, "read"):
                    result = content_obj.read()
                    if inspect.iscoroutine(result):
                        result = await result
                    file_bytes = result or b""
                file_name = getattr(e, "name", None)
                file_type = getattr(e, "type", None)

            # 保存到缓存
            self.selected_file["name"] = file_name
            self.selected_file["content"] = file_bytes
            self.selected_file["type"] = file_type

            # 更新 UI
            if file_bytes:
                self.file_info_label.text = f"已选择: {file_name}"
                ui.notify("文件已选择，请填写表单后点击确认上传", color="positive")

        except Exception as exc:
            import traceback
            traceback.print_exc()
            ui.notify(f"文件读取失败: {exc}", color="negative")

    async def _handle_upload(
        self,
        device_id: str,
        title: Optional[str],
        content_role: str,
        description: Optional[str]
    ) -> None:
        """处理上传"""
        if not self.selected_file.get("content"):
            ui.notify("请先选择一个文件并等待上传完成", color="warning")
            return

        file_name = self.selected_file.get("name") or "uploaded_image"
        file_bytes = self.selected_file.get("content")
        file_mime = self.selected_file.get("type") or "application/octet-stream"

        try:
            # 调用 API 上传
            result = await self.backend_client.upload_image(
                file_data=file_bytes,
                filename=file_name,
                content_type=file_mime,
                device_id=device_id,
                title=title,
                content_role=content_role,
                description=description
            )

            ui.notify("上传成功", color="positive")

            # 清理缓存
            self.selected_file = {"name": None, "content": None, "type": None}

            # 关闭对话框
            self.dialog.close()

            # 触发回调
            if self.on_success:
                await self.on_success(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            ui.notify(f"上传失败: {e}", color="negative")
```

**在 main_page 中使用**：
```python
def main_page() -> None:
    # ... UI 创建 ...

    from desktop.nicegui_app.ui.dialogs.upload_dialog import UploadDialog

    upload_dialog = UploadDialog(
        backend_client=backend_client,
        app_state=app_state,
        on_success=lambda result: ui.notify(f"上传成功: {result['id']}", color="positive")
    )

    upload_asset_button = ui.button("上传图片资产")
    upload_asset_button.on_click(lambda: upload_dialog.show(current_device_id))
```

### 3.2 组件拆分优先级

**低风险 → 高风险**：

1. ✅ **独立对话框**（无状态依赖）
   - `ProjectDialog`
   - `UploadDialog`
   - `PreviewDialog`

2. ✅ **只读组件**（无状态修改）
   - `AssetList`（显示部分）
   - `ProjectPanel`（显示部分）

3. ⚠️ **状态修改组件**
   - `TreePanel`
   - `AssetDetail`

4. 🔴 **核心布局组件**
   - `MainLayout`（最后处理）

---

## 🪜 阶段 4：主应用简化（最后一步）

### 4.1 目标结构

**重构前**（1629 行）：
```python
# pc_app.py

async def fetch_json(path): ...
async def list_projects(): ...
# ... 8 个辅助函数 ...

def main_page():
    """1426 行的巨无霸"""
    # UI 创建
    # 24 个嵌套函数
    # ...

def index_page(): ...
```

**重构后**（~200 行）：
```python
# pc_app.py

from nicegui import ui, app
from pathlib import Path
import sys

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# 配置
from shared.config.settings import get_settings
from .api.client import BackendClient
from .state.store import app_state
from .ui.main_layout import MainLayout

SETTINGS = get_settings()
UI_VERSION = "PC UI v0.4.0 (重构版)"

# 静态文件
app.add_static_files("/local_assets", SETTINGS.local_storage_dir)

# 初始化
backend_client = BackendClient()

def main_page() -> None:
    """主页面（简化版）"""
    layout = MainLayout(backend_client, app_state)
    layout.render()

def index_page() -> None:
    """索引页面"""
    ui.label("Redirecting...").classes("text-grey")
    ui.run_javascript("window.location.href = '/'")

# 路由
app.add_page("/", main_page)
app.add_page("/index", index_page)

if __name__ == "__main__":
    ui.run(title="BDC-AI PC UI", port=8080)
```

---

## 🔄 每个阶段的标准流程

### 1. 创建新代码
- ✅ 不修改原文件
- ✅ 新建模块文件
- ✅ 实现新功能

### 2. 添加兼容层
- ✅ 保留旧函数/类
- ✅ 创建适配器
- ✅ 标记 @deprecated

### 3. 逐步迁移
- ✅ 一个函数一个函数迁移
- ✅ 每次迁移后测试
- ✅ 保留旧代码备份

### 4. 提交代码
- ✅ 频繁提交（每个函数一次）
- ✅ 详细的 commit message
- ✅ 推送到远程分支

### 5. 测试验证
- ✅ 功能验证清单
- ✅ 回归测试
- ✅ 性能测试

---

## 🚨 风险应对预案

### 场景 1：功能异常

**症状**：重构后某个功能不工作

**处理**：
```bash
# 1. 立即回滚到上一个 commit
git reset --hard HEAD~1

# 2. 分析问题
# 3. 修复后再次提交
```

### 场景 2：状态丢失

**症状**：用户刷新页面后状态丢失

**处理**：
- 添加状态持久化（localStorage）
- 实现状态恢复机制

### 场景 3：性能下降

**症状**：页面响应变慢

**处理**：
- 使用性能分析工具
- 优化热路径代码
- 添加缓存机制

---

## 📊 进度跟踪

创建重构进度表：

```markdown
## 重构进度

### 阶段 1：API 客户端（完成度：0%）
- [ ] 创建 BackendClient 类
- [ ] 实现项目 API
- [ ] 实现工程结构 API
- [ ] 实现资产 API
- [ ] 单元测试
- [ ] 逐步替换旧调用

### 阶段 2：状态管理（完成度：0%）
- [ ] 创建 AppState 类
- [ ] 迁移项目状态
- [ ] 迁移树状态
- [ ] 迁移资产状态
- [ ] 删除旧闭包变量

### 阶段 3：UI 组件（完成度：0%）
- [ ] 提取对话框组件
- [ ] 提取面板组件
- [ ] 提取列表组件
- [ ] 提取详情组件

### 阶段 4：主应用（完成度：0%）
- [ ] 简化 main_page
- [ ] 整合所有组件
- [ ] 清理旧代码
```

---

**文档创建时间**：2025-01-22
**版本**：v1.0
