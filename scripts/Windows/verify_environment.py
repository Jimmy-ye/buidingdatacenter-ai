"""
BDC-AI 后端环境完整验证
"""

import subprocess
import sys
import os
from pathlib import Path

# ANSI 颜色
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}{title}{Colors.ENDC}")
    print("=" * 80 + "\n")

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 9:
        print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} Python 版本符合要求 (>= 3.9)")
        return True
    else:
        print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} Python 版本过低，需要 3.9+")
        return False

def check_postgresql():
    """检查 PostgreSQL"""
    try:
        result = subprocess.run(
            ["pg_config", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} PostgreSQL 已安装")
            print(f"  版本: {result.stdout.strip()}")
            return True
        else:
            print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} PostgreSQL 未找到")
            return False
    except:
        print(f"{Colors.WARNING}[WARN]{Colors.ENDC} PostgreSQL 命令行工具未找到（可能服务正在运行）")
        return True

def check_database_connection():
    """检查数据库连接"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="bdc_ai",
            user="admin",
            password="password"
        )
        conn.close()
        print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} 数据库连接成功")
        return True
    except Exception as e:
        print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} 数据库连接失败: {e}")
        return False

def check_dependencies():
    """检查依赖"""
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/Windows/check_dependencies.py'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # 解析输出
        lines = result.stdout.split('\n')
        for line in lines:
            if '已安装:' in line:
                parts = line.split('已安装:')
                if len(parts) == 2:
                    installed = int(parts[1].strip())
                    total = int(result.stdout.split('需要检查的依赖:')[1].split('个')[0])
                    if installed == total:
                        print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} 所有依赖已安装 ({installed}/{total})")
                        return True
        return False
    except Exception as e:
        print(f"{Colors.WARNING}[WARN]{Colors.ENDC} 无法检查依赖: {e}")
        return False

def check_backend_running():
    """检查后端服务是否运行"""
    try:
        import requests
        response = requests.get('http://localhost:8000/api/v1/health', timeout=2)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} 后端服务运行正常")
            print(f"  状态: {response.json()}")
            return True
        else:
            print(f"{Colors.WARNING}[WARN]{Colors.ENDC} 后端服务响应异常 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} 后端服务未运行: {e}")
        return False

def check_tailscale():
    """检查 Tailscale"""
    try:
        result = subprocess.run(
            ["tailscale", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # 提取 IP 地址
            for line in result.stdout.split('\n'):
                if '100.' in line:
                    ip = line.split()[0]
                    print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} Tailscale 已连接")
                    print(f"  IP: {ip}")
                    return True

        print(f"{Colors.WARNING}[WARN]{Colors.ENDC} Tailscale 未连接")
        return False
    except:
        print(f"{Colors.WARNING}[WARN]{Colors.ENDC} Tailscale 未安装")
        return False

def check_env_file():
    """检查环境变量文件"""
    env_files = [
        ('.env', '后端环境变量'),
        ('services/worker/.env', 'Worker 环境变量')
    ]

    all_exist = True
    for file_path, desc in env_files:
        if Path(file_path).exists():
            print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {desc} ({file_path})")
        else:
            print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {desc} 未找到 ({file_path})")
            all_exist = False

    return all_exist

def main():
    """主函数"""
    print_header("BDC-AI 后端环境完整验证")

    results = {
        'Python 版本': check_python_version(),
        'PostgreSQL': check_postgresql(),
        '数据库连接': check_database_connection(),
        '依赖包': check_dependencies(),
        '后端服务': check_backend_running(),
        'Tailscale': check_tailscale(),
        '环境变量': check_env_file(),
    }

    print_header("验证总结")

    all_ok = all(results.values())

    for item, status in results.items():
        if status:
            print(f"{Colors.OKGREEN}[✓]{Colors.ENDC} {item}")
        else:
            print(f"{Colors.FAIL}[✗]{Colors.ENDC} {item}")

    print()
    if all_ok:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ 所有检查通过！环境已就绪。{Colors.ENDC}")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"{Colors.WARNING}{Colors.BOLD}⚠ {failed_count} 项检查未通过，请检查。{Colors.ENDC}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
