# 调试工具说明

**最后更新**: 2026-01-26

本目录包含用于调试和测试的辅助脚本。这些工具主要用于开发过程中的快速状态检查和问题排查。

---

## 📋 脚本分类

### 资产状态检查脚本

| 脚本名 | 用途 | 使用场景 |
|--------|------|---------|
| `check_assets_status.py` | 查询项目下所有资产的状态 | 调试资产处理流程 |
| `check_db_payloads.py` | 检查资产的structured_payloads | 调试数据存储问题 |
| `check_new_asset.py` | 查看单个资产的详细信息 | 验证资产创建结果 |
| `update_asset_status.py` | 手动更新资产状态 | 调试状态转换问题 |

### Worker 调试脚本

| 脚本名 | 用途 | 使用场景 |
|--------|------|---------|
| `check_worker_status.py` | 检查Worker进程和待处理资产 | 调试Worker运行状态 |
| `manual_update_status.py` | 手动更新资产状态为pending_scene_llm | 触发Worker处理特定资产 |
| `rerun_project_images.py` | 批量重新处理项目中的所有图片 | 重新运行图片处理流程 |

### 功能测试脚本

| 脚本名 | 用途 | 使用场景 |
|--------|------|---------|
| `test_engineer_note.py` | 测试工程师备注对LLM的影响 | 验证备注功能 |
| `test_single_meter.py` | 测试单个仪表资产的处理流程 | 调试仪表读数识别 |
| `upload_meter_with_auto_route.py` | 上传仪表图片并自动路由 | 测试自动路由功能 |

---

## 🚀 使用示例

### 查看项目资产状态

```bash
# 从项目根目录运行
cd D:\BDC-AI

# 使用默认项目ID
venv\Scripts\python.exe scripts\调试工具\check_assets_status.py

# 或修改脚本中的PROJECT_ID后运行
```

### 手动触发Worker处理

```bash
# 1. 编辑脚本，修改manual_update_status.py中的ASSET_ID
# 2. 运行脚本更新状态
venv\Scripts\python.exe scripts\调试工具\manual_update_status.py

# 3. Worker会自动处理该资产
```

### 测试工程师备注功能

```bash
# 运行完整的工程师备注测试（5个用例）
venv\Scripts\python.exe scripts\调试工具\test_engineer_note.py
```

---

## ⚠️ 注意事项

1. **脚本位置**: 这些脚本现在位于 `scripts/调试工具/` 目录下
2. **配置依赖**: 大多数脚本依赖 `.env` 文件中的配置（如数据库URL、API密钥等）
3. **调试用途**: 这些脚本主要用于开发和调试，不应在生产环境使用
4. **手动编辑**: 使用前通常需要编辑脚本中的ID、路径等配置

---

## 🔧 维护说明

- 不再使用的临时调试脚本应及时删除
- 成熟的功能测试脚本可以迁移到 `scripts/测试/` 目录
- 添加新脚本时，请更新本README文件

---

## 📚 相关文档

- **../测试/README.md** - 正式测试脚本
- **../服务管理/README.md** - 服务启动和管理
- **../Windows/README.md** - Windows系统脚本

---

**调试工具集中管理！** 🔧
