from typing import List

from bigtree import Node
from sqlalchemy.orm import Session, joinedload

from shared.db.models_project import Building, Zone, BuildingSystem, Device


class EngineeringTreeService:
    """工程结构树服务 - 基于 Building/Zone/System/Device 构建项目工程树。"""

    @staticmethod
    def build_project_tree(project_id, db: Session) -> Node:
        """构建项目的工程结构树，并返回 bigtree 的根节点。"""
        buildings: List[Building] = (
            db.query(Building)
            .options(
                joinedload(Building.zones),
                joinedload(Building.systems).joinedload(BuildingSystem.devices).joinedload(Device.zone),
            )
            .filter(Building.project_id == project_id)
            .all()
        )

        # 根节点
        root = Node("项目根")
        root.id = "project-root"
        root.type = "project_root"

        # Building -> System -> Device 以及 Building 下的 Zones
        for building in buildings:
            b_node = Node(building.name, parent=root)
            b_node.id = str(building.id)
            b_node.type = "building"
            b_node.usage_type = building.usage_type

            # Systems 及其 Devices
            for system in building.systems:
                s_node = Node(system.name or system.type, parent=b_node)
                s_node.id = str(system.id)
                s_node.type = "system"
                s_node.system_type = system.type

                for device in system.devices:
                    d_node = Node(device.model or (device.device_type or "device"), parent=s_node)
                    d_node.id = str(device.id)
                    d_node.type = "device"
                    d_node.device_type = device.device_type
                    if device.zone is not None:
                        d_node.zone = {
                            "id": str(device.zone.id),
                            "name": device.zone.name,
                        }

            # Zones 列表（不含设备）
            for zone in building.zones:
                z_node = Node(zone.name, parent=b_node)
                z_node.id = str(zone.id)
                z_node.type = "zone"
                z_node.zone_type = zone.type
                z_node.device_count = len(zone.devices)

        return root

    @staticmethod
    def tree_to_dict(node: Node) -> dict:
        """将 bigtree Node 转换为可序列化的字典。"""
        if node.is_leaf:
            return {k: v for k, v in vars(node).items() if not k.startswith("_")}

        return {
            "id": getattr(node, "id", None),
            "name": node.node_name,
            "type": getattr(node, "type", None),
            "children": [EngineeringTreeService.tree_to_dict(child) for child in node.children],
        }
