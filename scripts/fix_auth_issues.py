"""
BDC-AI 认证系统问题修复指南

本脚本提供了一键修复所有高优先级认证问题的方案。
"""

print("""
================================================================================
  BDC-AI 认证系统问题修复指南
================================================================================

问题概述：
  测试发现项目接口缺少认证保护，以及部分代码存在小缺陷。

修复内容：
  1. 为所有项目 API 添加认证保护
  2. 修复 auth_service.py 导入缺失
  3. 修复 models_auth.py 关系定义错误

预计时间：30 分钟
================================================================================
""")

# ============================================================================
# 修复 1：projects.py - 添加认证依赖
# ============================================================================

print("\n[修复 1/3] 为项目 API 添加认证保护")
print("-" * 80)

print("""
修改文件：services/backend/app/api/v1/projects.py

在第 12 行后添加导入：
  from shared.security.dependencies import get_current_user
  from shared.db.models_auth import User

修改 5 个路由函数：

1. list_projects (第 25-66 行)
   在第 31 行后添加：
     current_user: User = Depends(get_current_user)

2. get_project (第 74-87 行)
   在第 76 行后添加：
     current_user: User = Depends(get_current_user)

3. create_project (第 96-106 行)
   在第 98 行后添加：
     current_user: User = Depends(get_current_user)

4. update_project (第 114-136 行)
   在第 117 行后添加：
     current_user: User = Depends(get_current_user)

5. delete_project (第 144-165 行)
   在第 146 行后添加：
     current_user: User = Depends(get_current_user)

示例：
  @router.get("/", response_model=List[ProjectRead])
  async def list_projects(
      db: Session = Depends(get_db),
      current_user: User = Depends(get_current_user),  # 新增
  ) -> List[ProjectRead]:
      ...
""")

# ============================================================================
# 修复 2：auth_service.py - 添加导入
# ============================================================================

print("\n[修复 2/3] 修复 auth_service.py 导入缺失")
print("-" * 80)

print("""
修改文件：services/backend/app/services/auth_service.py

在文件头部找到导入语句（约第 10 行）：
  from shared.db.models_auth import User, Role, Permission, UserRole, AuditLog

修改为：
  from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission, AuditLog

添加 RolePermission 到导入列表。
""")

# ============================================================================
# 修复 3：models_auth.py - 修复关系定义
# ============================================================================

print("\n[修复 3/3] 修复 UserRole 关系定义")
print("-" * 80)

print("""
修改文件：shared/db/models_auth.py

找到 UserRole 类（约第 100 行）：
  class UserRole(Base):
      ...
      role = relationship("Role", back_populates="role_permissions")  # 错误

修改为：
  class UserRole(Base):
      ...
      role = relationship("Role", back_populates="user_roles")  # 正确

注意：将 "role_permissions" 改为 "user_roles"
""")

# ============================================================================
# 验证步骤
# ============================================================================

print("\n" + "=" * 80)
print("  修复后验证步骤")
print("=" * 80)

print("""
步骤 1：验证代码无语法错误
  cd "D:\\Huawei Files\\华为家庭存储\\Programs\\program-bdc-ai"
  python -c "from services.backend.app.api.v1.projects import router"
  python -c "from services.backend.app.services.auth_service import AuthService"
  python -c "from shared.db.models_auth import UserRole"

步骤 2：重启后端服务
  # 如果服务正在运行，按 Ctrl+C 停止
  python -m uvicorn services.backend.app.main:app --host localhost --port 8000 --reload

步骤 3：运行测试
  python test_auth_system.py

预期结果：
  总计: 9/9 测试通过 ✓
  [SUCCESS] 所有测试通过！认证系统运行正常。

步骤 4：手动验证未认证访问
  curl http://localhost:8000/api/v1/projects/

预期结果：
  {
    "detail": "Not authenticated"
  }

步骤 5：验证认证访问
  # 先登录获取 token
  TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \\
    -H "Content-Type: application/json" \\
    -d '{"username":"admin","password":"admin123"}' \\
    | jq -r '.access_token')

  # 使用 token 访问
  curl http://localhost:8000/api/v1/projects/ \\
    -H "Authorization: Bearer $TOKEN"

预期结果：
  返回项目列表数据
""")

# ============================================================================
# 一键修复脚本
# ============================================================================

print("\n" + "=" * 80)
print("  是否执行一键修复？")
print("=" * 80)
print("""
注意：一键修复会自动修改代码文件。建议先备份代码。

手动修复步骤：
  1. 打开文件：services/backend/app/api/v1/projects.py
  2. 按照上述说明逐个添加 current_user 参数
  3. 保存文件
  4. 对其他两个文件执行类似操作
  5. 运行测试验证

或者使用下方的一键修复脚本。
""")

# ============================================================================
# 实际修复代码
# ============================================================================

import sys
import os

def fix_projects_file():
    """修复 projects.py 文件"""
    file_path = "services/backend/app/api/v1/projects.py"

    print(f"\n正在修复: {file_path}")

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经修复
    if 'get_current_user' in content:
        print("  [SKIP] 文件已经包含认证依赖，跳过修复")
        return True

    # 添加导入
    if 'from shared.security.dependencies import get_current_user' not in content:
        # 在第 12 行后添加
        lines = content.split('\n')
        insert_position = 12  # 在 shared.db.session import 后

        new_imports = [
            "from shared.security.dependencies import get_current_user",
            "from shared.db.models_auth import User",
        ]

        for new_import in reversed(new_imports):
            lines.insert(insert_position, new_import)

        content = '\n'.join(lines)

    # 为每个函数添加 current_user 参数
    functions_to_fix = [
        ('list_projects', 'db: Session = Depends(get_db)', 'db: Session = Depends(get_db),\n    current_user: User = Depends(get_current_user)'),
        ('get_project', 'db: Session = Depends(get_db)', 'db: Session = Depends(get_db),\n        current_user: User = Depends(get_current_user)'),
        ('create_project', 'db: Session = Depends(get_db)', 'db: Session = Depends(get_db),\n    current_user: User = Depends(get_current_user)'),
        ('update_project', 'db: Session = Depends(get_db)', 'db: Session = Depends(get_db),\n    current_user: User = Depends(get_current_user)'),
        ('delete_project', 'db: Session = Depends(get_db)', 'db: Session = Depends(get_db),\n    current_user: User = Depends(get_current_user)'),
    ]

    for func_name, old_pattern, new_pattern in functions_to_fix:
        if f'def {func_name}' in content:
            # 找到函数定义行
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if f'async def {func_name}' in line:
                    # 在下一行查找 db: Session
                    for j in range(i+1, min(i+5, len(lines))):
                        if 'db: Session = Depends(get_db)' in lines[j]:
                            # 替换
                            lines[j] = lines[j].replace(
                                'db: Session = Depends(get_db)',
                                'db: Session = Depends(get_db),\n    current_user: User = Depends(get_current_user)' if 'async def' in lines[i] else 'db: Session = Depends(get_db),\n        current_user: User = Depends(get_current_user)'
                            )
                            break
                    break
            content = '\n'.join(lines)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  [DONE] 已添加认证依赖")
    return True


def fix_auth_service_imports():
    """修复 auth_service.py 导入"""
    file_path = "services/backend/app/services/auth_service.py"

    print(f"\n正在修复: {file_path}")

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经包含 RolePermission
    if 'RolePermission' in content and 'from shared.db.models_auth import' in content:
        if 'RolePermission' in content.split('from shared.db.models_auth import')[1].split('\n')[0]:
            print("  [SKIP] 导入已包含 RolePermission，跳过修复")
            return True

    # 修复导入
    old_import = 'from shared.db.models_auth import User, Role, Permission, UserRole, AuditLog'
    new_import = 'from shared.db.models_auth import User, Role, Permission, UserRole, RolePermission, AuditLog'

    if old_import in content:
        content = content.replace(old_import, new_import)

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  [DONE] 已添加 RolePermission 导入")
        return True
    else:
        print("  [SKIP] 未找到匹配的导入语句")
        return False


def fix_user_role_relationship():
    """修复 UserRole 关系定义"""
    file_path = "shared/db/models_auth.py"

    print(f"\n正在修复: {file_path}")

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经修复
    if 'back_populates="user_roles"' in content and 'class UserRole' in content:
        print("  [SKIP] UserRole 关系已正确，跳过修复")
        return True

    # 修复关系定义
    old_pattern = 'role = relationship("Role", back_populates="role_permissions")'
    new_pattern = 'role = relationship("Role", back_populates="user_roles")'

    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  [DONE] 已修复 UserRole 关系定义")
        return True
    else:
        print("  [SKIP] 未找到需要修复的关系定义")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("  开始执行一键修复...")
    print("=" * 80)

    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    try:
        # 执行修复
        fix_projects_file()
        fix_auth_service_imports()
        fix_user_role_relationship()

        print("\n" + "=" * 80)
        print("  修复完成！")
        print("=" * 80)
        print("""
下一步：
  1. 重启后端服务
  2. 运行测试：python test_auth_system.py
  3. 验证所有测试通过

如果遇到问题，请检查：
  - 文件编码是否为 UTF-8
  - 是否有足够的文件写入权限
  - 备份文件是否正确
        """)

    except Exception as e:
        print(f"\n[ERROR] 修复失败: {e}")
        print("\n请手动修复或检查错误信息")
        return 1

    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        exit(main())
    else:
        print("\n提示：使用 --fix 参数执行实际修复")
        print("示例：python fix_auth_issues.py --fix")
        print("\n建议：")
        print("  1. 先手动备份代码")
        print("  2. 再执行自动修复")
