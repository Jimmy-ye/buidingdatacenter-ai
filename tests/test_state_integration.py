"""
状态管理与 PC UI 集成测试

验证状态管理与旧代码的兼容性

运行测试: pytest tests/test_state_integration.py -v
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


def test_app_state_singleton_consistency():
    """测试全局单例的一致性"""
    from desktop.nicegui_app.state.store import app_state as app_state2

    # 应该是同一个实例
    assert app_state is app_state2
    assert id(app_state) == id(app_state2)


def test_state_compatibility_with_old_code():
    """测试状态管理与旧代码的兼容性"""
    # 模拟旧代码使用的变量结构
    projects_cache = []
    full_tree_nodes = []
    selected_asset = None
    all_assets_for_device = []
    current_device_id = None
    current_tree_node_type = None
    current_tree_node_id = None

    # 测试数据
    test_projects = [
        {"id": "1", "name": "Project A"},
        {"id": "2", "name": "Project B"}
    ]

    test_tree = [
        {
            "id": "node-1",
            "name": "Building A",
            "type": "building",
            "children": []
        }
    ]

    test_assets = [
        {"id": "asset-1", "title": "Asset A"},
        {"id": "asset-2", "title": "Asset B"}
    ]

    # 模拟 sync_old_vars_to_state() 逻辑
    app_state.project.set_projects(test_projects)
    app_state.project.set_current_project("1")
    app_state.tree.set_nodes(test_tree)
    app_state.tree.set_selected_node("building", "node-1")
    app_state.asset.set_assets(test_assets)
    app_state.asset.set_selected_asset(test_assets[0])
    app_state.asset.current_device_id = "device-1"

    # 模拟 sync_state_to_old_vars() 逻辑
    projects_cache = app_state.project.projects
    full_tree_nodes = app_state.tree.all_nodes
    current_tree_node_type = app_state.tree.selected_node_type
    current_tree_node_id = app_state.tree.selected_node_id
    all_assets_for_device = app_state.asset.all_assets
    selected_asset = app_state.asset.selected_asset
    current_device_id = app_state.asset.current_device_id

    # 验证同步结果
    assert len(projects_cache) == 2
    assert projects_cache[0]["name"] == "Project A"
    assert len(full_tree_nodes) == 1
    assert full_tree_nodes[0]["name"] == "Building A"
    assert current_tree_node_type == "building"
    assert current_tree_node_id == "node-1"
    assert len(all_assets_for_device) == 2
    assert selected_asset["title"] == "Asset A"
    assert current_device_id == "device-1"


def test_state_clear_and_reinitialize():
    """测试状态清空和重新初始化"""
    # 设置一些初始数据
    app_state.project.set_projects([{"id": "1", "name": "Test"}])
    app_state.project.set_current_project("1")
    app_state.asset.set_assets([{"id": "1", "title": "Test"}])

    # 验证已设置
    assert len(app_state.project.projects) == 1
    assert app_state.project.current_project_id == "1"

    # 清空
    app_state.clear()

    # 验证已清空
    assert len(app_state.project.projects) == 0
    assert app_state.project.current_project_id is None
    assert len(app_state.asset.all_assets) == 0


def test_state_filter_functionality():
    """测试过滤功能"""
    # 设置测试数据
    assets = [
        {"id": "1", "title": "Asset A", "modality": "image", "content_role": "meter"},
        {"id": "2", "title": "Asset B", "modality": "table", "content_role": "scene_issue"},
        {"id": "3", "title": "Asset C", "modality": "image", "content_role": "nameplate"},
    ]
    app_state.asset.set_assets(assets)

    # 初始不过滤
    assert len(app_state.asset.filtered_assets) == 3

    # 过滤类型
    app_state.asset.set_filter_modality("image")
    assert len(app_state.asset.filtered_assets) == 2
    assert all(a["modality"] == "image" for a in app_state.asset.filtered_assets)

    # 清空类型过滤
    app_state.asset.set_filter_modality("")
    assert len(app_state.asset.filtered_assets) == 3

    # 过滤角色
    app_state.asset.set_filter_role("meter")
    assert len(app_state.asset.filtered_assets) == 1
    assert app_state.asset.filtered_assets[0]["content_role"] == "meter"


def test_tree_search_functionality():
    """测试树搜索功能"""
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
    app_state.tree.set_nodes(nodes)

    # 初始不过滤
    assert len(app_state.tree.filtered_nodes) == 2

    # 搜索 "Building A"
    app_state.tree.apply_search_filter("Building A")
    assert len(app_state.tree.filtered_nodes) == 1
    assert app_state.tree.filtered_nodes[0]["name"] == "Building A"

    # 搜索 "Floor"
    app_state.tree.apply_search_filter("Floor")
    assert len(app_state.tree.filtered_nodes) == 1
    # 应该保留 Building A，因为它包含匹配的子节点

    # 清空搜索
    app_state.tree.apply_search_filter("")
    assert len(app_state.tree.filtered_nodes) == 2


def test_helper_functions():
    """测试快捷方式函数"""
    # 设置测试数据
    app_state.project.set_projects([{"id": "1", "name": "Test Project"}])
    app_state.project.set_current_project("1")

    asset = {"id": "asset-1", "title": "Test Asset"}
    app_state.asset.set_selected_asset(asset)

    # 测试 get_current_project
    project = get_current_project()
    assert project is not None
    assert project["name"] == "Test Project"

    # 测试 get_selected_asset
    selected = get_selected_asset()
    assert selected is not None
    assert selected["title"] == "Test Asset"

    # 测试 get_selected_node (未设置)
    node = get_selected_node()
    assert node is None

    # 设置节点后测试
    app_state.tree.set_nodes([{"id": "node-1", "name": "Test Node"}])
    app_state.tree.set_selected_node("test", "node-1")
    node = get_selected_node()
    assert node is not None
    assert node["name"] == "Test Node"


def test_state_summary():
    """测试状态摘要功能"""
    # 设置测试数据
    app_state.project.set_projects([{"id": "1", "name": "A"}, {"id": "2", "name": "B"}])
    app_state.project.set_current_project("1")
    app_state.tree.set_nodes([{"id": "1"}, {"id": "2"}])
    app_state.asset.set_assets([{"id": "1"}, {"id": "2"}, {"id": "3"}])
    app_state.asset.set_selected_asset({"id": "1"})

    # 获取摘要
    summary = app_state.get_summary()

    assert summary["projects"]["count"] == 2
    assert summary["projects"]["current"] == "1"
    assert summary["tree"]["total_nodes"] == 2
    assert summary["tree"]["filtered_nodes"] == 2
    assert summary["assets"]["total"] == 3
    assert summary["assets"]["selected"] == "1"


if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v"] + sys.argv[1:])
