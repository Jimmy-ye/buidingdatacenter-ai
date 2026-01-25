# 工程师结构树 API 设计（v2.0）

## 设计原则

本设计文档定义了工程结构相关的核心实体 API，遵循以下原则：

1. **主从关系明确**：Device 归属于 System（主），位于 Zone（从）
2. **避免数据冗余**：同一设备只在系统中出现一次
3. **多维查询支持**：提供扁平化查询，避免层层展开树
4. **实用导向**：符合工程师实际工作习惯
5. **架构兼容**：对现有项目结构调整最小

---

## 核心实体

- **Project**（项目）- 已有
- **Building**（建筑）
- **Zone**（区域/分区）- 与 System 同级
- **BuildingSystem**（系统）- 与 Zone 同级
- **Device**（设备）- 归属于 System，位于 Zone

### 关键设计决策

```
✓ 正确关系：
Building
├── System（功能分类）→ Device（主归属）
└── Zone（物理位置）→ Device（位置属性）

✗ 避免的情况：
Building
├── Zone → Device（重复）
└── System → Device（重复）
```

**核心原则**：> **Device 归属于 System，位于 Zone**（Ownership vs Location）

---

## 1. Building（建筑）

### 1.1 路由设计

```
列出 / 创建 Project 下所有 Building
GET  /api/v1/projects/{project_id}/buildings
POST /api/v1/projects/{project_id}/buildings

单个 Building 详情 / 修改 / 删除
GET    /api/v1/buildings/{building_id}
PATCH  /api/v1/buildings/{building_id}
DELETE /api/v1/buildings/{building_id}
```

### 1.2 字段设计（Schemas）

```python
class BuildingBase(BaseModel):
    name: str  # 建筑名称（必填）
    usage_type: str | None = None  # office/commercial/datacenter/mixed_use
    floor_area: float | None = None  # 建筑面积（m²）
    gfa_area: float | None = None  # GFA 面积（m²）
    year_built: int | None = None  # 建成年份
    tags: list[str] | None = None  # 标签（新增）

class BuildingCreate(BuildingBase):
    pass  # project_id 从路由获取

class BuildingRead(BuildingBase):
    id: uuid.UUID
    project_id: uuid.UUID
```

### 1.3 过滤方式

用于 `GET /api/v1/projects/{project_id}/buildings`：

- `usage_type: str | None` - 按建筑用途过滤
- `name_contains: str | None` - 按名称模糊搜索
- `tags: str | None` - 按标签筛选（逗号分隔，AND 逻辑）

### 1.4 默认系统模板（新建 Building 后）

为降低工程录入成本，推荐在创建 Building 后自动生成一批基础系统：

- 围护结构（`type="envelope"`）
- 制冷（`type="cooling"`）
- 制热（`type="heating"`）
- 空调末端（`type="terminal_hvac"`）
- 照明（`type="lighting"`）
- 电梯（`type="elevator"`）
- 动力（`type="power"`）
- 电力监控（`type="ems"`）
- 能管平台（`type="energy_platform"`）

业务约定：

- 当后端启用默认系统模板时，`POST /api/v1/projects/{project_id}/buildings` 成功返回后，应在对应 `building_id` 下自动插入上述若干 `BuildingSystem` 记录。
- 默认系统的 `name` 通常与中文名称一致，`type` 字段使用稳定的英文/代码，用于前后端逻辑判断与过滤。
- 后续可通过 `PATCH /api/v1/systems/{system_id}` 对名称、描述、标签进行细化调整，或通过 `POST /api/v1/buildings/{building_id}/systems` 增补自定义系统。

---

## 2. Zone（区域/分区）

**注意**：Zone 与 System 是**同级关系**，不是父子关系。

### 2.1 路由设计

```
列出 / 创建 Building 下的 Zones
GET  /api/v1/buildings/{building_id}/zones
POST /api/v1/buildings/{building_id}/zones

单个 Zone 详情 / 修改 / 删除
GET    /api/v1/zones/{zone_id}
PATCH  /api/v1/zones/{zone_id}
DELETE /api/v1/zones/{zone_id}

查询 Zone 下的设备（只读视图，不是归属关系）
GET /api/v1/zones/{zone_id}/devices
GET /api/v1/zones/{zone_id}/assets
```

### 2.2 字段设计

```python
class ZoneBase(BaseModel):
    name: str  # 区域名称
    type: str | None = None  # office/public/parking/datacenter_room
    geometry_ref: str | None = None  # BIM/CAD 引用 ID
    tags: list[str] | None = None  # 标签（新增）

class ZoneCreate(ZoneBase):
    pass  # building_id 从路由获取

class ZoneRead(ZoneBase):
    id: uuid.UUID
    building_id: uuid.UUID
    device_count: int | None = None  # 该区域的设备数量（统计字段）
```

### 2.3 关键业务规则

**Zone → Device 是位置视图，不是归属关系**：

```python
# ❌ 不允许通过 Zone 创建设备
# POST /api/v1/zones/{zone_id}/devices → 404 Not Found

# ✅ 允许通过 Zone 查询设备（只读）
GET /api/v1/zones/{zone_id}/devices
→ 返回位于该区域的设备（device.zone_id == zone_id）
→ 每个设备包含 primary_system 字段（主归属信息）
```

---

## 3. BuildingSystem（系统）

**注意**：System 是 Device 的**主归属**。

### 3.1 路由设计

```
列出 / 创建 Building 下的 Systems
GET  /api/v1/buildings/{building_id}/systems
POST /api/v1/buildings/{building_id}/systems

单个 System 详情 / 修改 / 删除
GET    /api/v1/systems/{system_id}
PATCH  /api/v1/systems/{system_id}
DELETE /api/v1/systems/{system_id}

管理 System 下的设备（主路径）
GET  /api/v1/systems/{system_id}/devices
POST /api/v1/systems/{system_id}/devices
```

### 3.2 字段设计

```python
class SystemBase(BaseModel):
    type: str  # 系统类型（必填）
    # HVAC/ChilledWater/HotWater/Boiler/CoolingTower/Lighting/Elevator
    name: str | None = None  # 系统名称
    description: str | None = None  # 补充说明
    tags: list[str] | None = None  # 标签（新增）

class SystemCreate(SystemBase):
    pass  # building_id 从路由获取

class SystemRead(SystemBase):
    id: uuid.UUID
    building_id: uuid.UUID
    device_count: int | None = None  # 该系统的设备数量（统计字段）
```

---

## 4. Device（设备）⭐ 核心

### 4.1 主从关系设计

```python
# 数据模型
class Device(Base):
    __tablename__ = "devices"

    # === 主关系：System（必填）===
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("building_systems.id"),
        nullable=False  # 设备必须属于某个系统
    )

    # === 从关系：Zone（可选）===
    zone_id = Column(
        UUID(as_uuid=True),
        ForeignKey("zones.id"),
        nullable=True  # 设备可以在某个区域，也可以不属于任何区域
    )

    device_type = Column(String(50))
    model = Column(String(200))
    rated_power = Column(Float)
    serial_no = Column(String(100))
    tags = Column(JSON, nullable=True)  # 新增：标签

    # Relationships
    system = relationship("BuildingSystem", back_populates="devices")
    zone = relationship("Zone", back_populates="devices")
    assets = relationship("Asset", back_populates="device")
```

**业务规则**：

1. `system_id` 必填（设备必须归属于某个系统）
2. `zone_id` 可选（设备可以位于某个区域，也可以不属于任何区域）
3. 如果提供 `zone_id`，则该 Zone 的 `building_id` 必须与 System 所在 Building 一致
4. **创建设备只能通过 System**，不能通过 Zone

### 4.2 路由设计

#### 主要路径（System → Device）

```
创建设备（只能通过 System）
POST /api/v1/systems/{system_id}/devices
Body:
{
    "zone_id": "...",  # 可选，指定设备位置
    "device_type": "fcu",
    "model": "风机盘管FCU-03",
    "rated_power": 1.5,
    "tags": ["高能耗", "2024年改造"]
}

查询某系统的设备
GET /api/v1/systems/{system_id}/devices
Query Params:
    - device_type: str | None
    - tags: str | None
    - zone_id: str | None  # 可选，进一步筛选位于某区域的设备
```

#### 辅助路径（Zone → Device，只读视图）

```
查询某区域的设备（只读）
GET /api/v1/zones/{zone_id}/devices
→ 返回位于该区域的设备
→ 每个设备包含 primary_system 字段（主归属信息）
→ 不允许通过此路径创建设备
```

#### 扁平化查询（避免层层展开树）⭐ 推荐

```
全局设备查询（不关心层级，只关心属性）
GET /api/v1/projects/{project_id}/devices/flat

Query Params:
    - system_id: str | None  # 限定某个系统
    - zone_id: str | None  # 限定某个区域
    - device_type: str | None  # 设备类型
    - min_rated_power: float | None  # 最小额定功率
    - tags: str | None  # 标签筛选（逗号分隔）
    - search: str | None  # 全文搜索（model/serial_no）

返回：
{
    "total": 15,
    "items": [
        {
            "id": "dev-xxx",
            "device_type": "chiller",
            "model": "800RT 离心机",
            "rated_power": 650.5,
            "primary_system": {  # ← 强调：这是主归属
                "id": "sys-xxx",
                "name": "冷冻水系统1#",
                "type": "ChilledWater"
            },
            "location": {  # ← 这是位置信息
                "id": "zone-xxx",
                "name": "地下二层机房"
            },
            "engineer_path": "A座办公楼 / 冷冻水系统1# / 800RT 离心机",
            "location_path": "A座办公楼 / 地下二层机房",
            "tags": ["高能耗", "重点监控"],
            "asset_count": 5  # 该设备的资产数量
        }
    ]
}
```

#### 单个设备操作

```
GET /api/v1/devices/{device_id}
PATCH /api/v1/devices/{device_id}
DELETE /api/v1/devices/{device_id}
```

### 4.3 字段设计

```python
class DeviceBase(BaseModel):
    zone_id: uuid.UUID | None = None  # 可选，设备位置
    device_type: str | None = None
    model: str | None = None
    rated_power: float | None = None  # kW
    serial_no: str | None = None
    tags: list[str] | None = None

class DeviceCreate(DeviceBase):
    pass  # system_id 从路由获取

class DeviceRead(DeviceBase):
    id: uuid.UUID
    system_id: uuid.UUID  # 主归属
    zone_id: uuid.UUID | None  # 位置
    engineer_path: str | None = None  # 工程路径（自动生成）
    asset_count: int | None = None  # 资产数量（统计）
```

### 4.4 标签系统（新增）⭐

**标签设计原则**：
- 灵活分类：支持按业务需求动态打标签
- 扁平化查询：通过标签快速筛选设备
- 个性化视图：支持创建虚拟分组

**标签查询接口**：

```python
GET /api/v1/projects/{project_id}/devices?tags=高能耗,待维修
→ AND 逻辑：同时包含"高能耗"和"待维修"

GET /api/v1/projects/{project_id}/devices?tags_any=高能耗,待维修
→ OR 逻辑：包含"高能耗"或"待维修"

GET /api/v1/projects/{project_id}/tags/suggestions
→ 返回该项目下使用过的所有标签及使用频次
{
    "device_tags": [
        {"tag": "高能耗", "count": 15},
        {"tag": "待维修", "count": 8},
        {"tag": "2024年改造", "count": 5}
    ]
}
```

---

## 5. 工程结构树视图

### 5.1 单树模型（推荐）⭐

**只返回 System 树，Zone 作为 Device 的属性**

```
GET /api/v1/projects/{project_id}/structure_tree

返回：
{
    "project_id": "...",
    "tree": {
        "id": "project-root",
        "name": "项目根",
        "type": "project_root",
        "children": [
            {
                "id": "building-xxx",
                "name": "A座办公楼",
                "type": "building",
                "usage_type": "office",
                "children": [
                    {
                        "id": "system-xxx",
                        "name": "HVAC系统",
                        "type": "system",
                        "system_type": "HVAC",
                        "children": [
                            {
                                "id": "dev-xxx",
                                "name": "风机盘管FCU-03",
                                "type": "device",
                                "device_type": "fcu",
                                "zone": {  # ← Zone 作为属性，不是独立的树
                                    "id": "zone-xxx",
                                    "name": "5F办公区"
                                },
                                "asset_count": 3
                            }
                        ]
                    }
                ],
                "zones": [  # ← Zone 列表（不含设备）
                    {
                        "id": "zone-xxx",
                        "name": "5F办公区",
                        "type": "zone",
                        "device_count": 15
                    }
                ]
            }
        ]
    }
}
```

**优势**：
- ✅ 避免了 Device 在两个树中出现
- ✅ 层级清晰：System 是 Device 的主归属
- ✅ Zone 信息保留在 Device 对象中
- ✅ 前端可以通过 Device.zone 快速筛选

### 5.2 双视图模型（可选）

如果前端强烈需要双视图：

```
视图 1：系统树（主）
GET /api/v1/projects/{project_id}/system_tree
→ Building → System → Device

视图 2：位置树（辅助，只读）
GET /api/v1/projects/{project_id}/location_tree
→ Building → Zone → [Device References]
→ 只返回设备引用，不包含完整设备信息
```

### 5.3 实现建议（使用 bigtree 辅助）⭐

**为什么使用 bigtree**：
- ✅ 提供强大的树操作 API（遍历、搜索、修改）
- ✅ 与 pandas/SQLAlchemy 无缝集成
- ✅ 活跃维护，零依赖（除可选的 pandas）
- ✅ 对现有架构无影响（仅应用层增强）

**安装**：
```bash
pip install bigtree
```

**服务层实现示例**：

```python
# services/backend/app/services/tree_service.py
from bigtree import dict_to_tree, Node
from sqlalchemy.orm import joinedload

class EngineeringTreeService:
    """工程结构树服务 - 使用 bigtree 辅助"""

    @staticmethod
    def build_project_tree(project_id: str, db: Session) -> Node:
        """
        构建项目的完整工程结构树

        返回 bigtree Node，提供便捷的树操作 API
        """
        # 1. 查询数据库（使用 eager loading 优化）
        buildings = db.query(Building)\
            .options(
                joinedload(Building.zones),
                joinedload(Building.systems)
                .joinedload(BuildingSystem.devices)
                .joinedload(Device.zone)  # ← 加载设备的 Zone 信息
            )\
            .filter_by(project_id=project_id)\
            .all()

        # 2. 转换为 bigtree 树结构
        tree_dict = EngineeringTreeService._build_tree_dict(buildings)
        root = dict_to_tree(tree_dict)

        return root

    @staticmethod
    def _build_tree_dict(buildings: list[Building]) -> dict:
        """将数据库查询结果转换为 bigtree 所需的字典格式"""
        return {
            "id": "project-root",
            "name": "项目根",
            "type": "project_root",
            "children": [
                {
                    "id": str(building.id),
                    "name": building.name,
                    "type": "building",
                    "usage_type": building.usage_type,
                    "children": [
                        # Systems
                        *[{
                            "id": str(system.id),
                            "name": system.name or system.type,
                            "type": "system",
                            "system_type": system.type,
                            "children": [
                                {
                                    "id": str(device.id),
                                    "name": device.model or f"{device.device_type}",
                                    "type": "device",
                                    "device_type": device.device_type,
                                    "zone": {
                                        "id": str(device.zone.id),
                                        "name": device.zone.name
                                    } if device.zone else None
                                }
                                for device in system.devices
                            ]
                        } for system in building.systems],
                        # Zones（不含设备）
                        *[{
                            "id": str(zone.id),
                            "name": zone.name,
                            "type": "zone",
                            "zone_type": zone.type,
                            "device_count": len(zone.devices)
                        } for zone in building.zones]
                    ]
                }
                for building in buildings
            ]
        }

    @staticmethod
    def tree_to_dict(node: Node) -> dict:
        """将 bigtree Node 转换为字典（用于 API 返回）"""
        if node.is_leaf:
            return {
                k: v for k, v in vars(node).items()
                if not k.startswith("_")
            }

        return {
            "id": getattr(node, "id", None),
            "name": node.node_name,
            "type": getattr(node, "type", None),
            "children": [
                EngineeringTreeService.tree_to_dict(child)
                for child in node.children
            ]
        }
```

**API 使用示例**：

```python
# services/backend/app/api/v1/projects.py
from app.services.tree_service import EngineeringTreeService

@router.get("/projects/{project_id}/structure_tree")
async def get_project_structure_tree(
    project_id: str,
    db: Session = Depends(get_db)
):
    """获取项目的完整工程结构树（使用 bigtree 优化）"""
    # 构建树
    root = EngineeringTreeService.build_project_tree(project_id, db)

    # 转换为字典返回
    return {
        "project_id": project_id,
        "tree": EngineeringTreeService.tree_to_dict(root)
    }
```

---

## 6. Asset 反向索引⭐ 重要

### 6.1 从工程节点查看关联的 Asset

```
# 设备的资产列表
GET /api/v1/devices/{device_id}/assets
→ 返回该设备的所有 Asset（图片、表格等）
→ 支持按 modality 筛选

# 系统的资产列表
GET /api/v1/systems/{system_id}/assets

# 区域的资产列表
GET /api/v1/zones/{zone_id}/assets

# 建筑的资产列表
GET /api/v1/buildings/{building_id}/assets
```

### 6.2 资产统计摘要（辅助决策）

```
GET /api/v1/devices/{device_id}/assets/summary

返回：
{
    "device_id": "dev-xxx",
    "total_assets": 15,
    "by_modality": {
        "image": 10,
        "table": 3,
        "text": 2
    },
    "latest_scene_issues": [
        {
            "asset_id": "...",
            "severity": "high",
            "issue": "冷机电机铭牌模糊"
        }
    ],
    "unprocessed_count": 2,  # 未处理的 Asset 数量
    "last_updated": "2025-01-19T10:30:00Z"
}
```

**价值**：
- ✅ 工程师点击设备时，立即看到"这个设备有什么资料"
- ✅ 可以快速定位"缺少资料"的设备（unprocessed_count = 0）
- ✅ 支持基于资料完整度的工作优先级

---

## 7. 与 Asset 的协同

### 7.0 工程实体与资产挂接关系总览

- **主挂接点：System**
  - 每个 Asset 理论上应能解析到一个所在的 System（功能归属）。
  - 新资产创建时，如果提供 `device_id`，后端通过 `_resolve_engineering_hierarchy` 自动反推该设备所属的 System，并写入 `asset.system_id`。
  - 如果直接提供 `system_id`（例如系统级上传），则以该字段作为主挂接点。

- **可选挂接点：Device**
  - `asset.device_id` 是可选的，用于指向具体设备（铭牌、现场问题、能耗表等贴在单台设备上的资料）。
  - 缺省情况下，系统级资料（系统原理图、配电一次图等）可以只挂在 `system_id` 上，不必绑定具体设备。

- **位置属性：Zone / Building**
  - `asset.building_id`、`asset.zone_id` 表示物理位置维度：在哪栋楼、哪一层/哪一区域。
  - 若只提供 `device_id`，后端会依据设备上的 `zone_id`、所属 System 的 `building_id` 自动补全这两个字段。

- **统一解析函数 `_resolve_engineering_hierarchy`**
  - 入参：`project_id, building_id, zone_id, system_id, device_id`（部分可空）。
  - 责任：
    - 校验所有 ID 是否存在且层级一致（Device → System → Building，Zone → Building）。
    - 在只提供部分 ID（如仅 device_id 或仅 system_id）时，自动推导缺失的层级。
    - 返回实体对象和 `engineer_path` 字符串，便于前端展示和追踪。

> 总结：**System 是资产的主挂接维度，Device/Zone 是可选的细化维度**。这样既支持系统级视图，又保留到单台设备和具体区域的下钻能力。

### 7.1 工程路径生成

上传 Asset 时，前端可以选择具体 Building/Zone/System/Device：

```python
POST /api/v1/assets/upload_image_with_note
{
    "project_id": "...",
    "device_id": "...",  # 选择设备
    # 系统会自动推导：
    # - system_id（从 device.system_id）
    # - building_id（从 system.building_id）
    # - zone_id（从 device.zone_id，如果有）
    "file": <binary>,
    "content_role": "scene_issue",
    "note": "5F西风机盘管异响"
}
```

**后端自动处理**：

```python
# services/backend/app/services/asset_service.py

def _resolve_engineering_hierarchy(
    project_id: str | None,
    building_id: str | None,
    zone_id: str | None,
    system_id: str | None,
    device_id: str | None,
    db: Session
) -> dict:
    """
    解析工程层级关系

    1. 如果提供了 device_id，自动推导 system_id, building_id, zone_id
    2. 如果提供了 system_id，自动推导 building_id
    3. 校验所有 ID 的存在性和层级一致性
    4. 生成人类可读的工程路径
    """
    # 从 device_id 推导
    if device_id:
        device = db.query(Device).filter_by(id=device_id).one_or_none()
        if not device:
            raise HTTPException(404, "Device not found")

        system_id = str(device.system_id)
        zone_id = str(device.zone_id) if device.zone_id else None
        building_id = str(device.system.building_id)

    # 从 system_id 推导
    elif system_id:
        system = db.query(BuildingSystem).filter_by(id=system_id).one_or_none()
        if not system:
            raise HTTPException(404, "System not found")
        building_id = str(system.building_id)

    # 校验层级一致性
    if zone_id and system_id:
        zone = db.query(Zone).filter_by(id=zone_id).one_or_none()
        system = db.query(BuildingSystem).filter_by(id=system_id).one_or_none()
        if zone and system and zone.building_id != system.building_id:
            raise HTTPException(
                400,
                "Zone and System must belong to the same Building"
            )

    # 生成工程路径
    engineer_path = _generate_engineer_path(
        building_id, zone_id, system_id, device_id, db
    )

    return {
        "project_id": project_id,
        "building_id": building_id,
        "zone_id": zone_id,
        "system_id": system_id,
        "device_id": device_id,
        "engineer_path": engineer_path
    }

def _generate_engineer_path(
    building_id: str | None,
    zone_id: str | None,
    system_id: str | None,
    device_id: str | None,
    db: Session
) -> str:
    """生成人类可读的工程路径"""
    parts = []

    if building_id:
        building = db.query(Building).filter_by(id=building_id).one()
        parts.append(building.name)

    if system_id:
        system = db.query(BuildingSystem).filter_by(id=system_id).one()
        parts.append(system.name or system.type)

    if device_id:
        device = db.query(Device).filter_by(id=device_id).one()
        parts.append(device.model or device.device_type)

    return " / ".join(parts)
```

### 7.2 Asset 返回结构

```python
class AssetRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID

    # 工程结构关联
    building_id: uuid.UUID | None
    zone_id: uuid.UUID | None
    system_id: uuid.UUID | None
    device_id: uuid.UUID | None

    # 工程路径（自动生成）
    engineer_path: str | None = None  # "A座办公楼 / HVAC系统 / 风机盘管FCU-03"
    location_path: str | None = None  # "A座办公楼 / 5F办公区"（如果有 zone）

    # Asset 基础信息
    modality: str
    title: str | None
    description: str | None
    # ...
```

---

## 8. 前端使用建议

### 8.1 主界面：System 树

```
左侧导航（树形结构）：
📁 A座办公楼
  📁 HVAC系统
    🔧 冷机CH-001
      📷 图片 (3)
      📊 表格 (1)
    🔧 冷机CH-002
  📁 照明系统
    💡 灯具L-001
```

### 8.2 辅助视图：Zone 筛选

```
顶部筛选器：
[按区域筛选: 全部 ▼]
  - 全部
  - 5F办公区 (15 设备)
  - 3F会议室 (8 设备)
  - 地下二层机房 (23 设备)

选择"5F办公区"后，System 树中只显示位于该区域的设备
```

### 8.3 设备详情页

```
设备：风机盘管FCU-03

━━━━━━━━━━━━━━━━━━━━━━━━
📍 物理位置：5F办公区 ← Zone（只读标签，可点击跳转）
⚙️ 所属系统：HVAC系统 ← System（主归属，可点击跳转）

📂 相关资料：
  📷 图片 (3) ← 点击查看
  📊 表格 (1) ← 点击查看
  📝 文本 (2)

🏷️ 标签：
  #高能耗 #待维修 #2024年改造
```

### 8.4 扁平化查询界面

```
全局设备查询
━━━━━━━━━━━━━━━━━━━━━━━━
搜索框：[🔍 搜索设备型号、序列号...]

筛选器：
[设备类型: 全部 ▼] [系统: 全部 ▼] [区域: 全部 ▼]
[最小功率: ____] [标签: 高能耗,待维修]

结果列表（扁平化，直接查看所有匹配设备）：
┌────────────────────────────────────┐
│ 800RT 离心机                        │
│ 📍 地下二层机房  ⚙️ 冷冻水系统1#    │
│ 🏷️ 高能耗 #重点监控                  │
│ 📷 5 图片  📊 2 表格                 │
└────────────────────────────────────┘
┌────────────────────────────────────┐
│ 风机盘管FCU-03                      │
│ 📍 5F办公区  ⚙️ HVAC系统            │
│ 🏷️ 待维修                           │
│ 📷 3 图片  📊 1 表格                 │
└────────────────────────────────────┘
```

---

## 9. 实施计划

### 第 1 天：数据模型调整

- [ ] 调整 Device 模型（增加 tags 字段）
- [ ] 调整 Zone/System 模型（增加 tags 字段）
- [ ] 增加 asset_count 统计字段
- [ ] 编写数据库迁移脚本

### 第 2 天：核心 API 实现

- [ ] 实现 Building/Zone/System CRUD
- [ ] 实现 Device CRUD（只能通过 System 创建）
- [ ] 实现 Zone → Device 查询（只读视图）
- [ ] 实现扁平化查询 `/projects/{id}/devices/flat`

### 第 3 天：高级功能

- [ ] 集成 bigtree
- [ ] 实现 `/projects/{id}/structure_tree`
- [ ] 实现 Asset 反向索引
- [ ] 实现工程路径自动生成

### 第 4 天：测试与优化

- [ ] 编写单元测试
- [ ] 性能测试（eager loading 优化）
- [ ] 更新 API 文档

---

## 10. 性能优化建议

### 10.1 数据库查询优化

```python
# 使用 joinedload 避免 N+1 查询
from sqlalchemy.orm import joinedload

buildings = db.query(Building)\
    .options(
        joinedload(Building.zones),
        joinedload(Building.systems)
        .joinedload(BuildingSystem.devices)
        .joinedload(Device.zone)
    )\
    .filter_by(project_id=project_id)\
    .all()
```

### 10.2 索引建议

```sql
-- Device 表索引
CREATE INDEX idx_device_system ON devices(system_id);
CREATE INDEX idx_device_zone ON devices(zone_id);
CREATE INDEX idx_device_type ON devices(device_type);
CREATE INDEX idx_device_tags ON devices USING GIN(tags);

-- Asset 表索引
CREATE INDEX idx_asset_device ON assets(device_id);
CREATE INDEX idx_asset_system ON assets(system_id);
CREATE INDEX idx_asset_zone ON assets(zone_id);
```

---

## 11. 总结

### 核心设计原则

1. **Device 归属 System，位于 Zone**（主从关系）
2. **创建只能通过 System**，查询可以通过 System 或 Zone
3. **提供扁平化查询**，避免层层展开树
4. **使用 bigtree 辅助**，对现有架构无影响
5. **支持标签系统**，灵活分类和筛选

### 技术栈

- **数据库层**：Adjacency List（外键）
- **应用层**：bigtree（树操作辅助）
- **API 设计**：RESTful + 扁平化查询
- **性能优化**：eager loading + 索引

### 对现有架构的影响

- ✅ **数据模型**：最小调整（增加 tags 字段）
- ✅ **API 设计**：保持 RESTful 风格
- ✅ **前端兼容**：可以逐步迁移
- ✅ **性能**：通过 bigtree 和 eager loading 优化

这套 API 设计为后续的**表格流水线、诊断问题清单、多模态检索**提供统一的工程结构基础。
