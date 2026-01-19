#!/usr/bin/env python3
"""检查 SQLite 数据的外键完整性"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from shared.db.models_asset import Asset
from shared.db.models_project import Project

SQLITE_DB_PATH = project_root / "data" / "bdc_ai.db"
SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH}"

engine = create_engine(SQLITE_URL)
session = Session(bind=engine)

# 检查 assets 中的 project_id 是否都存在
print("检查 assets 的外键完整性...")
assets = session.query(Asset).all()
print(f"总资产数: {len(assets)}")

# 获取所有 project_id
project_ids = set([p.id for p in session.query(Project).all()])
print(f"Projects 表中的 UUID 数量: {len(project_ids)}")

# 检查孤立记录
orphan_assets = []
for asset in assets:
    if asset.project_id and asset.project_id not in project_ids:
        orphan_assets.append(asset)

print(f"\n发现 {len(orphan_assets)} 条孤立记录:")
for asset in orphan_assets[:5]:
    print(f"  Asset ID: {asset.id}")
    print(f"  Project ID: {asset.project_id} (不存在)")
    print(f"  Title: {asset.title}")
    print()

session.close()
