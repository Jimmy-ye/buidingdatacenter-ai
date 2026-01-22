"""
后端 API 客户端封装
提供统一的后端调用接口，便于测试和维护

版本: v1.0
创建时间: 2025-01-22
"""

import httpx
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BackendClient:
    """
    后端 API 客户端

    提供统一的 API 调用接口，包含：
    - 统一的错误处理
    - 统一的日志记录
    - 类型提示
    - 超时控制
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000/api/v1",
        timeout: float = 30.0
    ):
        """
        初始化客户端

        Args:
            base_url: 后端 API 基础 URL
            timeout: 请求超时时间（秒）
        """
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
        """
        GET 请求

        Args:
            path: API 路径
            params: 查询参数

        Returns:
            响应数据
        """
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        POST 请求

        Args:
            path: API 路径
            data: 请求体数据
            **kwargs: 其他参数（如 files）

        Returns:
            响应数据
        """
        return await self._request("POST", path, json=data, **kwargs)

    async def patch(self, path: str, data: Optional[Dict] = None) -> Any:
        """
        PATCH 请求

        Args:
            path: API 路径
            data: 请求体数据

        Returns:
            响应数据
        """
        return await self._request("PATCH", path, json=data)

    async def delete(self, path: str) -> Any:
        """
        DELETE 请求

        Args:
            path: API 路径

        Returns:
            响应数据
        """
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
                - name: 项目名称
                - client: 客户名称（可选）
                - location: 位置（可选）
                - type: 类型（可选）
                - status: 状态（可选）
                - tags: 标签（可选）

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
            reason: 删除原因（可选）
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
                - name: 名称
                - tags: 标签

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
            node_type: 节点类型 (building/zone/system/device)
            node_id: 节点 ID
            reason: 删除原因（可选）
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
            **filters: 过滤条件
                - modality: 资产类型
                - content_role: 内容角色
                - status: 状态

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
            title: 资产标题（可选）
            content_role: 内容角色
            description: 描述（可选）

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

        url = f"{self.base_url}/assets/upload_image_with_note"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                url,
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
