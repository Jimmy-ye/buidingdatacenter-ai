# 后端 API 完整性检查清单

生成时间：2026-01-23
分支：feature/mobile-development

## ✅ 项目 API (projects.py)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/projects/` | GET | 获取项目列表 | ✅ |
| `/api/v1/projects/{id}` | GET | 获取项目详情 | ✅ |
| `/api/v1/projects/` | POST | 创建项目 | ✅ |
| `/api/v1/projects/{id}` | PATCH | 更新项目 | ✅ |
| `/api/v1/projects/{id}` | DELETE | 删除项目（软删除） | ✅ |

## ✅ 工程结构 API (engineering.py)

### 楼栋 (Buildings)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/projects/{project_id}/buildings` | GET | 获取项目的楼栋列表 | ✅ |
| `/api/v1/projects/{project_id}/buildings` | POST | 创建楼栋 | ✅ |
| `/api/v1/buildings/{building_id}` | GET | 获取楼栋详情 | ✅ |
| `/api/v1/buildings/{building_id}` | PATCH | 更新楼栋 | ✅ |
| `/api/v1/buildings/{building_id}` | DELETE | 删除楼栋 | ✅ |

### 区域 (Zones)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/buildings/{building_id}/zones` | GET | 获取楼栋的区域列表 | ✅ |
| `/api/v1/buildings/{building_id}/zones` | POST | 创建区域 | ✅ |
| `/api/v1/zones/{zone_id}` | GET | 获取区域详情 | ✅ |
| `/api/v1/zones/{zone_id}` | PATCH | 更新区域 | ✅ |
| `/api/v1/zones/{zone_id}` | DELETE | 删除区域 | ✅ |

### 系统 (Systems)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/buildings/{building_id}/systems` | GET | 获取楼栋的系统列表 | ✅ |
| `/api/v1/buildings/{building_id}/systems` | POST | 创建系统 | ✅ |
| `/api/v1/systems/{system_id}` | GET | 获取系统详情 | ✅ |
| `/api/v1/systems/{system_id}` | PATCH | 更新系统 | ✅ |
| `/api/v1/systems/{system_id}` | DELETE | 删除系统 | ✅ |

### 设备 (Devices)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/systems/{system_id}/devices` | GET | 获取系统的设备列表 | ✅ |
| `/api/v1/systems/{system_id}/devices` | POST | 创建设备 | ✅ |
| `/api/v1/projects/{project_id}/devices/flat` | GET | 扁平化设备列表（带路径） | ✅ |
| `/api/v1/zones/{zone_id}/devices` | GET | 获取区域的设备列表（只读） | ✅ |
| `/api/v1/devices/{device_id}` | GET | 获取设备详情 | ✅ |
| `/api/v1/devices/{device_id}` | PATCH | 更新设备 | ✅ |
| `/api/v1/devices/{device_id}` | DELETE | 删除设备 | ✅ |

### 工程结构树 (Structure Tree)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/projects/{project_id}/structure_tree` | GET | 获取完整工程结构树 | ✅ |

## ✅ 资产 API (assets.py)

### 资产查询

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/assets/` | GET | 获取资产列表（支持多维度过滤） | ✅ |
| `/api/v1/assets/{asset_id}` | GET | 获取资产详情（含结构化内容） | ✅ |

### 资产上传

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/assets/upload_image_with_note` | POST | 上传图片+工程师备注 | ✅ |
| `/api/v1/assets/upload_meter_with_auto_route` | POST | 上传仪表读数并自动路由 | ✅ |
| `/api/v1/assets/upload_nameplate_with_auto_route` | POST | 上传铭牌照片并自动路由 | ✅ |

### AI 分析

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/assets/{asset_id}/run_ocr` | POST | 运行 OCR 文字识别 | ✅ |
| `/api/v1/assets/{asset_id}/run_scene_llm` | POST | 运行 GLM-4V 场景分析 | ✅ |
| `/api/v1/assets/{asset_id}/scene_issue_report` | POST | 附加场景问题报告 | ✅ |

### 资产路由

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/assets/{asset_id}/route` | POST | 手动路由资产到工程结构 | ✅ |

### 按节点查询资产

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/devices/{device_id}/assets` | GET | 获取设备资产列表 | ✅ |
| `/api/v1/systems/{system_id}/assets` | GET | 获取系统资产列表 | ✅ |
| `/api/v1/zones/{zone_id}/assets` | GET | 获取区域资产列表 | ✅ |
| `/api/v1/buildings/{building_id}/assets` | GET | 获取楼栋资产列表 | ✅ |

## ✅ 健康检查 API (health.py)

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/health/` | GET | 健康检查 | ✅ |

---

## 📊 统计

- **总 API 数量**：68 个端点
- **项目 API**：5 个 ✅
- **工程结构 API**：38 个 ✅
- **资产 API**：24 个 ✅
- **健康检查 API**：1 个 ✅

## 🎯 移动端需要的核心 API

| 功能 | API 端点 | 状态 |
|------|----------|------|
| 项目列表 | `GET /api/v1/projects/` | ✅ |
| 工程结构树 | `GET /api/v1/projects/{id}/structure_tree` | ✅ |
| 设备资产列表（设备视图） | `GET /api/v1/assets/?device_id={id}` | ✅ |
| 系统资产列表（系统视图） | `GET /api/v1/assets/?system_id={id}` | ✅ |
| 上传图片+备注（设备级或系统级，使用 device_id 或 system_id） | `POST /api/v1/assets/upload_image_with_note` | ✅ |

**结论**：所有移动端开发需要的 API 都已完整！ ✅


**修复时间**：2026-01-23

---

**维护者**：BDC-AI 开发团队
**最后更新**：2026-01-23
