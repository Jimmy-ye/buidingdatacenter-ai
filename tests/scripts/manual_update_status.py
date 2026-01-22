"""
手动在数据库中将 meter 资产的状态改为 pending_scene_llm
"""
import uuid
from shared.db.session import SessionLocal
from shared.db.models_asset import Asset
from shared.config.settings import get_settings

# 新上传的资产 ID
ASSET_ID = "121e1bc0-ce7e-4edf-8c44-8709f21ee17c"

def manual_update_status():
    db = SessionLocal()
    try:
        # 查询资产
        asset = db.query(Asset).filter(Asset.id == ASSET_ID).one_or_none()
        if not asset:
            print(f"[ERROR] 资产不存在: {ASSET_ID}")
            return

        print(f"[INFO] 当前资产信息：")
        print(f"  - ID: {asset.id}")
        print(f"  - Title: {asset.title}")
        print(f"  - Content Role: {asset.content_role}")
        print(f"  - 当前状态: {asset.status}")

        # 手动更新状态
        print(f"\n[INFO] 手动更新状态为 pending_scene_llm...")
        asset.status = "pending_scene_llm"
        db.commit()

        # 验证更新
        db.refresh(asset)
        print(f"[SUCCESS] 状态已更新为: {asset.status}")

        print(f"\n[INFO] 现在 Worker 应该会处理这个资产...")
        print(f"[INFO] 处理完成后状态会变为: parsed_scene_llm")

    finally:
        db.close()

if __name__ == "__main__":
    manual_update_status()
