"""
全局状态管理模块

使用集中式状态管理替代分散的闭包变量

版本: v1.0
创建时间: 2025-01-22
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ==================== 项目状态 ====================

@dataclass
class ProjectState:
    """项目相关状态"""

    # 数据
    projects: List[Dict[str, Any]] = field(default_factory=list)
    current_project_id: Optional[str] = None

    # UI 状态
    loading: bool = False
    error_message: Optional[str] = None

    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """
        获取当前选中的项目

        Returns:
            当前项目，如果未选择返回 None
        """
        if not self.current_project_id:
            return None
        for p in self.projects:
            if str(p.get("id")) == str(self.current_project_id):
                return p
        return None

    def set_projects(self, projects: List[Dict[str, Any]]) -> None:
        """
        设置项目列表

        Args:
            projects: 项目列表
        """
        self.projects = projects

    def set_current_project(self, project_id: Optional[str]) -> None:
        """
        设置当前选中的项目

        Args:
            project_id: 项目 ID
        """
        self.current_project_id = project_id

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取项目

        Args:
            project_id: 项目 ID

        Returns:
            项目对象，未找到返回 None
        """
        for p in self.projects:
            if str(p.get("id")) == str(project_id):
                return p
        return None


# ==================== 工程结构树状态 ====================

@dataclass
class TreeState:
    """工程结构树相关状态"""

    # 数据
    all_nodes: List[Dict[str, Any]] = field(default_factory=list)
    filtered_nodes: List[Dict[str, Any]] = field(default_factory=list)

    # 搜索和选择
    search_query: str = ""
    selected_node_type: Optional[str] = None  # 'building', 'zone', 'system', 'device'
    selected_node_id: Optional[str] = None

    # UI 状态
    loading: bool = False
    expanded_node_ids: set = field(default_factory=set)

    def set_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """
        设置树节点

        Args:
            nodes: 完整的树节点列表
        """
        self.all_nodes = nodes
        # 初始时不过滤
        self.filtered_nodes = nodes

    def apply_search_filter(self, query: str) -> None:
        """
        应用搜索过滤

        Args:
            query: 搜索关键词
        """
        self.search_query = query.lower()

        if not query:
            self.filtered_nodes = self.all_nodes
            return

        def filter_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """
            递归过滤节点

            保留匹配的节点及其父节点
            """
            result = []
            for node in nodes:
                name = node.get("name", "").lower()
                # 节点名称匹配
                name_matches = self.search_query in name

                # 递归检查子节点
                children = node.get("children", [])
                if children:
                    filtered_children = filter_nodes(children)
                    has_matching_children = len(filtered_children) > 0
                else:
                    filtered_children = []
                    has_matching_children = False

                # 保留节点如果：名称匹配 或 有匹配的子节点
                if name_matches or has_matching_children:
                    new_node = node.copy()
                    if children:
                        new_node["children"] = filtered_children
                    result.append(new_node)

            return result

        self.filtered_nodes = filter_nodes(self.all_nodes)

    def set_selected_node(self, node_type: Optional[str], node_id: Optional[str]) -> None:
        """
        设置选中的节点

        Args:
            node_type: 节点类型
            node_id: 节点 ID
        """
        self.selected_node_type = node_type
        self.selected_node_id = node_id

    def get_selected_node(self) -> Optional[Dict[str, Any]]:
        """
        获取选中的节点

        Returns:
            选中的节点对象
        """
        if not self.selected_node_id:
            return None

        def find_node(nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
            """递归查找节点"""
            for node in nodes:
                if node.get("id") == self.selected_node_id:
                    return node
                children = node.get("children", [])
                if children:
                    result = find_node(children)
                    if result:
                        return result
            return None

        return find_node(self.filtered_nodes)

    def toggle_expanded(self, node_id: str) -> None:
        """
        切换节点展开/折叠状态

        Args:
            node_id: 节点 ID
        """
        if node_id in self.expanded_node_ids:
            self.expanded_node_ids.remove(node_id)
        else:
            self.expanded_node_ids.add(node_id)


# ==================== 资产状态 ====================

@dataclass
class AssetState:
    """资产相关状态"""

    # 数据
    all_assets: List[Dict[str, Any]] = field(default_factory=list)
    filtered_assets: List[Dict[str, Any]] = field(default_factory=list)
    selected_asset: Optional[Dict[str, Any]] = None

    # 当前设备
    current_device_id: Optional[str] = None

    # 过滤条件
    filter_modality: str = ""
    filter_role: str = ""
    filter_time: str = "all"

    # UI 状态
    loading: bool = False

    def set_assets(self, assets: List[Dict[str, Any]]) -> None:
        """
        设置资产列表

        Args:
            assets: 资产列表
        """
        self.all_assets = assets
        self.apply_filters()

    def apply_filters(self) -> None:
        """
        应用所有过滤条件
        """
        filtered = self.all_assets.copy()

        # 类型过滤
        if self.filter_modality:
            filtered = [a for a in filtered if a.get("modality") == self.filter_modality]

        # 角色过滤
        if self.filter_role:
            filtered = [a for a in filtered if a.get("content_role") == self.filter_role]

        # 时间过滤
        if self.filter_time != "all":
            cutoff = None
            now = datetime.now()

            if self.filter_time == "7d":
                cutoff = now - timedelta(days=7)
            elif self.filter_time == "30d":
                cutoff = now - timedelta(days=30)

            if cutoff:
                filtered = [
                    a for a in filtered
                    if a.get("capture_time")
                ]

        self.filtered_assets = filtered

    def set_filter_modality(self, modality: str) -> None:
        """
        设置类型过滤

        Args:
            modality: 资产类型 (image/table/document)
        """
        self.filter_modality = modality
        self.apply_filters()

    def set_filter_role(self, role: str) -> None:
        """
        设置角色过滤

        Args:
            role: 内容角色 (meter/scene_issue/nameplate)
        """
        self.filter_role = role
        self.apply_filters()

    def set_filter_time(self, time_range: str) -> None:
        """
        设置时间过滤

        Args:
            time_range: 时间范围 (all/7d/30d)
        """
        self.filter_time = time_range
        self.apply_filters()

    def get_selected_asset(self) -> Optional[Dict[str, Any]]:
        """
        获取选中的资产

        Returns:
            选中的资产对象
        """
        return self.selected_asset

    def set_selected_asset(self, asset: Optional[Dict[str, Any]]) -> None:
        """
        设置选中的资产

        Args:
            asset: 资产对象
        """
        self.selected_asset = asset

    def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取资产

        Args:
            asset_id: 资产 ID

        Returns:
            资产对象，未找到返回 None
        """
        for asset in self.all_assets:
            if str(asset.get("id")) == str(asset_id):
                return asset
        return None


# ==================== 全局应用状态 ====================

@dataclass
class AppState:
    """
    全局应用状态

    使用集中式状态管理，替代分散的闭包变量
    """

    project: ProjectState = field(default_factory=ProjectState)
    tree: TreeState = field(default_factory=TreeState)
    asset: AssetState = field(default_factory=AssetState)

    def clear(self) -> None:
        """
        清空所有状态
        """
        self.project = ProjectState()
        self.tree = TreeState()
        self.asset = AssetState()

    def get_summary(self) -> Dict[str, Any]:
        """
        获取状态摘要

        Returns:
            状态摘要字典
        """
        return {
            "projects": {
                "count": len(self.project.projects),
                "current": self.project.current_project_id,
            },
            "tree": {
                "total_nodes": len(self.tree.all_nodes),
                "filtered_nodes": len(self.tree.filtered_nodes),
                "selected": f"{self.tree.selected_node_type}:{self.tree.selected_node_id}",
            },
            "assets": {
                "total": len(self.asset.all_assets),
                "filtered": len(self.asset.filtered_assets),
                "selected": self.asset.selected_asset.get("id") if self.asset.selected_asset else None,
            },
        }


# ==================== 全局单例 ====================

# 创建全局状态实例
app_state = AppState()


# ==================== 辅助函数 ====================

def get_current_project() -> Optional[Dict[str, Any]]:
    """快捷方式：获取当前项目"""
    return app_state.project.get_current_project()


def get_selected_asset() -> Optional[Dict[str, Any]]:
    """快捷方式：获取选中的资产"""
    return app_state.asset.get_selected_asset()


def get_selected_node() -> Optional[Dict[str, Any]]:
    """快捷方式：获取选中的树节点"""
    return app_state.tree.get_selected_node()
