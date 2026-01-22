# 测试脚本说明

本目录包含用于调试和测试的辅助脚本。

## 脚本列表

### 资产状态检查脚本

| 脚本名 | 用途 | 使用场景 |
|--------|------|---------|
| `check_assets_status.py` | 查询项目下所有资产的状态 | 调试资产处理流程 |
| `check_db_payloads.py` | 检查资产的structured_payloads | 调试数据存储问题 |
| `check_new_asset.py` | 查看单个资产的详细信息 | 验证资产创建结果 |
| `update_asset_status.py` | 手动更新资产状态 | 调试状态转换问题 |

### Worker调试脚本

| 脚本名 | 用途 | 使用场景 |
|--------|------|---------|
| `check_worker_status.py` | 检查Worker进程和待处理资产 | 调试Worker运行状态 |
| `manual_update_status.py` | 手动更新资产状态为pending_scene_llm | 触发Worker处理特定资产 |
| `rerun_project_images.py` | 批量重新处理项目中的所有图片 | 重新运行图片处理流程 |

### 测试和上传脚本

| 脚本名 | 用途 | 使用场景 |
|--------|------|---------|
| `test_engineer_note.py` | 测试工程师备注对LLM的影响 | 验证备注功能 |
| `test_single_meter.py` | 测试单个仪表资产的处理流程 | 调试仪表读数识别 |
| `upload_meter_with_auto_route.py` | 上传仪表图片并自动路由 | 测试自动路由功能 |

## 使用示例

### 查看项目资产状态

```bash
# 使用默认项目ID
python tests/scripts/check_assets_status.py

# 修改脚本中的PROJECT_ID后运行
```

### 手动触发Worker处理

```bash
# 1. 修改manual_update_status.py中的ASSET_ID
# 2. 运行脚本更新状态
python tests/scripts/manual_update_status.py

# 3. Worker会自动处理该资产
```

### 测试工程师备注功能

```bash
# 运行完整的工程师备注测试（5个用例）
python tests/scripts/test_engineer_note.py
```

## 注意事项

1. **脚本位置**：这些脚本在项目根目录时可以运行，移到`tests/scripts/`后可能需要调整导入路径
2. **配置依赖**：大多数脚本依赖`.env`文件中的配置（如数据库URL、API密钥等）
3. **调试用途**：这些脚本主要用于开发和调试，不应在生产环境使用
4. **手动编辑**：使用前通常需要编辑脚本中的ID、路径等配置

## 清理和维护

- 不再使用的临时测试脚本应删除
- 通用性强的脚本可以整合到`tests/`目录的测试套件中
- 添加新脚本时，更新本README文件

---

**最后更新**：2026-01-21
