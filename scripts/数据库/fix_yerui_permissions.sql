-- ===================================================================
-- 权限初始化 SQL 脚本
-- 用于在现有数据库上修复 yerui 用户权限
-- ===================================================================

-- 1. 将 yerui 设置为超级用户（保底方案）
UPDATE users SET is_superuser = true WHERE username = 'yerui';

-- 2. 如果 yerui 不存在，创建它（先注释，由 Python 脚本处理）
-- INSERT INTO users (id, username, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
-- VALUES (
--     gen_random_uuid(),
--     'yerui',
--     'yerui@bdc-ai.com',
--     '<hashed_password>',
--     '超级管理员',
--     true,
--     true,
--     CURRENT_TIMESTAMP,
--     CURRENT_TIMESTAMP
-- );

-- 3. 检查并创建必要的权限（如果不存在）
INSERT INTO permissions (code, name, description, resource, action, created_at)
VALUES
  -- 用户管理权限
  ('user:create', '创建用户', '创建新用户', 'user', 'create', CURRENT_TIMESTAMP),
  ('user:read', '查看用户', '查看用户列表和详情', 'user', 'read', CURRENT_TIMESTAMP),
  ('user:update', '更新用户', '更新用户信息', 'user', 'update', CURRENT_TIMESTAMP),
  ('user:delete', '删除用户', '删除用户', 'user', 'delete', CURRENT_TIMESTAMP),

  -- 角色管理权限
  ('role:create', '创建角色', '创建新角色', 'role', 'create', CURRENT_TIMESTAMP),
  ('role:read', '查看角色', '查看角色列表', 'role', 'read', CURRENT_TIMESTAMP),
  ('role:update', '更新角色', '更新角色信息', 'role', 'update', CURRENT_TIMESTAMP),
  ('role:delete', '删除角色', '删除角色', 'role', 'delete', CURRENT_TIMESTAMP),

  -- 项目管理权限
  ('project:create', '创建项目', '创建新项目', 'project', 'create', CURRENT_TIMESTAMP),
  ('project:read', '查看项目', '查看项目列表和详情', 'project', 'read', CURRENT_TIMESTAMP),
  ('project:update', '更新项目', '更新项目信息', 'project', 'update', CURRENT_TIMESTAMP),
  ('project:delete', '删除项目', '删除项目', 'project', 'delete', CURRENT_TIMESTAMP),

  -- 资产管理权限
  ('asset:create', '创建资产', '创建新资产', 'asset', 'create', CURRENT_TIMESTAMP),
  ('asset:read', '查看资产', '查看资产列表和详情', 'asset', 'read', CURRENT_TIMESTAMP),
  ('asset:update', '更新资产', '更新资产信息', 'asset', 'update', CURRENT_TIMESTAMP),
  ('asset:delete', '删除资产', '删除资产', 'asset', 'delete', CURRENT_TIMESTAMP),

  -- 系统管理权限
  ('system:config', '系统配置', '系统配置管理', 'system', 'config', CURRENT_TIMESTAMP),
  ('audit:read', '查看审计日志', '查看审计日志', 'audit', 'read', CURRENT_TIMESTAMP),

  -- 工程结构权限（PC-UI 需要）
  ('structures:create', '创建结构', '创建楼栋/系统/区域/设备', 'structures', 'create', CURRENT_TIMESTAMP),
  ('structures:read', '查看结构', '查看工程结构', 'structures', 'read', CURRENT_TIMESTAMP),
  ('structures:update', '更新结构', '更新工程结构', 'structures', 'update', CURRENT_TIMESTAMP),
  ('structures:delete', '删除结构', '删除工程结构', 'structures', 'delete', CURRENT_TIMESTAMP),

  -- 资产操作权限（PC-UI 需要）
  ('assets:upload', '上传资产', '上传多模态资产', 'assets', 'upload', CURRENT_TIMESTAMP),
  ('assets:read', '查看资产', '查看资产列表和详情', 'assets', 'read', CURRENT_TIMESTAMP),

  -- OCR 和 LLM 权限（PC-UI 需要）
  ('ocr:run', '运行OCR', '运行OCR识别', 'ocr', 'run', CURRENT_TIMESTAMP),
  ('llm:run', '运行LLM', '运行大模型分析', 'llm', 'run', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 4. 给 superadmin 角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT
  (SELECT id FROM roles WHERE name = 'superadmin'),
  id,
  CURRENT_TIMESTAMP
FROM permissions
ON CONFLICT DO NOTHING;

-- 5. 确保 yerui 有 superadmin 角色
INSERT INTO user_roles (user_id, role_id, created_at)
SELECT
  (SELECT id FROM users WHERE username = 'yerui'),
  (SELECT id FROM roles WHERE name = 'superadmin'),
  CURRENT_TIMESTAMP
ON CONFLICT DO NOTHING;

-- 6. 确保 admin 也有 superadmin 角色
INSERT INTO user_roles (user_id, role_id, created_at)
SELECT
  (SELECT id FROM users WHERE username = 'admin'),
  (SELECT id FROM roles WHERE name = 'superadmin'),
  CURRENT_TIMESTAMP
ON CONFLICT DO NOTHING;

-- 7. 验证结果
SELECT
  u.username,
  u.is_superuser,
  u.is_active,
  COUNT(rp.permission_id) as permission_count
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
LEFT JOIN role_permissions rp ON rp.role_id = r.id
WHERE u.username IN ('yerui', 'admin')
GROUP BY u.username, u.is_superuser, u.is_active
ORDER BY u.username;
