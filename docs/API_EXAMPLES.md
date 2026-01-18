# Assets API 使用示例

本文档提供 Assets API 的使用示例和请求体格式。

## API 端点

### 创建 Asset
```http
POST /api/v1/assets/
Content-Type: application/json
```

### 查询 Assets
```http
GET /api/v1/assets/?project_id=<project_id>
```

### 上传文件并创建 Asset（多模态采集）
```http
POST /api/v1/assets/upload
Content-Type: multipart/form-data
```

示例（curl）：
```bash
curl -X POST "http://localhost:8000/api/v1/assets/upload" \
  -F "project_id=<PROJECT_UUID>" \
  -F "modality=image" \
  -F "source=mobile_app" \
  -F "title=现场照片1" \
  -F "description=5F西侧外墙渗漏" \
  -F "file=@C:/path/to/photo.jpg"
```

### 使用 PaddleOCR 解析图片（第一层流水线）
```http
POST /api/v1/assets/{asset_id}/parse_image
```

说明：

- 仅适用于 `modality = image` 的 Asset；
- 内部调用 PaddleOCR，从本地文件路径读取图片，生成 `image_annotation` 类型的 `AssetStructuredPayload`；
- 根据 OCR 置信度更新 `Asset.status`：
  - `parsed_ocr_ok`：平均置信度高于阈值；
  - `parsed_ocr_low_conf`：平均置信度较低，后续可触发 Claude Vision 或人工标注。

---

## 完整请求示例

### 示例 1：创建图片类 Asset（现场照片）

```json
{
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "building_id": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "zone_id": "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "system_id": "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "device_id": "e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "image",
  "source": "mobile_app",
  "title": "5F 西侧办公室 - 空调风机盘管照片",
  "description": "设备编号 FCU-03，外观正常，滤网需更换",
  "capture_time": "2025-01-17T14:30:00Z",
  "location_meta": {
    "floor": "5F",
    "zone": "西侧办公区",
    "room": "501",
    "gps": "116.407526,39.904030",
    "device_id": "FCU-03"
  },
  "tags": ["空调", "风机盘管", "现场检查", "滤网"],
  "quality_score": 0.95,
  "status": "raw",
  "file": {
    "storage_type": "minio",
    "bucket": "bdc-assets",
    "path": "2025/01/17/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11.jpg",
    "file_name": "FCU-03_20250117_143000.jpg",
    "content_type": "image/jpeg",
    "size": 2048576.0,
    "hash": "sha256:a1b2c3d4e5f6..."
  }
}
```

### 示例 2：创建表格类 Asset（能耗记录表）

```json
{
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "table",
  "source": "pc_upload",
  "title": "2024年全年能耗记录表",
  "description": "来自物业系统的月度用电数据",
  "capture_time": "2025-01-15T10:00:00Z",
  "tags": ["能耗", "电量", "历史数据"],
  "status": "parsed",
  "file": {
    "storage_type": "minio",
    "bucket": "bdc-assets",
    "path": "2025/01/15/energy_data_2024.xlsx",
    "file_name": "energy_data_2024.xlsx",
    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "size": 45056.0,
    "hash": "md5:abc123..."
  }
}
```

### 示例 3：创建文本类 Asset（现场笔记）

```json
{
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "building_id": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "text",
  "source": "manual",
  "title": "5楼空调系统巡检记录",
  "description": "2025年1月例行巡检发现的问题记录",
  "capture_time": "2025-01-17T16:00:00Z",
  "location_meta": {
    "floor": "5F",
    "area": "设备间"
  },
  "tags": ["巡检", "空调", "维修建议"],
  "status": "validated",
  "file": {
    "storage_type": "minio",
    "bucket": "bdc-assets",
    "path": "2025/01/17/inspection_note_5f.txt",
    "file_name": "inspection_note_5f.txt",
    "content_type": "text/plain",
    "size": 1024.0
  }
}
```

### 示例 4：创建音频类 Asset（语音备忘）

```json
{
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "audio",
  "source": "mobile_app",
  "title": "现场语音备注 - 外墙保温检查",
  "description": "在现场检查外墙保温层时录制的语音备注",
  "capture_time": "2025-01-16T09:30:00Z",
  "location_meta": {
    "floor": "1F",
    "position": "北侧外墙",
    "gps": "116.407526,39.904030"
  },
  "tags": ["语音", "外墙", "保温", "缺陷"],
  "quality_score": 0.85,
  "status": "raw",
  "file": {
    "storage_type": "minio",
    "bucket": "bdc-assets",
    "path": "2025/01/16/voice_memo_wall.wav",
    "file_name": "voice_memo_wall.wav",
    "content_type": "audio/wav",
    "size": 1048576.0
  }
}
```

### 示例 5：创建文档类 Asset（PDF 报告）

```json
{
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "document",
  "source": "api",
  "title": "2024年度建筑能耗审计报告",
  "description": "第三方出具的年度能耗审计报告",
  "capture_time": "2025-01-10T08:00:00Z",
  "tags": ["报告", "审计", "年度总结"],
  "status": "validated",
  "file": {
    "storage_type": "minio",
    "bucket": "bdc-assets",
    "path": "2025/01/10/audit_report_2024.pdf",
    "file_name": "audit_report_2024.pdf",
    "content_type": "application/pdf",
    "size": 5242880.0,
    "hash": "sha256:xyz789..."
  }
}
```

---

## 最小化请求（仅必填字段）

```json
{
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "image",
  "source": "api",
  "file": {
    "storage_type": "minio",
    "bucket": "bdc-assets",
    "path": "test/image.jpg",
    "file_name": "image.jpg"
  }
}
```

---

## 字段说明

### Asset 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string (UUID) | ✅ | 所属项目 ID |
| building_id | string (UUID) | ❌ | 关联建筑 ID |
| zone_id | string (UUID) | ❌ | 关联区域 ID |
| system_id | string (UUID) | ❌ | 关联系统 ID |
| device_id | string (UUID) | ❌ | 关联设备 ID |
| modality | string | ✅ | 模态类型：image/table/text/audio/document |
| source | string | ✅ | 数据来源：mobile_app/pc_upload/api/external_system |
| title | string | ❌ | 资产标题 |
| description | string | ❌ | 详细描述 |
| capture_time | datetime | ❌ | 采集时间（ISO 8601 格式） |
| location_meta | object | ❌ | 位置元数据（JSON） |
| tags | array[string] | ❌ | 标签列表 |
| quality_score | float | ❌ | 质量评分（0-1） |
| status | string | ❌ | 状态：raw/parsed/validated |

### File 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storage_type | string | ✅ | 存储类型（默认：minio） |
| bucket | string | ✅ | 存储桶名称 |
| path | string | ✅ | 文件路径 |
| file_name | string | ✅ | 文件名 |
| content_type | string | ❌ | MIME 类型 |
| size | float | ❌ | 文件大小（字节） |
| hash | string | ❌ | 文件哈希值 |

---

## 模态类型说明

| modality | 说明 | 典型 content_type |
|----------|------|-------------------|
| image | 图片 | image/jpeg, image/png |
| table | 表格 | application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet |
| text | 文本 | text/plain, text/markdown |
| audio | 音频 | audio/wav, audio/mpeg |
| document | 文档 | application/pdf, application/msword |

---

## 响应示例

### 成功响应 (201 Created)

```json
{
  "id": "f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "building_id": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "zone_id": "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "system_id": "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "device_id": "e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "modality": "image",
  "source": "mobile_app",
  "title": "5F 西侧办公室 - 空调风机盘管照片",
  "description": "设备编号 FCU-03，外观正常，滤网需更换",
  "capture_time": "2025-01-17T14:30:00Z",
  "location_meta": {
    "floor": "5F",
    "zone": "西侧办公区",
    "room": "501",
    "gps": "116.407526,39.904030",
    "device_id": "FCU-03"
  },
  "tags": ["空调", "风机盘管", "现场检查", "滤网"],
  "quality_score": 0.95,
  "status": "raw",
  "file_id": "file-uuid-here"
}
```

---

## 使用 curl 测试

```bash
# 创建 Asset
curl -X POST "http://localhost:8000/api/v1/assets/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "modality": "image",
    "source": "mobile_app",
    "title": "测试图片",
    "file": {
      "storage_type": "minio",
      "bucket": "test-bucket",
      "path": "test/image.jpg",
      "file_name": "image.jpg",
      "content_type": "image/jpeg"
    }
  }'

# 查询 Assets
curl "http://localhost:8000/api/v1/assets/?project_id=your-project-id"
```
