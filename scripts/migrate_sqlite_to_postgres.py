#!/usr/bin/env python3
"""
SQLite → PostgreSQL 数据迁移脚本
迁移时间: 2025-01-19
数据库: bdc_ai.db (161 条记录) → PostgreSQL 18.1
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from shared.db.base import Base
from shared.db.models_project import Project, Building, Zone, BuildingSystem, Device
from shared.db.models_asset import FileBlob, Asset, AssetStructuredPayload, AssetFeature

# 连接配置
SQLITE_DB_PATH = project_root / "data" / "bdc_ai.db"
SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH}"
POSTGRES_URL = "postgresql://admin:password@localhost:5432/bdc_ai"


def migrate():
    print("=" * 70)
    print("SQLite → PostgreSQL 数据迁移")
    print("=" * 70)
    print(f"\n源数据库: {SQLITE_DB_PATH}")
    print(f"目标数据库: {POSTGRES_URL}")
    print("")

    # 检查 SQLite 数据库是否存在
    if not SQLITE_DB_PATH.exists():
        print(f"❌ 错误: SQLite 数据库不存在: {SQLITE_DB_PATH}")
        sys.exit(1)

    # 1. 连接 SQLite（源）
    print("[1/6] 连接到 SQLite 数据库...")
    sqlite_engine = create_engine(SQLITE_URL, echo=False)
    sqlite_session = Session(bind=sqlite_engine)
    print("    ✓ SQLite 连接成功")

    # 2. 连接 PostgreSQL（目标）
    print("[2/6] 连接到 PostgreSQL 数据库...")
    try:
        postgres_engine = create_engine(POSTGRES_URL, echo=False, pool_pre_ping=True)
        # 测试连接
        with postgres_engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print("    [OK] PostgreSQL 连接成功")
    except Exception as e:
        print(f"    [ERROR] PostgreSQL 连接失败: {e}")
        print("\n请检查:")
        print("  1. PostgreSQL 服务是否启动")
        print("  2. .env 文件中的 BDC_DATABASE_URL 是否正确")
        print("  3. 数据库和用户是否已创建")
        sys.exit(1)

    # 3. 创建所有表（PostgreSQL 会自动使用正确的 UUID 类型）
    print("[3/6] 在 PostgreSQL 中创建表结构...")
    Base.metadata.drop_all(bind=postgres_engine)  # 清空旧表（如果存在）
    Base.metadata.create_all(bind=postgres_engine)
    print("    ✓ 表结构创建完成")

    postgres_session = Session(bind=postgres_engine)

    # 4. 迁移数据（按外键依赖顺序）
    print("[4/6] 开始迁移数据...")

    total_migrated = 0
    errors = []

    try:
        # 4.1 Projects
        print("    [1/8] Migrating projects...")
        projects = sqlite_session.query(Project).all()
        print(f"        Debug: Read {len(projects)} projects from SQLite")

        for i, p in enumerate(projects):
            try:
                new_p = Project(
                    id=p.id,
                    name=p.name,
                    client=p.client,
                    location=p.location,
                    type=p.type,
                    status=p.status,
                    start_date=p.start_date,
                    end_date=p.end_date
                )
                postgres_session.add(new_p)

                # Log first 3 for debugging
                if i < 3:
                    print(f"        Debug: Adding project {i+1}: id={p.id}, name={p.name}")
            except Exception as e:
                print(f"        [ERROR] Failed to insert project {p.id}: {e}")
                errors.append(f"Project {p.id}: {e}")

        try:
            postgres_session.commit()
            print(f"        Debug: Commit completed")
        except Exception as e:
            print(f"        [ERROR] Commit failed: {e}")
            postgres_session.rollback()
            raise

        # Verify count after commit
        actual_count = postgres_session.query(Project).count()
        print(f"        Debug: Actual PostgreSQL project count: {actual_count}")
        print(f"        [OK] projects: {len(projects)} records")
        total_migrated += len(projects)

        # 4.2 Buildings
        print("    [2/8] 迁移 buildings...")
        buildings = sqlite_session.query(Building).all()
        for b in buildings:
            try:
                new_b = Building(
                    id=b.id,
                    project_id=b.project_id,
                    name=b.name,
                    usage_type=b.usage_type,
                    floor_area=b.floor_area,
                    gfa_area=getattr(b, "gfa_area", None),
                    year_built=b.year_built,
                )
                postgres_session.add(new_b)
            except Exception as e:
                errors.append(f"Building {b.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ buildings: {len(buildings)} 条")
        total_migrated += len(buildings)

        # 4.3 Zones
        print("    [3/8] 迁移 zones...")
        zones = sqlite_session.query(Zone).all()
        for z in zones:
            try:
                new_z = Zone(
                    id=z.id,
                    building_id=z.building_id,
                    name=z.name,
                    type=z.type,
                    geometry_ref=z.geometry_ref
                )
                postgres_session.add(new_z)
            except Exception as e:
                errors.append(f"Zone {z.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ zones: {len(zones)} 条")
        total_migrated += len(zones)

        # 4.4 BuildingSystems
        print("    [4/8] 迁移 systems...")
        systems = sqlite_session.query(BuildingSystem).all()
        for s in systems:
            try:
                new_s = BuildingSystem(
                    id=s.id,
                    building_id=s.building_id,
                    name=s.name,
                    type=s.type,
                    description=s.description
                )
                postgres_session.add(new_s)
            except Exception as e:
                errors.append(f"BuildingSystem {s.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ systems: {len(systems)} 条")
        total_migrated += len(systems)

        # 4.5 Devices
        print("    [5/8] 迁移 devices...")
        devices = sqlite_session.query(Device).all()
        for d in devices:
            try:
                new_d = Device(
                    id=d.id,
                    system_id=d.system_id,
                    zone_id=d.zone_id,
                    device_type=d.device_type,
                    model=d.model,
                    rated_power=d.rated_power,
                    serial_no=d.serial_no
                )
                postgres_session.add(new_d)
            except Exception as e:
                errors.append(f"Device {d.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ devices: {len(devices)} 条")
        total_migrated += len(devices)

        # 4.6 FileBlobs
        print("    [6/8] 迁移 file_blobs...")
        file_blobs = sqlite_session.query(FileBlob).all()
        for fb in file_blobs:
            try:
                new_fb = FileBlob(
                    id=fb.id,
                    storage_type=fb.storage_type,
                    bucket=fb.bucket,
                    path=fb.path,
                    file_name=fb.file_name,
                    content_type=fb.content_type,
                    size=fb.size,
                    hash=fb.hash
                )
                postgres_session.add(new_fb)
            except Exception as e:
                errors.append(f"FileBlob {fb.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ file_blobs: {len(file_blobs)} 条")
        total_migrated += len(file_blobs)

        # 4.7 Assets
        print("    [7/8] 迁移 assets...")
        assets = sqlite_session.query(Asset).all()
        for a in assets:
            try:
                new_a = Asset(
                    id=a.id,
                    project_id=a.project_id,
                    building_id=a.building_id,
                    zone_id=a.zone_id,
                    system_id=a.system_id,
                    device_id=a.device_id,
                    modality=a.modality,
                    source=a.source,
                    content_role=a.content_role,
                    title=a.title,
                    description=a.description,
                    file_id=a.file_id,
                    capture_time=a.capture_time,
                    location_meta=a.location_meta,
                    tags=a.tags,
                    quality_score=a.quality_score,
                    status=a.status
                )
                postgres_session.add(new_a)
            except Exception as e:
                errors.append(f"Asset {a.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ assets: {len(assets)} 条")
        total_migrated += len(assets)

        # 4.8 StructuredPayloads
        print("    [8/8] 迁移 asset_structured_payloads...")
        payloads = sqlite_session.query(AssetStructuredPayload).all()
        for sp in payloads:
            try:
                new_sp = AssetStructuredPayload(
                    id=sp.id,
                    asset_id=sp.asset_id,
                    schema_type=sp.schema_type,
                    payload=sp.payload,
                    version=sp.version,
                    created_by=sp.created_by,
                    created_at=sp.created_at
                )
                postgres_session.add(new_sp)
            except Exception as e:
                errors.append(f"StructuredPayload {sp.id}: {e}")
        postgres_session.commit()
        print(f"        ✓ structured_payloads: {len(payloads)} 条")
        total_migrated += len(payloads)

    except Exception as e:
        print(f"\n    ❌ 迁移过程中出错: {e}")
        postgres_session.rollback()
        sys.exit(1)

    # 5. 验证数据
    print("[5/6] 验证迁移结果...")

    # 统计 SQLite 数据
    sqlite_counts = {
        'projects': sqlite_session.query(Project).count(),
        'buildings': sqlite_session.query(Building).count(),
        'zones': sqlite_session.query(Zone).count(),
        'systems': sqlite_session.query(BuildingSystem).count(),
        'devices': sqlite_session.query(Device).count(),
        'file_blobs': sqlite_session.query(FileBlob).count(),
        'assets': sqlite_session.query(Asset).count(),
        'structured_payloads': sqlite_session.query(AssetStructuredPayload).count(),
    }

    # 统计 PostgreSQL 数据
    postgres_counts = {
        'projects': postgres_session.query(Project).count(),
        'buildings': postgres_session.query(Building).count(),
        'zones': postgres_session.query(Zone).count(),
        'systems': postgres_session.query(BuildingSystem).count(),
        'devices': postgres_session.query(Device).count(),
        'file_blobs': postgres_session.query(FileBlob).count(),
        'assets': postgres_session.query(Asset).count(),
        'structured_payloads': postgres_session.query(AssetStructuredPayload).count(),
    }

    print("\n    数据对比:")
    print(f"    {'表名':<25} {'SQLite':>10} {'PostgreSQL':>12} {'状态'}")
    print(f"    {'-'*25} {'-'*10} {'-'*12} {'-'*6}")

    all_match = True
    for table in sqlite_counts.keys():
        sqlite_count = sqlite_counts[table]
        postgres_count = postgres_counts[table]
        status = "✓" if sqlite_count == postgres_count else "✗"
        if sqlite_count != postgres_count:
            all_match = False
        print(f"    {table:<25} {sqlite_count:>10} {postgres_count:>12} {status}")

    print(f"\n    总计: {total_migrated} 条记录")

    if errors:
        print(f"\n    ⚠️  发现 {len(errors)} 个错误:")
        for error in errors[:5]:  # 只显示前 5 个
            print(f"      - {error}")
        if len(errors) > 5:
            print(f"      ... 还有 {len(errors) - 5} 个错误")

    if all_match:
        print("\n    ✅ 迁移成功！所有数据完全一致")
    else:
        print("\n    ⚠️  警告：部分数据数量不一致，请检查")

    # 6. 测试 UUID 查询（修复验证）
    print("[6/6] 测试 UUID 查询功能...")
    try:
        # 测试查询 Project
        test_project = postgres_session.query(Project).first()
        if test_project:
            print(f"    ✓ Project UUID 查询成功: {test_project.id}")

        # 测试查询 Asset
        test_asset = postgres_session.query(Asset).first()
        if test_asset:
            print(f"    ✓ Asset UUID 查询成功: {test_asset.id}")

            # 测试关联查询
            if test_asset.project_id:
                related_project = postgres_session.query(Project).filter(
                    Project.id == test_asset.project_id
                ).first()
                if related_project:
                    print(f"    ✓ 关联查询成功: Asset -> Project")

        print("    ✅ 所有 UUID 查询测试通过")
    except Exception as e:
        print(f"    ❌ UUID 查询测试失败: {e}")
        all_match = False

    # 7. 清理
    sqlite_session.close()
    postgres_session.close()

    print("\n" + "=" * 70)
    if all_match:
        print("✅ 迁移完成！")
    else:
        print("⚠️  迁移完成，但存在问题")
    print("=" * 70)

    print("\n下一步:")
    print("  1. 启动后端服务:")
    print("     cd services/backend")
    print("     python -m uvicorn app.main:app --host localhost --port 8000 --reload")
    print("")
    print("  2. 访问 Swagger 测试:")
    print("     http://localhost:8000/docs")
    print("")
    print("  3. 运行功能测试:")
    print("     python services/backend/test_multimodal_apis.py")
    print("")

    return 0 if all_match else 1


if __name__ == "__main__":
    try:
        exit_code = migrate()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
