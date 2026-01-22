# BDC-AI 文档中心

## 📚 文档导航

本目录包含项目的各类文档,包括总结报告、测试报告、API 示例等。所有文档已完成中文命名和去重优化。

---

## 📖 文档分类

### 🎯 项目总览

#### [项目总结.md](./项目总结.md)
**最新更新**: 2026-01-20
**文档版本**: 2.0.0

**内容概要**:
- 项目概览与 MVP 完成度
- 已完成功能详细列表
- 技术亮点与成就
- 数据统计与开发进度
- 下一步计划

**适合人群**: 新成员、项目干系人、技术评审

---

### 🗄️ 数据库迁移

#### [PostgreSQL迁移总结.md](./PostgreSQL迁移总结.md)
**更新日期**: 2025-01-19

**内容概要**:
- 迁移原因与问题分析
- SQLite UUID 兼容性问题详解
- 数据迁移统计与验证结果
- 技术优势对比
- 迁移脚本与备份说明

**适合人群**: 运维人员、DBA、开发人员

---

### 🧪 测试报告

#### [GLM_Worker测试报告.md](./GLM_Worker测试报告.md)
**测试日期**: 2025-01-19

**内容概要**:
- GLM-4V API 功能测试
- 图片识别与分析结果
- 性能指标统计
- 系统架构验证
- 完整数据流测试

**适合人群**: 测试人员、开发人员

---

### 🔒 安全与清理

#### [项目清理与安全加固总结.md](./项目清理与安全加固总结.md)
**清理日期**: 2025-01-19

**内容概要**:
- 临时文件清理清单
- API-KEY 安全处理
- .gitignore 配置更新
- 项目结构优化
- 安全加固措施

**适合人群**: 运维人员、安全审计

---

### 📡 API 文档

#### [API使用示例.md](./API使用示例.md)
**文档完善度**: 80%

**内容概要**:
- Assets API 端点说明
- 完整请求示例（5 种模态）
- 字段说明与数据类型
- curl 测试命令
- 响应格式示例

**适合人群**: 前端开发、API 集成人员

---

## 📂 GUIDEBOOK/ 目录

包含项目的核心指南文档:

### 核心文档
- **[PLAN.md](../GUIDEBOOK/PLAN.md)** - 项目详细规划（阶段 1/2/3）
- **[TECHNICAL_GUIDES.md](../GUIDEBOOK/TECHNICAL_GUIDES.md)** - 技术解析文档
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code 开发指南
- **[README.md](../README.md)** - 项目主文档

### 设计文档
- **[工程结构API设计.md](../GUIDEBOOK/工程结构API设计.md)** - Building/Zone/System/Device API 设计
- **[OPEN_SOURCE_RECOMMENDATIONS.md](../GUIDEBOOK/OPEN_SOURCE_RECOMMENDATIONS.md)** - 开源技术栈推荐
- **[MOBILE_RECOMMENDATIONS.md](../GUIDEBOOK/MOBILE_RECOMMENDATIONS.md)** - 移动端技术推荐

---

## 🗂️ 文档优化记录

### 已完成的优化

#### 1. 去重合并 ✅
- 合并 `FINAL_SUMMARY.md` + `PROJECT_PROGRESS_SUMMARY.md` → `项目总结.md`
- 合并 `SQLITE_UUID_ISSUES.md` + `POSTGRESQL_MIGRATION_SUMMARY.md` → `PostgreSQL迁移总结.md`

#### 2. 中文命名 ✅
- `API_EXAMPLES.md` → `API使用示例.md`
- `GLM_WORKER_TEST_REPORT.md` → `GLM_Worker测试报告.md`
- `CLEANUP_SUMMARY.md` → `项目清理与安全加固总结.md`
- `ENGINEERING_STRUCTURE_API_DESIGN.md` → `工程结构API设计.md`（移至 GUIDEBOOK/）

#### 3. 归类整理 ✅
- 将设计文档移至 `GUIDEBOOK/` 目录
- 将总结、测试、安全文档保留在 `docs/` 目录

#### 4. 删除冗余 ✅
删除以下重复文档:
- `FINAL_SUMMARY.md`
- `PROJECT_PROGRESS_SUMMARY.md`
- `SQLITE_UUID_ISSUES.md`
- `POSTGRESQL_MIGRATION_SUMMARY.md`

---

## 📋 文档使用建议

### 新成员入职
1. 先读 `../README.md` 了解项目
2. 再读 `项目总结.md` 了解当前状态
3. 参阅 `../GUIDEBOOK/TECHNICAL_GUIDES.md` 学习技术栈

### 开发人员
1. API 集成 → `API使用示例.md`
2. 数据库操作 → `PostgreSQL迁移总结.md`
3. 工程结构 → `../GUIDEBOOK/工程结构API设计.md`

### 测试人员
1. 功能测试 → `GLM_Worker测试报告.md`
2. 验证清单 → 各文档中的"验证检查清单"章节

### 运维人员
1. 部署参考 → `../README.md`
2. 安全加固 → `项目清理与安全加固总结.md`
3. 数据库管理 → `PostgreSQL迁移总结.md`

---

## 🔍 文档维护规范

### 命名规范
- **中文优先**: 所有文档使用中文命名
- **描述清晰**: 文件名应清楚表达文档内容
- **避免缩写**: 使用完整词汇,便于搜索

### 版本管理
- **日期标识**: 每个文档应在开头标注更新日期
- **版本号**: 重要文档应有版本号
- **变更记录**: 重大修改应记录变更内容

### 归类原则
- **GUIDEBOOK/**: 核心规划、技术指南、设计文档
- **docs/**: 总结报告、测试报告、临时文档
- **项目根目录**: README、CLAUDE.md 等入口文档

---

## 📞 反馈与建议

如发现文档问题或有改进建议,请:
1. 提交 Issue 到项目仓库
2. 直接修改文档并提交 PR
3. 联系项目维护者

---

**文档中心维护**: BDC-AI 开发团队
**最后更新**: 2026-01-20
