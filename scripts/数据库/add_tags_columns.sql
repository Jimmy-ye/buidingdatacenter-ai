-- 添加 tags 列到工程结构表
-- 用于支持工程结构树的标签功能

ALTER TABLE buildings      ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE zones          ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE building_systems ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE devices        ADD COLUMN IF NOT EXISTS tags jsonb;

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_devices_tags ON devices USING GIN(tags);
