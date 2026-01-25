"""创建默认管理员账号（简化版）"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.db.session import SessionLocal
from shared.db.models_auth import User
from shared.security.password import get_password_hash

def create_admin_user():
    """创建默认管理员账号"""
    db = SessionLocal()

    try:
        # 检查是否已存在管理员
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists")
            return existing_admin

        # 创建管理员账号
        admin = User(
            username="admin",
            email="admin@bdc-ai.com",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"[OK] Admin user created: {admin.username}")
        print(f"[OK] Email: {admin.email}")
        print(f"[OK] Default password: admin123")
        print("[!] Please change the password after first login!")
        print()

        return admin

    except Exception as e:
        print(f"[ERROR] Failed to create admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("BDC-AI - Create Admin User")
    print("=" * 50)
    print()

    create_admin_user()

    print()
    print("=" * 50)
    print("Done!")
    print("=" * 50)
