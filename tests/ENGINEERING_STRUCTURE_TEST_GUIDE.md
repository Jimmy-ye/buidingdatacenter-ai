# 工程师结构树与扁平设备视图测试说明

本文档总结当前工程结构相关实现情况，并说明如何使用集成测试脚本验证：

- Building / Zone / System / Device 工程结构 API
- JSON `tags` 字段
- Project 级扁平设备查询
- 工程结构树（structure_tree）

---

## 1. 已实现功能小结

### 1.1 数据模型（`shared/db/models_project.py`）

在原有模型基础上为四个实体增加了 `tags` JSON 字段：

- `Building`
  - `tags: JSON | None`
- `Zone`
  - `tags: JSON | None`
- `BuildingSystem`
  - `tags: JSON | None`
- `Device`
  - `tags: JSON | None`

> 注意：这是 ORM 定义的更新，PostgreSQL 表本身需要执行 `ALTER TABLE` 或删除重建。

### 1.2 工程结构 API（`services/backend/app/api/v1/engineering.py`）

主要端点：

- Building
  - `GET  /api/v1/projects/{project_id}/buildings`
  - `POST /api/v1/projects/{project_id}/buildings`
  - `GET  /api/v1/buildings/{building_id}` / `PATCH` / `DELETE`
- Zone（与 System 同级，位置视图）
  - `GET  /api/v1/buildings/{building_id}/zones`
  - `POST /api/v1/buildings/{building_id}/zones`
  - `GET  /api/v1/zones/{zone_id}` / `PATCH` / `DELETE`
  - `GET  /api/v1/zones/{zone_id}/devices`（只读视图）
- System（Device 主归属）
  - `GET  /api/v1/buildings/{building_id}/systems`
  - `POST /api/v1/buildings/{building_id}/systems`
  - `GET  /api/v1/systems/{system_id}` / `PATCH` / `DELETE`
  - `GET  /api/v1/systems/{system_id}/devices`
  - `POST /api/v1/systems/{system_id}/devices`（创建设备的唯一入口）
- Device
  - `GET  /api/v1/devices/{device_id}` / `PATCH` / `DELETE`

### 1.3 扁平设备查询（Flat View）

- `GET /api/v1/projects/{project_id}/devices/flat`

支持的过滤参数：

- `system_id: uuid | None`
- `zone_id: uuid | None`
- `device_type: str | None`
- `min_rated_power: float | None`
- `tags: str | None`（逗号分隔，AND 语义，通过 `Device.tags.contains([...])` 实现）
- `search: str | None`（在 `model` / `serial_no` 上模糊搜索）

返回模型：`DeviceFlatRead`，包含：

- 设备基本信息：`id, system_id, zone_id, device_type, model, rated_power, serial_no, tags`
- `primary_system { id, name, type }` 作为主归属信息
- `location { id, name }` 作为位置信息
- `engineer_path`：`Building / System / Device` 字符串

### 1.4 工程结构树（Structure Tree）

Service 文件：`services/backend/app/services/tree_service.py`

端点：

- `GET /api/v1/projects/{project_id}/structure_tree`

返回结构示例：

```jsonc
{
  "project_id": "...",
  "tree": {
    "id": "project-root",
    "name": "项目根",
    "type": "project_root",
    "children": [
      {
        "id": "building-...",
        "name": "A座办公楼",
        "type": "building",
        "children": [
          {
            "id": "system-...",
            "name": "HVAC系统",
            "type": "system",
            "children": [
              {
                "id": "device-...",
                "name": "风机盘管FCU-03",
                "type": "device",
                "device_type": "fcu",
                "zone": { "id": "zone-...", "name": "5F办公区" }
              }
            ]
          }
        ],
        "zones": [
          {
            "id": "zone-...",
            "name": "5F办公区",
            "type": "zone",
            "device_count": 1
          }
        ]
      }
    ]
  }
}
```

实现基于 `bigtree`：

- `build_project_tree(project_id, db)`: 查询 Building/Zone/System/Device 并构建 bigtree Node
- `tree_to_dict(node)`: 将 Node 递归转换为字典

---

## 2. 集成测试脚本说明

测试脚本路径：

- `tests/integration/test_engineering_structure.py`

脚本逻辑步骤：

1. **创建 Project**
   - `POST /api/v1/projects/`
   - 打印状态码与响应内容，获取 `project_id`
2. **创建 Building / Zone / System / Device**
   - `POST /api/v1/projects/{project_id}/buildings`
     - 建筑名称：`A座办公楼`
     - `tags`: `["总部园区"]`
   - `POST /api/v1/buildings/{building_id}/zones`
     - 区域名称：`5F办公区`
     - `tags`: `["5F"]`
   - `POST /api/v1/buildings/{building_id}/systems`
     - 系统类型：`HVAC`
     - 名称：`HVAC系统`
     - `tags`: `["空调"]`
   - `POST /api/v1/systems/{system_id}/devices`
     - `zone_id`：上一步 Zone 的 ID
     - `device_type`: `fcu`
     - `model`: `风机盘管FCU-03`
     - `tags`: `["高能耗", "待观察"]`
3. **测试扁平设备查询**
   - `GET /api/v1/projects/{project_id}/devices/flat`
   - Query 示例：
     - `device_type=fcu`
     - `min_rated_power=1.0`
     - `tags=高能耗`
   - 打印状态码与 JSON 内容（包含 `primary_system` / `location` / `engineer_path`）
4. **测试工程结构树**
   - `GET /api/v1/projects/{project_id}/structure_tree`
   - 打印状态码与响应文本的前 800 个字符，用于快速查看树结构是否符合预期。

运行脚本入口：

```python
if __name__ == "__main__":
    main()
```

---

## 3. 手动测试步骤

### 3.1 安装后端依赖

在项目根目录运行：

```bash
pip install -r services/backend/requirements.txt
```

确保包含：

- `fastapi`
- `sqlalchemy`
- `psycopg2-binary`
- `PaddleOCR`
- `bigtree==0.16.4`

### 3.2 更新数据库 Schema（添加 tags 列，**必须执行**）

> ⚠ **重要：如果没有为四个表添加 `tags` 列，所有 Building/Zone/System/Device 的创建/更新操作都会报 `500 Internal Server Error`。**
>
> 原因：ORM 模型已经包含 `tags` 字段，而 PostgreSQL 表缺少对应列；`Base.metadata.create_all()` 不会自动修改已存在的表结构。

请确认你连接的是实际运行后端时使用的 PostgreSQL 数据库（即 `BDC_DATABASE_URL` 指向的数据库），然后执行以下 SQL：

```sql
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE zones     ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE systems   ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE devices   ADD COLUMN IF NOT EXISTS tags jsonb;
```

> 注意：`systems` 是 ORM 中 `BuildingSystem.__tablename__ = "systems"` 对应的真实表名，**不是** `building_systems`。

执行完成后，可以用类似方式检查列是否存在（可选）：

```sql
-- 以 buildings 为例，查看 tags 列
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'buildings' AND column_name = 'tags';
```

开发环境中如果允许清空数据，也可以采用“重建库”的方式：

1. 删除原来的 `bdc_ai` 数据库
2. 重新创建空数据库
3. 启动后端，由 `Base.metadata.create_all` 自动建表（会包含 `tags` 列）

### 3.3 启动后端服务

在项目根目录执行：

```bash
python -m uvicorn services.backend.app.main:app --reload
```

确认浏览器访问：`http://127.0.0.1:8000/docs` 可以看到 `engineering` 相关 API。

### 3.4 运行工程结构集成测试

在项目根目录执行：

```bash
python tests/integration/test_engineering_structure.py
```

预期输出包括：

- Project / Building / Zone / System / Device 创建的状态码与响应内容
- `/api/v1/projects/{project_id}/devices/flat` 的 JSON 列表（包含主系统、位置、工程路径）
- `/api/v1/projects/{project_id}/structure_tree` 的 JSON 片段（树结构）

如需通过 pytest 统一运行集成测试：

```bash
pytest tests/integration/test_engineering_structure.py -v
```

---

## 4. 后续扩展建议

在当前实现基础上，可以进一步增加：

- 设备与资产（Asset）的反向索引 API：
  - `/devices/{device_id}/assets`
  - `/systems/{system_id}/assets`
  - `/zones/{zone_id}/assets`
  - `/buildings/{building_id}/assets`
- 资产统计摘要接口：`/devices/{device_id}/assets/summary`
- 更多标签查询能力（如 `tags_any` 的 OR 语义）

本测试文档可作为后续工程结构相关变更和回归测试的基准。
