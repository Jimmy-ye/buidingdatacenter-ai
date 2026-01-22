-- 添加软删除字段到 projects 表
-- 执行方式: psql -U admin -d bdc_ai -f migrations/add_soft_delete_fields.sql

-- 添加 is_deleted 字段
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 添加 deleted_at 字段
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- 添加 deleted_by 字段
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(100);

-- 添加 deletion_reason 字段
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS deletion_reason VARCHAR(500);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_is_deleted
ON projects(is_deleted);
