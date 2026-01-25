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

# 全局变量：psql 可执行文件路径
psql_path = None


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

    # 全局变量存储 psql 路径
    global psql_path

    psql_path = None

    # 方法 1：尝试从 PATH 运行 psql
    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"✓ PostgreSQL 已配置到 PATH")
            print(f"  版本信息: {result.stdout.strip()}")
            psql_path = "psql"
            return True
    except Exception as e:
        print(f"⚠ PostgreSQL 未在 PATH 中: {e}")

    # 方法 2：尝试查找 PostgreSQL 18（D 盘默认路径）
    print(f"\n尝试查找 PostgreSQL 18...")

    possible_paths = [
        Path(r"D:\Program Files\PostgreSQL\18\bin\psql.exe"),
        Path(r"C:\Program Files\PostgreSQL\18\bin\psql.exe"),
        Path(r"D:\Program Files (x86)\PostgreSQL\18\bin\psql.exe"),
        Path(r"C:\Program Files (x86)\PostgreSQL\18\bin\psql.exe"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"✓ 找到 PostgreSQL 18: {path}")
            psql_path = str(path)
            print(f"  将使用完整路径执行命令")
            return True

    print(f"✗ 未找到 PostgreSQL 18")
    print(f"\n请确保：")
    print(f"  1. PostgreSQL 18 已安装")
    print(f"     默认路径: D:\\Program Files\\PostgreSQL\\18")
    print(f"  2. 将 PostgreSQL bin 目录添加到 PATH")
    print(f"     方法: 运行此脚本后，执行: $env:Path += ';D:\\Program Files\\PostgreSQL\\18\\bin'")
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
    global psql_path

    # 使用检测到的 psql 路径
    if psql_path is None:
        print("❌ psql 路径未找到")
        return False

    # 输入密码
    print()
    print("="*60)
    print("PostgreSQL 认证")
    print("="*60)
    password = input("请输入 postgres 用户密码: ").strip()

    if not password:
        print("❌ 密码不能为空")
        return False

    # 如果是完整路径，需要用引号包裹
    psql_cmd = f'& "{psql_path}"' if '\\' in psql_path else psql_path

    sql_commands = """
-- 创建数据库
CREATE DATABASE bdc_ai;

-- 验证创建
SELECT 'Database created successfully!' AS status;
"""

    # 设置 PGPASSWORD 环境变量
    env = os.environ.copy()
    env['PGPASSWORD'] = password

    cmd = f"{psql_cmd} -U postgres -c \"{sql_commands.strip()}\""

    try:
        # Windows PowerShell，传递环境变量
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            env=env,
            capture_output=True,
            text=True,
            check=False
        )

        print(result.stdout)
        if result.stderr:
            # 检查是否是"已存在"错误
            if 'already exists' in result.stderr or '数据库已存在' in result.stderr:
                print("✓ 数据库 'bdc_ai' 已存在")
                return True
            elif 'password authentication failed' in result.stderr or '密码认证失败' in result.stderr:
                print("❌ 密码错误，请检查 postgres 用户密码")
                return False
            else:
                print(f"错误: {result.stderr}")
                return False

        print("✓ 数据库 'bdc_ai' 创建成功")
        return True
    except Exception as e:
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
    global psql_path

    if psql_path is None:
        print("❌ psql 路径未找到")
        return False

    psql_cmd = f'& "{psql_path}"' if '\\' in psql_path else psql_path

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

    cmd = f"{psql_cmd} -U postgres -d bdc_ai -c \"{sql_commands.strip()}\""

    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            check=False
        )

        print(result.stdout)
        if result.stderr:
            # 只显示真正的错误，忽略 NOTICE
            for line in result.stderr.split('\n'):
                if line.strip() and 'NOTICE' not in line.upper():
                    print(f"警告: {line}")

        return True
    except Exception as e:
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
