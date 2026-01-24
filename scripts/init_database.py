"""
BDC-AI 数据库初始化脚本（Windows）

功能：
1. 连接到 PostgreSQL 18
2. 创建 bdc_ai 数据库
3. 验证数据库创建
4. 初始化数据库表
5. 验证表创建

使用方法：
    python scripts/init_database.py
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """运行命令并显示输出"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print('='*60)

    try:
        if isinstance(command, str):
            if command.startswith("psql"):
                # Windows PowerShell
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(result.stdout)
        else:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if hasattr(e, 'stderr'):
            print(f"错误输出: {e.stderr}")
        return False


def check_postgresql_path():
    """检查 PostgreSQL 是否在 PATH 中"""
    print(f"\n{'='*60}")
    print("  检查 PostgreSQL 安装")
    print('='*60)

    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ PostgreSQL 已安装")
            print(f"  版本信息: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠ PostgreSQL 可能未安装或未配置到 PATH")

            # 尝试查找 PostgreSQL 18
            pg_path = Path(r"D:\Program Files\PostgreSQL\18\bin\psql.exe")
            if pg_path.exists():
                print(f"✓ 找到 PostgreSQL 18: {pg_path.parent}")
                print(f"  提示: 可使用完整路径: & '{pg_path}' -U postgres")
                return True
            else:
                print(f"✗ 未找到 PostgreSQL 18")
                return False

    except FileNotFoundError:
        print(f"✗ psql 命令未找到")
        print(f"\n请确保：")
        print(f"  1. PostgreSQL 18 已安装")
        print(f"  2. PostgreSQL bin 目录已添加到 PATH")
        print(f"     默认路径: D:\\Program Files\\PostgreSQL\\18\\bin")
        return False


def test_database_connection():
    """测试数据库连接"""
    psql_commands = [
        "psql -U postgres -c \"SELECT current_database(), current_user;\""
    ]

    cmd = "; ".join([
        f'& "D:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe"'
        if not run_command else "psql",
        *psql_commands
    ])

    try:
        subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except:
        return False


def create_database():
    """创建数据库"""
    sql_commands = """
-- 创建数据库
CREATE DATABASE bdc_ai;

-- 验证创建
SELECT 'Database created successfully!' AS status;
"""

    cmd = f"psql -U postgres -c \"{sql_commands.strip()}\""

    try:
        # Windows PowerShell
        subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ 数据库 'bdc_ai' 创建成功")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = str(e)
        if 'already exists' in error_msg or '数据库已存在' in error_msg:
            print("✓ 数据库 'bdc_ai' 已存在")
            return True
        else:
            print(f"❌ 创建数据库失败: {e}")
            return False


def initialize_database():
    """初始化数据库表"""
    project_root = Path(__file__).parent.parent

    # 检查虚拟环境
    venv_python = project_root / "venv" / "Scripts" / "python.exe"

    if not venv_python.exists():
        print("❌ 未找到虚拟环境，请先创建虚拟环境")
        print(f"  预期路径: {venv_python}")
        return False

    init_script = project_root / "scripts" / "init_auth_db.py"

    if not init_script.exists():
        print(f"❌ 未找到初始化脚本: {init_script}")
        return False

    print(f"\n{'='*60}")
    print("  初始化数据库表")
    print('='*60)

    try:
        result = subprocess.run(
            [str(venv_python), str(init_script)],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(project_root)
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 初始化失败: {e}")
        print(f"  请检查虚拟环境是否激活")
        print(f"  请检查依赖是否已安装: pip install -r services/backend/requirements.txt")
        return False


def verify_tables():
    """验证表创建"""
    sql_commands = """
-- 查看所有表
\\dt

-- 验证关键表
SELECT 'users' AS table_name, COUNT(*) FROM users
UNION ALL
SELECT 'roles' AS table_name, COUNT(*) FROM roles
UNION ALL
SELECT 'permissions' AS table_name, COUNT(*) FROM permissions;
"""

    cmd = f"psql -U postgres -d bdc_ai -c \"{sql_commands.strip()}\""

    try:
        subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("BDC-AI 数据库初始化向导")
    print("="*60)
    print()
    print("此脚本将完成以下操作：")
    print("  1. 检查 PostgreSQL 安装")
    print("  2. 创建 bdc_ai 数据库")
    print("  3. 初始化数据库表（用户、角色、权限）")
    print("  4. 验证表创建")
    print()

    input("按 Enter 继续...")

    # 检查 PostgreSQL
    if not check_postgresql_path():
        print("\n❌ PostgreSQL 未正确安装，请先安装 PostgreSQL 18")
        print("下载地址: https://www.postgresql.org/download/windows/")
        sys.exit(1)

    print()
    input("按 Enter 继续...")

    # 测试连接
    print()
    print("提示：即将测试数据库连接，可能需要输入密码...")
    print("      如果提示密码，请输入 PostgreSQL 超级用户密码")
    print()

    input("准备好后按 Enter 继续...")

    # 创建数据库
    print()
    if not create_database():
        print("\n❌ 数据库创建失败")
        sys.exit(1)

    input("按 Enter 继续...")

    # 初始化表
    print()
    if not initialize_database():
        print("\n❌ 数据库初始化失败")
        sys.exit(1)

    input("按 Enter 继续...")

    # 验证表
    print()
    if not verify_tables():
        print("\n❌ 表验证失败")
        sys.exit(1)

    # 完成
    print()
    print("="*60)
    print("  ✅ 数据库初始化完成！")
    print("="*60)
    print()
    print("下一步操作：")
    print()
    print("1. 启动后端服务")
    print("   python -m uvicorn services.backend.app.main:app --host localhost --port 8000")
    print()
    print("2. 测试连接")
    print("   curl http://localhost:8000/health")
    print()
    print("3. 查看数据库")
    print("   psql -U postgres -d bdc_ai")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ 已取消")
        sys.exit(0)
