# Asset ↔ 工程结构 关联查询测试说明

本文档介绍如何使用集成测试脚本验证 Asset 与工程结构（Building/Zone/System/Device）的关联查询，包括：

- Project 级联删除与 Asset 关系
- `/api/v1/assets` 的多维过滤
- 工程节点 → 资产的反向查询

> **重要变更（2025-01）**：Project 已实现软删除/硬删除策略，硬删除时会级联删除所有关联的 Asset 记录。

---

## 1. Project 删除与 Asset 级联删除

### 1.1 软删除不影响 Asset

当使用软删除（默认）方式删除 Project 时：

- Project 的 `is_deleted` 字段设置为 `True`
- **Asset 记录不受影响**，仍然保留在数据库中
- 可以通过 Asset 的 `project_id` 字段关联到已软删除的 Project

### 1.2 硬删除级联删除 Asset

当使用硬删除方式（`hard_delete=true`）删除 Project 时：

- **先删除 assets 表中所有 `project_id` 匹配的记录**
- 再删除 Project 记录本身
- 此操作**不可逆**

### 1.3 示例

```python
# 软删除 - Asset 不受影响
DELETE /api/v1/projects/{project_id}?reason=测试软删除

# 硬删除 - 所有相关 Asset 会被删除
DELETE /api/v1/projects/{project_id}?hard_delete=true&reason=测试硬删除
```

---

## 2. 测试脚本概览

脚本路径：

- `tests/integration/test_asset_engineering_link.py`

脚本主要步骤：

1. 创建一个测试 Project。
2. 创建 Building / Zone / System / Device 四个工程实体。
3. 通过 `upload_image_with_note` 上传一张绑定到上述工程节点的图片 Asset。
4. 使用 `/api/v1/assets` 做多维过滤查询。
5. 使用以下反向查询接口按工程节点列出资产：
   - `GET /api/v1/devices/{device_id}/assets`
   - `GET /api/v1/zones/{zone_id}/assets`
   - `GET /api/v1/buildings/{building_id}/assets`
   - `GET /api/v1/systems/{system_id}/assets`

脚本采用 `requests` 直接调用本地运行中的 FastAPI 后端，打印每一步的状态码和 JSON 响应，便于人工检查。

---

## 3. 运行前置条件

### 3.1 环境与依赖

- 已安装 backend 依赖：

```bash
pip install -r services/backend/requirements.txt
```

- 本地 PostgreSQL 数据库已按 `ENGINEERING_STRUCTURE_TEST_GUIDE.md` 中说明完成：
  - 为 `projects` 表添加软删除字段和 `tags jsonb` 列
  - 为 `buildings/zones/systems/devices` 添加 `tags jsonb` 列
  - ORM 模型中的 `tags` 字段类型为 `JSONB`

### 3.2 启动后端服务

在项目根目录运行：

```bash
python -m uvicorn services.backend.app.main:app --reload
```

确认浏览器访问 `http://127.0.0.1:8000/docs` 正常，且能看到：

- `projects` 相关 API
- `engineering` 相关 API（Building/Zone/System/Device）
- `assets` 相关 API

---

## 4. 脚本执行流程

### 4.1 运行脚本

在项目根目录执行：

```bash
python tests/integration/test_asset_engineering_link.py
```

脚本输出分为 5 大部分：

#### 步骤 1：创建 Project

- 请求：`POST /api/v1/projects/`
- 预期：
  - 状态码：`201`
  - 返回 JSON 中包含 `id` 字段（`project_id`）

#### 步骤 2：创建 Building / Zone / System / Device

依次调用：

- `POST /api/v1/projects/{project_id}/buildings`
- `POST /api/v1/buildings/{building_id}/zones`
- `POST /api/v1/buildings/{building_id}/systems`
- `POST /api/v1/systems/{system_id}/devices`

预期：

- 每一步状态码均为 `201`
- 分别获得 `building_id`、`zone_id`、`system_id`、`device_id`

#### 步骤 3：上传绑定到工程结构的图片 Asset

- 请求：

  ```http
  POST /api/v1/assets/upload_image_with_note
  ```

  - Query 参数：
    - `project_id`
    - `source=test_script`
    - `content_role=scene_issue`
    - `building_id`
    - `zone_id`
    - `system_id`
    - `device_id`
  - Form 数据：
    - `note`: 简短说明，如 "5F风机盘管测试图片"
    - `title`: 如 "FCU-03 测试图"
  - Files：
    - `file`: 一张测试图片（二进制内容脚本中用假数据代替）

- 预期：
  - 状态码：`201`
  - 返回 JSON 中包含：
    - `id`（`asset_id`）
    - `project_id`、`building_id`、`zone_id`、`system_id`、`device_id`
    - `modality="image"`
    - `content_role="scene_issue"`
    - `engineer_path` 字段（如 "A座办公楼 / HVAC系统 / 风机盘管FCU-03"）

#### 步骤 4：`/api/v1/assets` 多维过滤

- 请求示例：

  ```http
  GET /api/v1/assets
      ?project_id={project_id}
      &building_id={building_id}
      &zone_id={zone_id}
      &system_id={system_id}
      &device_id={device_id}
      &modality=image
  ```

- 预期：
  - 状态码：`200`
  - 返回列表长度 ≥ 1，包含刚刚上传的 Asset
  - 每个 Asset 记录中带有对应的工程结构 ID 字段

#### 步骤 5：工程节点 → 资产反向查询

脚本依次调用：

1. `GET /api/v1/devices/{device_id}/assets`
2. `GET /api/v1/zones/{zone_id}/assets`
3. `GET /api/v1/buildings/{building_id}/assets`
4. `GET /api/v1/systems/{system_id}/assets`

预期：

- 每个请求状态码均为 `200`
- 返回 JSON 列表中包含刚刚上传的 Asset
- 返回模型为 `AssetDetailRead`，应包含：
  - `id`, `project_id`, `building_id`, `zone_id`, `system_id`, `device_id`
  - `modality`, `content_role`, `title`, `description`
  - `structured_payloads: []`（此时可能为空列表）

> 验收点：
> - 能通过脚本验证“按设备/区域/楼栋/系统”查看资产列表。
> - 返回结构中预留了 `structured_payloads` 字段，后续 OCR/LLM 写入后可直接在这些列表接口中看到。

---

## 5. 在 Swagger 中手动验证

除了运行脚本，你还可以在 Swagger UI 中手动验证：

1. 打开 `http://127.0.0.1:8000/docs`。
2. 按以下顺序操作：
   1. 调用 `POST /api/v1/projects/` 创建项目。
   2. 调用 `POST /api/v1/projects/{project_id}/buildings` 创建 Building。
   3. 调用 `POST /api/v1/buildings/{building_id}/zones` 创建 Zone。
   4. 调用 `POST /api/v1/buildings/{building_id}/systems` 创建 System。
   5. 调用 `POST /api/v1/systems/{system_id}/devices` 创建 Device。
   6. 调用 `POST /api/v1/assets/upload_image_with_note` 上传图片。

3. 然后验证：

- 在 `GET /api/v1/assets` 中填写：
  - `project_id` + 需要的工程结构 ID（如 `device_id`），查看过滤结果。
- 在 `GET /api/v1/devices/{device_id}/assets` 中填入 `device_id`：
  - 查看该设备下的全部资产（图片/表格等）。
- 同理验证：
  - `GET /api/v1/zones/{zone_id}/assets`
  - `GET /api/v1/buildings/{building_id}/assets`
  - `GET /api/v1/systems/{system_id}/assets`

如果一切正常，你应该能在 Swagger 中：

- 通过“设备视角”看到某设备的所有图片资产。
- 通过“楼层/区域视角”看到某区域的所有资产。
- 确认返回结构中已经包含 `structured_payloads` 字段，用于后续 OCR/LLM 结果挂载。

---

## 6. Project 级联删除测试

### 6.1 测试目标

验证 Project 硬删除时，Asset 记录是否被正确级联删除。

### 6.2 测试步骤

#### 步骤 1：创建 Project 和 Asset

```bash
# 创建项目
POST /api/v1/projects/
{
  "name": "级联删除测试项目",
  "tags": {"test": "cascade"}
}

# 保存返回的 project_id

# 创建工程结构
POST /api/v1/projects/{project_id}/buildings
POST /api/v1/buildings/{building_id}/systems
POST /api/v1/systems/{system_id}/devices

# 上传 Asset
POST /api/v1/assets/upload_image_with_note?project_id={project_id}&device_id={device_id}
```

#### 步骤 2：查询 Asset

```bash
GET /api/v1/assets?project_id={project_id}
# 应返回至少 1 条记录
```

#### 步骤 3：硬删除 Project

```bash
DELETE /api/v1/projects/{project_id}?hard_delete=true&reason=测试级联删除
```

#### 步骤 4：验证 Asset 已被删除

```bash
GET /api/v1/assets?project_id={project_id}
# 应返回空列表 []

# 在数据库中验证
SELECT * FROM assets WHERE project_id = '{project_id}';
# 应返回 0 rows
```

### 6.3 预期结果

- Project 记录被删除
- 所有相关 Asset 记录被删除
- 所有相关 Building/Zone/System/Device 记录被删除（通过外键 CASCADE）

---

## 7. 后续扩展方向

在当前基础上，可以进一步扩展：

- 在反向查询接口中增加 `modality` / `content_role` / `tags` 等过滤参数
- 为 `Asset` 的 `tags` 字段也切换到 JSONB 并支持标签过滤（类似设备 tags）
- 增加 `/devices/{device_id}/assets/summary` 之类的统计接口，汇总资产数量、类型分布、最新 OCR/LLM 状态等
- 为 Asset 也实现软删除功能（类似 Project 的 `is_deleted` 字段）
- 增加按 `is_deleted` 状态过滤 Asset 的功能

本测试脚本与说明可作为 Asset ↔ 工程结构 关联功能的回归测试基础。
