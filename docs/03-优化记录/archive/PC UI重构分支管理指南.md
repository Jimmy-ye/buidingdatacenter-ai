# PC UI 重构分支管理指南

## 📊 当前分支结构

```
master (主分支)
├── feature/pc-ui (功能开发分支)
│   ├── PC UI 基础功能
│   ├── 表格行点击事件
│   ├── 工程师备注功能
│   └── 文档整理
│
└── refactor/pc-ui-modularization (重构分支) ← 当前分支
    └── 代码重构工作
        ├── 阶段 1: API 客户端封装 ✅
        ├── 阶段 2: 状态管理 (待开始)
        ├── 阶段 3: UI 组件拆分 (待开始)
        └── 阶段 4: 主应用简化 (待开始)
```

---

## 🎯 分支职责

### master 分支
- **用途**：生产环境代码
- **状态**：稳定版本
- **合并策略**：只接受经过测试的合并

### feature/pc-ui 分支
- **用途**：PC UI 功能开发
- **内容**：
  - ✅ NiceGUI 界面基础功能
  - ✅ 工程结构树展示
  - ✅ 资产列表与详情
  - ✅ 图片预览
  - ✅ OCR/LLM 集成
  - ✅ 文档整理（中文化）

### refactor/pc-ui-modularization 分支（当前）
- **用途**：代码重构与优化
- **内容**：
  - ✅ API 客户端封装
  - ⏳ 状态管理重构
  - ⏳ UI 组件拆分
  - ⏳ 代码模块化

---

## 🔄 工作流程

### 开发新功能

```bash
# 1. 切换到功能分支
git checkout feature/pc-ui

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交功能
git add .
git commit -m "feat: XXX 功能"

# 4. 推送到远程
git push origin feature/pc-ui
```

### 重构代码

```bash
# 1. 切换到重构分支
git checkout refactor/pc-ui-modularization

# 2. 进行重构
# ... 重构代码 ...

# 3. 提交重构
git add .
git commit -m "refactor(stage X): XXX 重构"

# 4. 推送到远程
git push origin refactor/pc-ui-modularization
```

### 合并到 master

#### 方案 A：先合并功能，再合并重构

```bash
# 步骤 1: 合并功能分支到 master
git checkout master
git pull origin master
git merge feature/pc-ui
# 解决冲突（如果有）
git push origin master

# 步骤 2: 合并重构分支到 master
git checkout master
git pull origin master
git merge refactor/pc-ui-modularization
# 解决冲突（如果有）
git push origin master
```

#### 方案 B：先合并重构到功能，再一起合并到 master

```bash
# 步骤 1: 将重构合并到功能分支
git checkout feature/pc-ui
git pull origin feature/pc-ui
git merge refactor/pc-ui-modularization
# 解决冲突（如果有）
git push origin feature/pc-ui

# 步骤 2: 将功能分支合并到 master
git checkout master
git pull origin master
git merge feature/pc-ui
git push origin master
```

---

## 📋 当前提交历史

### feature/pc-ui 分支

```
67a47ab refactor(stage 1): 创建 API 客户端封装，开始渐进式重构 ← 重构提交
fa6d949 docs: 文档文件名中文化与版本信息修正
dced77d docs: 整合GUIDEBOOK目录到docs，统一文档管理
0ba9e21 feat: 实现工程师备注功能与Prompt优化，整理文档目录
04c097e chore: 清理测试脚本并简化调试输出，创建 UI 优化方案文档
316b215 fix: 实现 PC 端表格行点击事件联动详情面板
2b9fa75 feat: 实现 PC 端 NiceGUI 界面与工程结构管理
```

### refactor/pc-ui-modularization 分支（当前）

```
67a47ab refactor(stage 1): 创建 API 客户端封装，开始渐进式重构
```

**说明**：重构分支从 feature/pc-ui 的最新提交创建，包含所有历史提交。

---

## ⚠️ 重要注意事项

### 1. 分支隔离

**原则**：功能开发和重构工作分开进行

- ✅ **功能分支**（feature/pc-ui）
  - 新功能开发
  - Bug 修复
  - 文档更新

- ✅ **重构分支**（refactor/pc-ui-modularization）
  - 代码重构
  - 架构优化
  - 性能优化

### 2. 何时合并功能分支到 master

**条件**：
- ✅ 功能完整且经过测试
- ✅ 文档已更新
- ✅ 无重大 bug

**操作**：
```bash
git checkout master
git merge feature/pc-ui
git push origin master
```

### 3. 何时合并重构分支到 master

**条件**：
- ✅ 所有重构阶段完成
- ✅ 功能测试通过
- ✅ 性能测试通过
- ✅ 代码审查通过

**操作**：
```bash
git checkout master
git merge refactor/pc-ui-modularization
git push origin master
```

### 4. 如何保持分支同步

**定期同步**：
```bash
# 将 master 的更新合并到功能分支
git checkout feature/pc-ui
git merge master

# 将 master 的更新合并到重构分支
git checkout refactor/pc-ui-modularization
git merge master
```

---

## 🚀 快速参考

### 常用命令

```bash
# 查看所有分支
git branch -v

# 切换分支
git checkout <branch-name>

# 创建并切换到新分支
git checkout -b <new-branch>

# 合并分支
git merge <source-branch>

# 查看分支差异
git log master..feature/pc-ui --oneline

# 查看提交图
git log --graph --oneline --all

# 删除已合并的分支
git branch -d <branch-name>
```

### 当前分支状态

```bash
# 当前所在分支
refactor/pc-ui-modularization

# 基于分支
feature/pc-ui

# 包含提交
- 67a47ab refactor(stage 1): 创建 API 客户端封装
- fa6d949 docs: 文档文件名中文化与版本信息修正
- dced77d docs: 整合GUIDEBOOK目录到docs，统一文档管理
- ... (更多历史提交)
```

---

## 📝 重构进度追踪

### 阶段 1: API 客户端封装 ✅

**状态**: 完成
**提交**: `67a47ab`
**日期**: 2025-01-22

**完成内容**:
- ✅ 创建 `BackendClient` 类
- ✅ 实现所有 API 方法
- ✅ 向后兼容层
- ✅ 单元测试
- ✅ 迁移示例文档

**文件**:
- `desktop/nicegui_app/api/client.py`
- `tests/test_api_client.py`
- `desktop/nicegui_app/api/migration_examples.py`

### 阶段 2: 状态管理 ⏳

**状态**: 待开始
**预计时间**: 1-2 天

**计划内容**:
- [ ] 创建 `AppState` 类
- [ ] 实现项目状态管理
- [ ] 实现树状态管理
- [ ] 实现资产状态管理
- [ ] 创建兼容层
- [ ] 逐步迁移旧代码

### 阶段 3: UI 组件拆分 ⏳

**状态**: 待开始
**预计时间**: 3-5 天

**计划内容**:
- [ ] 提取对话框组件
  - [ ] ProjectDialog
  - [ ] UploadDialog
  - [ ] PreviewDialog
- [ ] 提取面板组件
  - [ ] ProjectPanel
  - [ ] TreePanel
  - [ ] AssetList
  - [ ] AssetDetail

### 阶段 4: 主应用简化 ⏳

**状态**: 待开始
**预计时间**: 1 天

**计划内容**:
- [ ] 简化 `main_page()` 函数
- [ ] 整合所有组件
- [ ] 清理旧代码
- [ ] 性能测试

---

## 🔧 故障排查

### 问题 1: 合并冲突

**症状**：
```bash
git merge feature/pc-ui
# CONFLICT (content): Merge conflict in pc_app.py
```

**解决**：
```bash
# 1. 查看冲突文件
git status

# 2. 手动解决冲突
# 编辑冲突文件，选择需要的代码

# 3. 标记为已解决
git add <resolved-file>

# 4. 完成合并
git commit

# 5. 推送
git push
```

### 问题 2: 错误的分支

**症状**：在错误的分支上进行了提交

**解决**：
```bash
# 方案 A: 撤销提交（未推送）
git reset --soft HEAD~1
git checkout <correct-branch>
git commit -m "xxx"

# 方案 B: Cherry-pick（已推送）
git checkout <correct-branch>
git cherry-pick <wrong-branch-commit-hash>
git checkout <wrong-branch>
git reset --hard HEAD~1
```

### 问题 3: 需要回滚

**症状**：重构引入了 bug

**解决**：
```bash
# 回滚到上一个稳定版本
git reset --hard HEAD~1

# 或者创建 revert 提交
git revert <commit-hash>
```

---

## 📞 获取帮助

### 查看分支历史
```bash
git log --graph --oneline --all --decorate
```

### 查看特定分支的提交
```bash
git log feature/pc-ui --oneline
```

### 比较两个分支
```bash
git diff master..feature/pc-ui
```

### 查看远程分支
```bash
git branch -r
```

---

**文档创建时间**: 2025-01-22
**当前分支**: refactor/pc-ui-modularization
**维护者**: BDC-AI 开发团队
