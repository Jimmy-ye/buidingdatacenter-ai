"""
API 客户端单元测试
测试 BackendClient 的各个 API 方法

运行测试: pytest tests/test_api_client.py -v
"""

import pytest
from desktop.nicegui_app.api.client import BackendClient


@pytest.mark.asyncio
async def test_client_initialization():
    """测试客户端初始化"""
    client = BackendClient()
    assert client.base_url == "http://127.0.0.1:8000/api/v1"
    assert client.timeout == 30.0


@pytest.mark.asyncio
async def test_list_projects():
    """测试获取项目列表"""
    client = BackendClient()
    projects = await client.list_projects()
    assert isinstance(projects, list)
    # 如果有项目，验证结构
    if projects:
        project = projects[0]
        assert "id" in project
        assert "name" in project


@pytest.mark.asyncio
async def test_get_project():
    """测试获取项目详情"""
    client = BackendClient()
    projects = await client.list_projects()

    if projects:
        project_id = projects[0]["id"]
        project = await client.get_project(project_id)
        assert project["id"] == project_id


@pytest.mark.asyncio
async def test_get_structure_tree():
    """测试获取工程结构树"""
    client = BackendClient()
    projects = await client.list_projects()

    if projects:
        project_id = projects[0]["id"]
        tree = await client.get_structure_tree(project_id)
        assert isinstance(tree, dict)
        # 验证树结构
        assert "nodes" in tree or "tree" in tree


@pytest.mark.asyncio
async def test_list_assets():
    """测试获取资产列表"""
    client = BackendClient()

    # 测试不带过滤的查询
    assets = await client.list_assets()
    assert isinstance(assets, list)

    # 测试带过滤的查询
    filtered_assets = await client.list_assets(modality="image")
    assert isinstance(filtered_assets, list)


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    client = BackendClient()

    # 测试 404 错误
    with pytest.raises(Exception):  # httpx.HTTPError
        await client.get_project("non-existent-id")

    # 测试无效路径
    with pytest.raises(Exception):
        await client.get("/invalid/path")


# ==================== 集成测试示例 ====================

@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整的业务流程（集成测试）"""
    client = BackendClient()

    # 1. 获取项目列表
    projects = await client.list_projects()
    assert isinstance(projects, list)

    if not projects:
        pytest.skip("没有可用的项目进行集成测试")

    # 2. 选择第一个项目
    project = projects[0]
    project_id = project["id"]

    # 3. 获取工程结构树
    tree = await client.get_structure_tree(project_id)
    assert isinstance(tree, dict)

    # 4. 获取资产列表
    assets = await client.list_assets()
    assert isinstance(assets, list)

    # 5. 如果有资产，测试获取详情
    if assets:
        asset = await client.get_asset(assets[0]["id"])
        assert asset["id"] == assets[0]["id"]


if __name__ == "__main__":
    # 运行测试
    import sys
    pytest.main([__file__, "-v"] + sys.argv[1:])
