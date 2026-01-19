# PostgreSQL 迁移总结

## 迁移日期
2025-01-19

## 迁移原因
SQLite 不支持 SQLAlchemy 的 `UUID(as_uuid=True)` 类型，导致 10 处代码出现 UUID 查询问题。评估后决定迁移到 PostgreSQL 作为长期解决方案。

## 迁移结果
**✅ 完全成功！**

### 数据库信息
- **PostgreSQL 版本**: 18.1
- **数据库**: bdc_ai
- **用户**: admin
- **连接**: postgresql://admin:password@localhost:5432/bdc_ai

### 数据迁移统计
| 表名 | SQLite | PostgreSQL | 状态 |
|------|--------|------------|------|
| projects | 50 | 50 | ✅ |
| buildings | 0 | 0 | ✅ |
| zones | 0 | 0 | ✅ |
| systems | 0 | 0 | ✅ |
| devices | 0 | 0 | ✅ |
| file_blobs | 51 | 51 | ✅ |
| assets | 51 | 51 | ✅ |
| structured_payloads | 9 | 9 | ✅ |
| **总计** | **161** | **161** | **✅** |

## 关键问题修复

### 问题 1: Project 模型字段不匹配
**错误**：迁移脚本试图插入 `created_at` 字段，但该字段不存在
**解决**：修正字段映射，添加 `type`, `start_date`, `end_date`

### 问题 2: UUID 外键约束违反
**错误**：Assets 插入失败，因为 projects 表未正确插入
**解决**：修复 Project 迁移逻辑，添加详细日志和错误处理

## 验证测试结果

### 1. PostgreSQL UUID 查询 ✅
- 通过 Asset ID 查询：正常
- 通过 Project ID 关联查询：正常
- 通过 File ID 关联查询：正常

### 2. 后端 API 测试 ✅
- Health Check: 200 OK
- Projects List: 返回 50 个项目
- Project Detail: UUID 查询正常
- Assets List: 返回 51 个资产
- Asset Filter by Project: 正常工作

### 3. GLM Worker 图片读取 ✅
- 后端 API 正常返回 file_path
- 本地文件存在且可读
- 图片处理（PIL）正常
- Base64 编码成功
- 文件路径解析正确

## 配置变更

### .env 文件
```bash
# 修改前:
BDC_DATABASE_URL=sqlite:///./data/bdc_ai.db

# 修改后:
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai
```

### 代码变更
**无需修改任何代码**！SQLAlchemy 的 UUID(as_uuid=True) 在 PostgreSQL 下原生支持。

## 后续步骤

### 1. 启动后端服务
```bash
cd services/backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload
```

### 2. 访问 API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 启动 GLM Worker
```bash
cd services/worker
# 确保设置了 GLM_API_KEY 环境变量
python scene_issue_glm_worker.py
```

### 4. 测试场景问题分析流程
```bash
python services/worker/test_scene_issue_pipeline.py
```

## 技术优势

### PostgreSQL vs SQLite
1. **UUID 原生支持**: 无需类型转换
2. **外键约束**: 严格的数据完整性
3. **并发性能**: 更好的多用户支持
4. **扩展性**: 支持 pgvector, TimescaleDB 等扩展
5. **生产就绪**: 适合企业级部署

### 解决的问题
- ✅ 10 处 UUID 查询问题全部解决
- ✅ 外键关联查询完全正常
- ✅ 数据完整性得到保证
- ✅ 为未来扩展（向量检索、时序数据）做好准备

## 迁移脚本
所有迁移脚本保存在项目根目录：
- `migrate_sqlite_to_postgres.py` - 数据迁移脚本
- `check_foreign_keys.py` - 外键完整性检查
- `setup_postgres.bat` - PostgreSQL 数据库初始化脚本
- `test_postgres_image_access.py` - 迁移后验证测试
- `test_glm_worker_image_access.py` - GLM Worker 功能验证

## 数据备份
原始 SQLite 数据库保留在：
```
data/bdc_ai.db
```

建议保留作为备份，直到 PostgreSQL 验证通过并稳定运行一段时间。

## 性能对比
- **数据量**: 161 条记录
- **SQLite 数据库大小**: ~124 KB
- **迁移耗时**: < 1 秒
- **查询性能**: PostgreSQL 查询速度与 SQLite 相当（对于小数据集）

## 结论
PostgreSQL 迁移完全成功，所有功能验证通过。系统现已具备生产环境运行的基础，可支持未来扩展需求。
