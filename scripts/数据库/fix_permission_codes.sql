-- 权限代码修复脚本（单数改复数）
-- 用于修复权限代码不一致问题
-- 问题：数据库使用 project:create，PC-UI 检查 projects:create
-- 解决：统一改为复数形式

-- ============================================
-- 1. 项目管理权限：project:* → projects:*
-- ============================================
UPDATE permissions
SET code = 'projects:create',
    resource = 'projects',
    description = '创建项目'
WHERE code = 'project:create';

UPDATE permissions
SET code = 'projects:read',
    resource = 'projects',
    description = '查看项目'
WHERE code = 'project:read';

UPDATE permissions
SET code = 'projects:update',
    resource = 'projects',
    description = '更新项目'
WHERE code = 'project:update';

UPDATE permissions
SET code = 'projects:delete',
    resource = 'projects',
    description = '删除项目'
WHERE code = 'project:delete';

-- ============================================
-- 2. 资产管理权限：asset:* → assets:*
-- ============================================
UPDATE permissions
SET code = 'assets:create',
    resource = 'assets',
    description = '创建资产'
WHERE code = 'asset:create';

UPDATE permissions
SET code = 'assets:read',
    resource = 'assets',
    description = '查看资产'
WHERE code = 'asset:read';

UPDATE permissions
SET code = 'assets:update',
    resource = 'assets',
    description = '更新资产'
WHERE code = 'asset:update';

UPDATE permissions
SET code = 'assets:delete',
    resource = 'assets',
    description = '删除资产'
WHERE code = 'asset:delete';

-- ============================================
-- 3. 验证修改结果
-- ============================================
DO $$
DECLARE
    project_count INTEGER;
    projects_count INTEGER;
    asset_count INTEGER;
    assets_count INTEGER;
BEGIN
    -- 统计单数形式权限（应该为 0）
    SELECT COUNT(*) INTO project_count
    FROM permissions
    WHERE code LIKE 'project:%';

    -- 统计复数形式权限
    SELECT COUNT(*) INTO projects_count
    FROM permissions
    WHERE code LIKE 'projects:%';

    -- 统计资产单数形式（应该为 0）
    SELECT COUNT(*) INTO asset_count
    FROM permissions
    WHERE code LIKE 'asset:%' AND code NOT LIKE 'assets:%';

    -- 统计资产复数形式
    SELECT COUNT(*) INTO assets_count
    FROM permissions
    WHERE code LIKE 'assets:%';

    -- 输出结果
    RAISE NOTICE '===========================================';
    RAISE NOTICE '权限代码修复验证结果';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'project:* (单数) 数量: % (应为 0)', project_count;
    RAISE NOTICE 'projects:* (复数) 数量: % (应为 4)', projects_count;
    RAISE NOTICE '';
    RAISE NOTICE 'asset:* (单数排除 assets:*) 数量: % (应为 0)', asset_count;
    RAISE NOTICE 'assets:* (复数) 数量: % (应为 4)', assets_count;
    RAISE NOTICE '===========================================';

    -- 检查是否修复成功
    IF project_count = 0 AND projects_count = 4 AND
       asset_count = 0 AND assets_count = 4 THEN
        RAISE NOTICE '✅ 权限代码修复成功！';
    ELSE
        RAISE NOTICE '⚠️  权限代码修复可能不完整，请手动检查！';
    END IF;
END $$;

-- ============================================
-- 4. 显示修改后的权限列表
-- ============================================
SELECT
    resource,
    action,
    code,
    name
FROM permissions
WHERE resource IN ('projects', 'assets')
ORDER BY resource, action;
