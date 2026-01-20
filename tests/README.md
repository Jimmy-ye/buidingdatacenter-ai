# tests 测试数据目录

本目录用于存放测试数据和样本文件。

## 📁 目录结构

```
tests/
├── changsha-现场/        # 长沙万象城现场图片测试数据
├── changsha-表具/        # 长沙万象城表具图片测试数据
└── README.md            # 本文件
```

## 📊 测试数据说明

### changsha-现场（4张）
现场照片，用于测试 LLM 场景理解功能。

- `IMG_20250706_180220.jpg` - 风机盘管
- `IMG_20250708_105710.jpg` - 冷却塔
- `IMG_20250708_110459.jpg` - 冷却塔
- `IMG_20250710_115616.jpg` - 玻璃幕墙

**项目 ID**: `be0ceec0-27b3-4139-8636-05dd4412c769`

**用途**：测试 GLM-4V 视觉模型的现场问题识别能力

### changsha-表具（8张）
表计设备照片，用于测试 OCR 文字识别功能。

- `IMG_20250710_144250.jpg` - 压力表
- `IMG_20250710_144341.jpg` - 压力表
- `IMG_20250710_144432.jpg` - 压力表
- `IMG_20250710_144534.jpg` - 压力表
- `IMG_20250710_144657.jpg` - 压力表
- `IMG_20250710_144704.jpg` - 压力表
- `IMG_20250710_144826.jpg` - 压力表
- `IMG_20250710_144855.jpg` - 压力表

**项目 ID**: `be0ceec0-27b3-4139-8636-05dd4412c769`

**用途**：测试 PaddleOCR 中文识别能力

## 🔍 相关文档

测试指南和报告已移至 `docs/` 目录：

- **测试指南**：
  - `docs/ASSET_ENGINEERING_TEST_GUIDE.md` - Asset 与工程结构关联测试
  - `docs/ENGINEERING_STRUCTURE_TEST_GUIDE.md` - 工程结构测试指南

- **项目报告**：
  - `docs/changsha_complete_report.md` - 长沙万象城项目完整报告
  - `docs/长沙万象城总览.md` - 长沙万象城项目总览
  - `docs/prompt_improvement_report.md` - 提示词优化效果报告

## 📝 使用说明

### 上传测试数据

如果要添加新的测试数据：

1. 创建对应的子文件夹（如 `tests/项目名-类型/`）
2. 将测试图片放入该文件夹
3. 使用脚本上传数据（参考 `docs/changsha_complete_report.md`）
4. 记录项目 ID 和 Asset ID

### 查询测试数据

```bash
# 查询所有测试资产
GET http://localhost:8000/api/v1/assets?project_id=be0ceec0-27b3-4139-8636-05dd4412c769

# 查询现场图片
GET http://localhost:8000/api/v1/assets?project_id=be0ceec0-27b3-4139-8636-05dd4412c769&content_role=scene_issue

# 查询表具图片
GET http://localhost:8000/api/v1/assets?project_id=be0ceec0-27b3-4139-8636-05dd4412c769&content_role=meter
```

### 查看 Asset 详情

```bash
# 查看单张图片的详细分析结果
GET http://localhost:8000/api/v1/assets/{asset_id}
```

## 🗑️ 清理测试数据

如果要删除测试项目：

```bash
# 软删除（推荐）- 数据保留但标记为已删除
DELETE /api/v1/projects/be0ceec0-27b3-4139-8636-05dd4412c769?reason=测试完成清理

# 硬删除（危险）- 物理删除所有数据
DELETE /api/v1/projects/be0ceec0-27b3-4139-8636-05dd4412c769?hard_delete=true&reason=测试完成清理
```

⚠️ **警告**：硬删除会级联删除所有相关的 Asset 记录，此操作不可逆！

## 📅 更新日志

- **2025-01-20**: 整理 tests 目录，移动测试脚本和文档到相应位置
- **2025-01-20**: 添加长沙万象城项目测试数据（12张图片）
- **2025-01-20**: 完成提示词优化测试，所有图片用新提示词重新分析

## 📌 关于测试脚本

之前的集成测试脚本已删除，因为：
1. 它们主要用于功能开发阶段的验证
2. 功能已稳定，改用 Swagger UI 手动测试更灵活
3. 测试指南已整理到 `docs/` 目录

如果需要重新运行测试，可以参考 `docs/ENGINEERING_STRUCTURE_TEST_GUIDE.md` 和 `docs/ASSET_ENGINEERING_TEST_GUIDE.md`。
