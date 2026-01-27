"""
pytest 配置文件和共享 fixtures

为 BDC-AI 项目提供测试配置和通用测试工具
"""

import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import event
from sqlalchemy.engine import Engine

# 先导入所有模型以确保它们被注册
from shared.db import models_asset, models_project, models_auth
from shared.db.base import Base
from shared.db.models_asset import Asset, AssetStructuredPayload, FileBlob
from shared.db.models_project import Project
from shared.db.session import get_db
from services.backend.app.main import app


# ================================
# SQLite UUID/JSONB 类型兼容性处理
# ================================

class StringUUID(TypeDecorator):
    """SQLite 兼容的 UUID 类型（将 UUID 存储为 String）"""

    impl = String(36)
    cache_ok = True  # 允许缓存以提升性能

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(value)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite 连接配置"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ================================
# 数据库模型 UUID/JSONB 替换（仅用于测试）
# ================================

def _replace_postgresql_types_once():
    """
    临时替换所有模型中的 PostgreSQL 特定类型为 SQLite 兼容类型

    这是一个 monkey patch，在创建表之前将：
    - PostgreSQL UUID 类型替换为 StringUUID
    - PostgreSQL JSONB 类型替换为 JSON
    """
    models = [
        # Asset 模型
        models_asset.FileBlob,
        models_asset.Asset,
        models_asset.AssetStructuredPayload,
        models_asset.AssetFeature,
        # Project 模型
        models_project.Project,
        models_project.Building,
        models_project.Zone,
        models_project.BuildingSystem,
        models_project.Device,
        # Auth 模型
        models_auth.User,
        models_auth.Role,
        models_auth.Permission,
        models_auth.UserRole,
        models_auth.RolePermission,
        models_auth.ProjectMember,
        models_auth.AuditLog,
    ]

    for model in models:
        for column in model.__table__.columns:
            # 替换 UUID 类型
            if isinstance(column.type, UUID):
                column.type = StringUUID(36)
            # 替换 JSONB 类型
            elif isinstance(column.type, JSONB):
                column.type = JSON()


# ================================
# 测试数据库配置
# ================================

# 使用临时文件 SQLite 数据库进行测试（内存数据库在多个连接间不共享）
import tempfile
test_db_file = tempfile.mktemp(suffix=".db")
TEST_DATABASE_URL = f"sqlite:///{test_db_file}"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要此参数
    echo=False,  # 关闭 SQL 日志
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 在模块加载时立即替换类型并创建所有表
_replace_postgresql_types_once()
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    创建测试数据库会话

    每个测试使用独立的内存数据库，测试结束后自动回滚
    """
    # 创建所有表（类型已在模块加载时替换）
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """
    创建 FastAPI 测试客户端

    使用测试数据库会话覆盖依赖注入
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ================================
# 项目与空间 Fixtures
# ================================

@pytest.fixture
def test_project(db_session: Session) -> Project:
    """创建测试项目"""
    project = Project(
        name="LLM 管线测试项目",
        client="测试客户",
        location="测试地点",
        type="commercial",
        status="active",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


# ================================
# 测试数据 Fixtures
# ================================

@pytest.fixture
def test_image_files():
    """
    测试图片文件路径字典

    返回三种测试图片的路径：
    - scene_issue: 场景问题图片
    - nameplate: 设备铭牌图片
    - meter: 仪表读数图片
    """
    test_dir = Path(__file__).parent / "changsha-表具"

    if not test_dir.exists():
        pytest.skip(f"测试图片目录不存在: {test_dir}")

    files = {
        "scene_issue": test_dir / "scene_issue.jpg",
        "nameplate": test_dir / "nameplate.jpg",
        "meter": test_dir / "meter.jpg"
    }

    # 验证所有文件存在
    for name, path in files.items():
        if not path.exists():
            pytest.skip(f"测试图片不存在: {path}")

    return files


@pytest.fixture
def mock_llm_responses() -> Dict[str, Dict[str, Any]]:
    """
    模拟 LLM 响应数据

    为三种 content_role 类型提供模拟的 LLM 分析结果
    """
    return {
        "scene_issue": {
            "title": "管道保温层破损",
            "issue_category": "设备维护",
            "severity": "medium",
            "summary": "冷冻水管道保温层有明显破损，存在结露风险",
            "suspected_causes": ["保温材料老化", "外力损伤"],
            "recommended_actions": ["更换破损保温层", "检查周边管道"],
            "confidence": 0.85,
            "tags": ["保温", "管道", "冷冻水"]
        },
        "nameplate": {
            "equipment_type": "离心式冷水机组",
            "fields": [
                {
                    "key": "model",
                    "label": "型号",
                    "value": "YCWE-1234",
                    "unit": None,
                    "confidence": 0.95
                },
                {
                    "key": "power_kw",
                    "label": "额定功率",
                    "value": 1200,
                    "unit": "kW",
                    "confidence": 0.90
                },
                {
                    "key": "refrigerant",
                    "label": "制冷剂",
                    "value": "R134a",
                    "unit": None,
                    "confidence": 0.92
                }
            ]
        },
        "meter": {
            "pre_reading": 65.0,
            "reading": 64.8,
            "unit": "℃",
            "status": "confirmed_from_image",
            "summary": "图片清晰可见，读数为 64.8℃，与预读数 65.0℃ 接近",
            "confidence": 0.90,
            "tags": ["温度表", "水温"]
        }
    }


@pytest.fixture
def sample_route_decision_payload() -> Dict[str, Any]:
    """
    模拟路由决策 payload

    用于验证路由决策生成的数据结构
    """
    return {
        "route": "scene_llm_pipeline",
        "reason": "content_role is not meter/nameplate; delegate to scene understanding pipeline",
        "content_role": "scene_issue"
    }


# ================================
# 辅助函数
# ================================

def create_test_asset_from_file(
    db: Session,
    project_id: uuid.UUID,
    file_path: Path,
    content_role: Optional[str] = None,
    meter_pre_reading: Optional[float] = None,
) -> Asset:
    """
    从文件创建测试 Asset 的辅助函数

    Args:
        db: 数据库会话
        project_id: 项目 ID
        file_path: 图片文件路径
        content_role: 内容角色（scene_issue, nameplate, meter 等）
        meter_pre_reading: 仪表预读数（仅用于 meter 类型）

    Returns:
        创建的 Asset 实例
    """
    from shared.config.settings import get_settings
    from datetime import datetime

    settings = get_settings()

    # 读取文件
    if not file_path.exists():
        raise FileNotFoundError(f"测试文件不存在: {file_path}")

    with open(file_path, "rb") as f:
        content = f.read()

    file_ext = file_path.suffix
    file_name = f"{uuid.uuid4()}{file_ext}"

    # 创建存储目录
    rel_path = str(project_id) + "/" + file_name
    abs_dir = os.path.join(settings.local_storage_dir, str(project_id))
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, file_name)

    # 写入文件
    with open(abs_path, "wb") as f:
        f.write(content)

    size = os.path.getsize(abs_path)

    # 创建 FileBlob
    file_blob = FileBlob(
        storage_type="local",
        bucket="assets",
        path=rel_path,
        file_name=file_path.name,
        content_type=f"image/{file_ext[1:]}",
        size=float(size),
    )
    db.add(file_blob)
    db.flush()

    # 创建 location_meta（如果需要）
    location_meta = None
    if meter_pre_reading is not None and (content_role or "").lower() == "meter":
        location_meta = {"meter_pre_reading": float(meter_pre_reading)}

    # 创建 Asset
    asset = Asset(
        project_id=project_id,
        modality="image",
        source="test",
        content_role=content_role,
        title=file_path.name,
        file_id=file_blob.id,
        capture_time=datetime.utcnow(),
        location_meta=location_meta,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


def upload_image_via_api(
    client: TestClient,
    project_id: str,
    file_path: Path,
    content_role: Optional[str] = None,
    meter_pre_reading: Optional[float] = None,
    auto_route: bool = False,
    note: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    通过 API 上传图片的辅助函数

    Args:
        client: FastAPI 测试客户端
        project_id: 项目 ID（字符串格式）
        file_path: 图片文件路径
        content_role: 内容角色
        meter_pre_reading: 仪表预读数
        auto_route: 是否自动路由
        note: 备注信息
        title: 标题

    Returns:
        API 响应 JSON 数据
    """
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "image/jpeg")}

        params = {
            "project_id": project_id,
            "source": "test",
        }

        if content_role:
            params["content_role"] = content_role
        if meter_pre_reading is not None:
            params["meter_pre_reading"] = meter_pre_reading
        if auto_route:
            params["auto_route"] = "true"  # Query 参数需要字符串

        data = {}
        if note:
            data["note"] = note
        if title:
            data["title"] = title

        response = client.post(
            "/api/v1/assets/upload_image_with_note",
            params=params,
            files=files,
            data=data,
        )

    return response


# ================================
# Pytest 配置
# ================================

def pytest_configure(config):
    """Pytest 初始化配置"""
    config.addinivalue_line(
        "markers",
        "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers",
        "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers",
        "api: API 测试标记"
    )
