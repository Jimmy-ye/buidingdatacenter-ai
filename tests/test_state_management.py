"""
状态管理模块单元测试

运行测试: pytest tests/test_state_management.py -v
"""

import pytest
from desktop.nicegui_app.state.store import (
    AppState,
    ProjectState,
    TreeState,
    AssetState,
    app_state,
    get_current_project,
    get_selected_asset,
    get_selected_node
)


# ==================== ProjectState 测试 ====================

def test_project_state_initialization():
    """测试项目状态初始化"""
    state = ProjectState()
    assert state.projects == []
    assert state.current_project_id is None
    assert state.loading is False
    assert state.error_message is None


def test_project_state_set_projects():
    """测试设置项目列表"""
    state = ProjectState()
    projects = [
        {"id": "1", "name": "Project A"},
        {"id": "2", "name": "Project B"}
    ]
    state.set_projects(projects)
    assert len(state.projects) == 2
    assert state.projects == projects


def test_project_state_set_current_project():
    """测试设置当前项目"""
    state = ProjectState()
    state.set_current_project("test-id")
    assert state.current_project_id == "test-id"


def test_project_state_get_current_project():
    """测试获取当前项目"""
    state = ProjectState()
    projects = [
        {"id": "1", "name": "Project A"},
        {"id": "2", "name": "Project B"}
    ]
    state.set_projects(projects)
    state.set_current_project("2")

    project = state.get_current_project()
    assert project is not None
    assert project["id"] == "2"
    assert project["name"] == "Project B"


def test_project_state_get_project_by_id():
    """测试根据 ID 获取项目"""
    state = ProjectState()
    projects = [
        {"id": "1", "name": "Project A"},
        {"id": "2", "name": "Project B"}
    ]
    state.set_projects(projects)

    # 找到存在的项目
    project = state.get_project_by_id("1")
    assert project is not None
    assert project["name"] == "Project A"

    # 找不到的项目
    project = state.get_project_by_id("999")
    assert project is None


# ==================== TreeState 测试 ====================

def test_tree_state_initialization():
    """测试树状态初始化"""
    state = TreeState()
    assert state.all_nodes == []
    assert state.filtered_nodes == []
    assert state.search_query == ""
    assert state.selected_node_type is None
    assert state.selected_node_id is None


def test_tree_state_set_nodes():
    """测试设置树节点"""
    state = TreeState()
    nodes = [
        {"id": "1", "name": "Building A", "children": []},
        {"id": "2", "name": "Building B", "children": []}
    ]
    state.set_nodes(nodes)
    assert len(state.all_nodes) == 2
    assert state.filtered_nodes == nodes  # 初始时不过滤


def test_tree_state_apply_search_filter():
    """测试搜索过滤"""
    state = TreeState()
    nodes = [
        {
            "id": "1",
            "name": "Building A",
            "children": [
                {"id": "1-1", "name": "Floor 1", "children": []}
            ]
        },
        {
            "id": "2",
            "name": "Building B",
            "children": []
        }
    ]
    state.set_nodes(nodes)

    # 搜索 "Building A"
    state.apply_search_filter("Building A")
    assert len(state.filtered_nodes) == 1
    assert state.filtered_nodes[0]["name"] == "Building A"

    # 清空搜索
    state.apply_search_filter("")
    assert len(state.filtered_nodes) == 2


def test_tree_state_set_selected_node():
    """测试设置选中节点"""
    state = TreeState()
    state.set_selected_node("device", "device-123")
    assert state.selected_node_type == "device"
    assert state.selected_node_id == "device-123"


def test_tree_state_toggle_expanded():
    """测试切换展开/折叠"""
    state = TreeState()
    state.toggle_expanded("node-1")
    assert "node-1" in state.expanded_node_ids

    state.toggle_expanded("node-1")
    assert "node-1" not in state.expanded_node_ids


# ==================== AssetState 测试 ====================

def test_asset_state_initialization():
    """测试资产状态初始化"""
    state = AssetState()
    assert state.all_assets == []
    assert state.filtered_assets == []
    assert state.selected_asset is None
    assert state.current_device_id is None
    assert state.filter_modality == ""
    assert state.filter_role == ""
    assert state.filter_time == "all"


def test_asset_state_set_assets():
    """测试设置资产列表"""
    state = AssetState()
    assets = [
        {"id": "1", "title": "Asset A", "modality": "image"},
        {"id": "2", "title": "Asset B", "modality": "table"}
    ]
    state.set_assets(assets)
    assert len(state.all_assets) == 2
    assert len(state.filtered_assets) == 2  # 初始时不过滤


def test_asset_state_filter_modality():
    """测试类型过滤"""
    state = AssetState()
    assets = [
        {"id": "1", "title": "Asset A", "modality": "image"},
        {"id": "2", "title": "Asset B", "modality": "table"},
        {"id": "3", "title": "Asset C", "modality": "image"}
    ]
    state.set_assets(assets)

    # 过滤图片类型
    state.set_filter_modality("image")
    assert len(state.filtered_assets) == 2
    assert all(a["modality"] == "image" for a in state.filtered_assets)


def test_asset_state_filter_role():
    """测试角色过滤"""
    state = AssetState()
    assets = [
        {"id": "1", "title": "Asset A", "content_role": "meter"},
        {"id": "2", "title": "Asset B", "content_role": "scene_issue"}
    ]
    state.set_assets(assets)

    # 过滤仪表角色
    state.set_filter_role("meter")
    assert len(state.filtered_assets) == 1
    assert state.filtered_assets[0]["content_role"] == "meter"


def test_asset_state_set_selected_asset():
    """测试设置选中资产"""
    state = AssetState()
    asset = {"id": "1", "title": "Asset A"}
    state.set_selected_asset(asset)
    assert state.selected_asset == asset


def test_asset_state_get_asset_by_id():
    """测试根据 ID 获取资产"""
    state = AssetState()
    assets = [
        {"id": "1", "title": "Asset A"},
        {"id": "2", "title": "Asset B"}
    ]
    state.set_assets(assets)

    # 找到存在的资产
    asset = state.get_asset_by_id("1")
    assert asset is not None
    assert asset["title"] == "Asset A"

    # 找不到的资产
    asset = state.get_asset_by_id("999")
    assert asset is None


# ==================== AppState 测试 ====================

def test_app_state_initialization():
    """测试应用状态初始化"""
    state = AppState()
    assert isinstance(state.project, ProjectState)
    assert isinstance(state.tree, TreeState)
    assert isinstance(state.asset, AssetState)


def test_app_state_clear():
    """测试清空状态"""
    state = AppState()
    # 添加一些数据
    state.project.set_projects([{"id": "1", "name": "Test"}])
    state.project.set_current_project("1")
    state.asset.set_assets([{"id": "1", "title": "Test"}])

    # 清空
    state.clear()

    # 验证已清空
    assert state.project.projects == []
    assert state.project.current_project_id is None
    assert state.asset.all_assets == []


def test_app_state_get_summary():
    """测试获取状态摘要"""
    state = AppState()
    state.project.set_projects([{"id": "1", "name": "Test"}])
    state.project.set_current_project("1")
    state.asset.set_assets([{"id": "1", "title": "Test"}])

    summary = state.get_summary()
    assert summary["projects"]["count"] == 1
    assert summary["projects"]["current"] == "1"
    assert summary["assets"]["total"] == 1


# ==================== 全局单例测试 ====================

def test_app_state_singleton():
    """测试全局单例"""
    from desktop.nicegui_app.state.store import app_state as app_state2

    # 应该是同一个实例
    assert app_state is app_state2


def test_get_current_project():
    """测试快捷方式获取当前项目"""
    state = AppState()
    projects = [{"id": "1", "name": "Test"}]
    state.project.set_projects(projects)
    state.project.set_current_project("1")

    # 替换全局单例（仅用于测试）
    import desktop.nicegui_app.state.store as store_module
    original_state = store_module.app_state
    store_module.app_state = state

    try:
        project = get_current_project()
        assert project is not None
        assert project["id"] == "1"
    finally:
        # 恢复原始状态
        store_module.app_state = original_state


def test_get_selected_asset():
    """测试快捷方式获取选中资产"""
    state = AppState()
    asset = {"id": "1", "title": "Test"}
    state.asset.set_selected_asset(asset)

    # 替换全局单例（仅用于测试）
    import desktop.nicegui_app.state.store as store_module
    original_state = store_module.app_state
    store_module.app_state = state

    try:
        result = get_selected_asset()
        assert result == asset
    finally:
        store_module.app_state = original_state


if __name__ == "__main__":
    # 运行测试
    import sys
    pytest.main([__file__, "-v"] + sys.argv[1:])
