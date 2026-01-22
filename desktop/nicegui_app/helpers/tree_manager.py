"""
工程结构树管理模块

提供工程结构树的过滤、搜索和管理逻辑

版本: v1.0
创建时间: 2025-01-22
"""

from typing import Any, Dict, List, Optional


class TreeFilterHelper:
    """
    树节点过滤辅助类

    提供树节点的搜索和过滤功能
    """

    @staticmethod
    def filter_nodes_by_text(
        nodes: List[Dict[str, Any]],
        search_text: str
    ) -> List[Dict[str, Any]]:
        """
        根据搜索文本过滤树节点

        Args:
            nodes: 树节点列表
            search_text: 搜索文本（不区分大小写）

        Returns:
            过滤后的树节点列表
        """
        if not nodes:
            return []

        text = search_text.strip().lower()
        if not text:
            return nodes

        def filter_node(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """递归过滤节点"""
            label = str(node.get("label") or "").lower()
            children = node.get("children") or []
            filtered_children: List[Dict[str, Any]] = []

            # 递归过滤子节点
            for child in children:
                filtered = filter_node(child)
                if filtered is not None:
                    filtered_children.append(filtered)

            # 如果节点标签匹配或有匹配的子节点，保留该节点
            if text in label or filtered_children:
                new_node = dict(node)
                new_node["children"] = filtered_children
                return new_node

            return None

        # 过滤所有根节点
        filtered_roots: List[Dict[str, Any]] = []
        for root in nodes:
            filtered = filter_node(root)
            if filtered is not None:
                filtered_roots.append(filtered)

        return filtered_roots

    @staticmethod
    def find_node_by_id(
        nodes: List[Dict[str, Any]],
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        在树中查找指定 ID 的节点

        Args:
            nodes: 树节点列表
            node_id: 要查找的节点 ID

        Returns:
            找到的节点，如果未找到则返回 None
        """
        if not nodes:
            return None

        for node in nodes:
            if str(node.get("id")) == str(node_id):
                return node

            # 递归搜索子节点
            children = node.get("children") or []
            if children:
                found = TreeFilterHelper.find_node_by_id(children, node_id)
                if found:
                    return found

        return None

    @staticmethod
    def get_node_path(
        nodes: List[Dict[str, Any]],
        node_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取从根节点到指定节点的路径

        Args:
            nodes: 树节点列表
            node_id: 目标节点 ID

        Returns:
            节点路径列表（从根到目标）
        """
        if not nodes:
            return []

        def find_path(current_nodes: List[Dict[str, Any]], target_id: str, path: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
            """递归查找路径"""
            for node in current_nodes:
                current_path = path + [node]

                if str(node.get("id")) == str(target_id):
                    return current_path

                children = node.get("children") or []
                if children:
                    result = find_path(children, target_id, current_path)
                    if result:
                        return result

            return None

        return find_path(nodes, node_id, []) or []


# ==================== 便捷函数 ====================

def filter_tree_nodes(nodes: List[Dict[str, Any]], search_text: str) -> List[Dict[str, Any]]:
    """
    过滤树节点（便捷函数）

    Args:
        nodes: 树节点列表
        search_text: 搜索文本

    Returns:
        过滤后的节点列表
    """
    return TreeFilterHelper.filter_nodes_by_text(nodes, search_text)


def find_tree_node(nodes: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
    """
    查找树节点（便捷函数）

    Args:
        nodes: 树节点列表
        node_id: 节点 ID

    Returns:
        找到的节点
    """
    return TreeFilterHelper.find_node_by_id(nodes, node_id)


def get_node_path(nodes: List[Dict[str, Any]], node_id: str) -> List[Dict[str, Any]]:
    """
    获取节点路径（便捷函数）

    Args:
        nodes: 树节点列表
        node_id: 节点 ID

    Returns:
        节点路径列表
    """
    return TreeFilterHelper.get_node_path(nodes, node_id)
