"""
BDC-AI API KEY 配置脚本

功能：
1. 生成强随机 JWT 密钥
2. 创建后端服务 .env 配置
3. 创建 Worker 服务 .env 配置
4. 设置文件权限

使用方法：
    python scripts/setup_api_keys.py

注意事项：
    - 此脚本会生成新的配置文件，不会覆盖现有 .env
    - 请手动输入从 https://open.bigmodel.cn/ 获取的 API KEY
    - 配置完成后请删除旧的 API KEY
"""

import os
import secrets
import sys
from pathlib import Path


def generate_jwt_secret():
    """生成强随机 JWT 密钥（64 字符 hex）"""
    return secrets.token_hex(32)


def create_backend_env(project_root: Path, jwt_secret: str, glm_api_key: str):
    """创建后端服务 .env 配置"""
    env_content = f"""# BDC-AI 后端服务配置
# 自动生成于：{os.popen('date /t && time /t').read().strip()}

# ================= 数据库配置 =================
# PostgreSQL 数据库连接 URL
BDC_DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# ================= 本地存储配置 =================
# 本地文件存储目录
BDC_LOCAL_STORAGE_DIR=data/assets

# ================= JWT 认证配置 =================
# JWT 密钥（强随机生成，请勿泄露）
BDC_JWT_SECRET_KEY={jwt_secret}

# Access Token 过期时间（分钟）
BDC_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Refresh Token 过期时间（天）
BDC_REFRESH_TOKEN_EXPIRE_DAYS=7

# ================= GLM API 配置 =================
# GLM API Key（从 https://open.bigmodel.cn/ 获取）
GLM_API_KEY={glm_api_key}

# GLM API 基础 URL
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# GLM 视觉模型
GLM_VISION_MODEL=glm-4v

# ================= MinIO 对象存储（可选）=================
# 如需使用 MinIO，请取消注释并配置
# BDC_MINIO_ENDPOINT=localhost:9000
# BDC_MINIO_ACCESS_KEY=minioadmin
# BDC_MINIO_SECRET_KEY=minioadmin
# BDC_MINIO_BUCKET=bdc-assets

# ================= 服务配置 =================
# 后端服务监听地址
BDC_HOST=0.0.0.0

# 后端服务端口
BDC_PORT=8000

# 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
BDC_LOG_LEVEL=INFO

# 调试模式（生产环境设置为 false）
BDC_DEBUG=false
"""
    return env_content


def create_worker_env(project_root: Path, glm_api_key: str, backend_url: str = "http://localhost:8000"):
    """创建 Worker 服务 .env 配置"""
    env_content = f"""# BDC-AI Worker 服务配置
# 自动生成于：{os.popen('date /t && time /t').read().strip()}

# ================= 后端连接配置 =================
# 后端服务基础 URL
BDC_BACKEND_BASE_URL={backend_url}

# ================= 本地存储配置 =================
# 本地存储目录（必须与后端配置一致）
BDC_LOCAL_STORAGE_DIR=../data/assets

# ================= GLM API 配置 =================
# GLM API Key（建议使用独立 KEY，便于监控和隔离）
# 获取地址：https://open.bigmodel.cn/
GLM_API_KEY={glm_api_key}

# GLM API 基础 URL
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# GLM 视觉模型
GLM_VISION_MODEL=glm-4v

# ================= Worker 配置 =================
# Worker 轮询间隔（秒）
# 默认 60 秒，即每分钟检查一次新任务
BDC_SCENE_WORKER_POLL_INTERVAL=60

# 可选：仅处理特定项目的场景问题
# 留空则处理所有项目的 scene_issue 类型资产
# BDC_SCENE_PROJECT_ID=
"""
    return env_content


def set_file_permissions(file_path: Path):
    """设置文件权限（仅所有者可读写）"""
    try:
        os.chmod(file_path, 0o600)  # rw-------
        print(f"✓ 已设置文件权限: {file_path}")
    except Exception as e:
        print(f"⚠ 无法设置文件权限: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("BDC-AI API KEY 配置向导")
    print("=" * 60)
    print()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    print(f"📂 项目根目录: {project_root}")
    print()

    # Step 1: 生成 JWT 密钥
    print("=" * 60)
    print("步骤 1/3: 生成 JWT 密钥")
    print("=" * 60)
    jwt_secret = generate_jwt_secret()
    print(f"✓ 已生成强随机 JWT 密钥（64 字符 hex）")
    print(f"  密钥: {jwt_secret[:16]}...{jwt_secret[-16:]}")
    print(f"  完整密钥: {jwt_secret}")
    print()
    print("⚠ 请将此密钥保存到安全位置（密码管理器）！")
    print()

    input("按 Enter 继续...")
    print()

    # Step 2: 输入后端 API KEY
    print("=" * 60)
    print("步骤 2/3: 配置后端 API KEY")
    print("=" * 60)
    print()
    print("请从以下地址获取后端服务 API KEY:")
    print("🔗 https://open.bigmodel.cn/apikeys")
    print()
    backend_api_key = input("请输入后端服务 GLM API KEY: ").strip()

    while not backend_api_key or backend_api_key == "your-glm-api-key-here":
        print("❌ API KEY 不能为空，请重新输入")
        backend_api_key = input("请输入后端服务 GLM API KEY: ").strip()

    print(f"✓ 后端 API KEY: {backend_api_key[:16]}...{backend_api_key[-8:]}")
    print()

    input("按 Enter 继续...")
    print()

    # Step 3: 输入 Worker API KEY
    print("=" * 60)
    print("步骤 3/3: 配置 Worker API KEY")
    print("=" * 60)
    print()
    print("建议：Worker 使用独立的 API KEY，便于监控和隔离")
    print("     如果使用同一个 KEY，直接按 Enter 确认")
    print()

    worker_api_key = input("请输入 Worker GLM API KEY (留空使用后端相同 KEY): ").strip()

    if not worker_api_key:
        worker_api_key = backend_api_key
        print("✓ Worker 使用与后端相同的 API KEY")
    else:
        print(f"✓ Worker API KEY: {worker_api_key[:16]}...{worker_api_key[-8:]}")

    print()

    # 确认配置
    print("=" * 60)
    print("配置摘要")
    print("=" * 60)
    print(f"JWT 密钥: {jwt_secret[:16]}...{jwt_secret[-16:]}")
    print(f"后端 API KEY: {backend_api_key[:16]}...{backend_api_key[-8:]}")
    print(f"Worker API KEY: {worker_api_key[:16]}...{worker_api_key[-8:]}")
    print()

    confirm = input("确认生成配置文件？(y/n): ").strip().lower()

    if confirm != 'y':
        print("❌ 已取消配置")
        sys.exit(0)

    print()
    print("✓ 开始生成配置文件...")
    print()

    # 创建备份
    backend_env = project_root / ".env"
    worker_env = project_root / "services" / "worker" / ".env"

    backup_suffix = ".backup"

    if backend_env.exists():
        backup_path = backend_env.with_suffix(backup_suffix)
        backend_env.rename(backup_path)
        print(f"✓ 已备份现有配置: {backup_path}")

    if worker_env.exists():
        backup_path = worker_env.with_suffix(backup_suffix)
        worker_env.rename(backup_path)
        print(f"✓ 已备份现有配置: {backup_path}")

    print()

    # 生成配置文件
    try:
        # 创建后端配置
        backend_content = create_backend_env(project_root, jwt_secret, backend_api_key)
        backend_env.write_text(backend_content, encoding='utf-8')
        print(f"✓ 已创建后端配置: {backend_env.relative_to(project_root)}")
        set_file_permissions(backend_env)

        # 创建 Worker 配置
        worker_content = create_worker_env(project_root, worker_api_key)
        worker_env.write_text(worker_content, encoding='utf-8')
        print(f"✓ 已创建 Worker 配置: {worker_env.relative_to(project_root)}")
        set_file_permissions(worker_env)

        print()
        print("=" * 60)
        print("✅ 配置完成！")
        print("=" * 60)
        print()
        print("下一步操作：")
        print()
        print("1. 验证配置文件")
        print(f"   cat {backend_env.relative_to(project_root)}")
        print(f"   cat {worker_env.relative_to(project_root)}")
        print()
        print("2. 启动后端服务")
        print("   python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000")
        print()
        print("3. 启动 Worker 服务（新终端）")
        print("   python services/worker/scene_issue_glm_worker.py")
        print()
        print("4. 测试 API 连接")
        print("   curl http://localhost:8000/health")
        print()
        print("⚠ 重要提醒：")
        print("   - 请访问 https://open.bigmodel.cn/apikeys")
        print("   - 撤销已暴露的旧 API KEY")
        print("   - 将新的密钥保存到密码管理器")
        print()

    except Exception as e:
        print()
        print(f"❌ 配置失败: {e}")
        print()
        print("请检查：")
        print("1. 是否有写入权限")
        print("2. 磁盘空间是否充足")
        print("3. 文件是否被占用")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ 已取消配置")
        sys.exit(0)
