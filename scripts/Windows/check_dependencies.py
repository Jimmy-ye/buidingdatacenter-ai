"""
检查后端依赖是否已安装
"""

import subprocess
import sys
import re
from pathlib import Path

def get_requirements():
    """解析 requirements.txt"""
    req_file = Path("services/backend/requirements.txt")

    if not req_file.exists():
        print(f"[ERROR] requirements.txt not found: {req_file}")
        sys.exit(1)

    requirements = []
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue

            # 提取包名（去掉版本号和extras）
            # 例如:
            # fastapi==0.104.1 -> fastapi
            # uvicorn[standard]==0.24.0 -> uvicorn
            # python-jose[cryptography]==3.3.0 -> python-jose
            match = re.match(r'^([a-zA-Z0-9_-]+)', line)
            if match:
                package_name = match.group(1)
                requirements.append({
                    'name': package_name,
                    'line': line
                })

    return requirements

def get_installed_packages():
    """获取已安装的包"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list'],
            capture_output=True,
            text=True,
            check=True
        )

        installed = {}
        for line in result.stdout.split('\n'):
            # 解析包名和版本
            # 格式: Package                Version
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0].lower()
                version = parts[1]
                installed[name] = version

        return installed
    except Exception as e:
        print(f"[ERROR] Failed to get installed packages: {e}")
        return {}

def check_requirements():
    """检查依赖"""
    print("=" * 80)
    print("BDC-AI 后端依赖检查")
    print("=" * 80)
    print()

    # 获取 requirements
    requirements = get_requirements()
    print(f"需要检查的依赖: {len(requirements)} 个")
    print()

    # 获取已安装的包
    installed = get_installed_packages()
    print(f"已安装的包: {len(installed)} 个")
    print()

    # 检查每个依赖
    missing = []
    installed_packages = []

    for req in requirements:
        name = req['name'].lower().replace('_', '-')

        if name in installed:
            installed_packages.append(req['name'])
            print(f"[OK] {req['name']:30s} - 已安装 (version: {installed[name]})")
        else:
            # 尝试其他可能的名称变体
            alt_names = [
                req['name'].replace('_', '-').lower(),
                req['name'].replace('-', '_').lower(),
                req['name'].lower()
            ]

            found = False
            for alt_name in alt_names:
                if alt_name in installed:
                    installed_packages.append(req['name'])
                    print(f"[OK] {req['name']:30s} - 已安装 (as: {alt_name}, version: {installed[alt_name]})")
                    found = True
                    break

            if not found:
                missing.append(req['name'])
                print(f"[MISSING] {req['name']:30s} - 未安装")

    # 总结
    print()
    print("=" * 80)
    print("检查总结")
    print("=" * 80)
    print(f"总计需要: {len(requirements)} 个")
    print(f"已安装: {len(installed_packages)} 个")
    print(f"缺失: {len(missing)} 个")
    print()

    if missing:
        print("缺失的依赖:")
        for pkg in missing:
            print(f"  - {pkg}")
        print()
        print("建议执行:")
        print("  cd D:\\BDC-AI")
        print("  venv\\Scripts\\pip.exe install -r services/backend/requirements.txt")
    else:
        print("[SUCCESS] 所有依赖都已安装！")

    print("=" * 80)

    return len(missing) == 0

if __name__ == '__main__':
    success = check_requirements()
    sys.exit(0 if success else 1)
