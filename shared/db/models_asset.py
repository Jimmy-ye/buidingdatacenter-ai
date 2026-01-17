import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class FileBlob(Base):
    __tablename__ = "file_blobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_type = Column(String(50), nullable=False)
    bucket = Column(String(200), nullable=False)
    path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size = Column(Float, nullable=True)
    hash = Column(String(128), nullable=True)

    asset = relationship("Asset", back_populates="file_blob", uselist=False)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.id"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)
    system_id = Column(UUID(as_uuid=True), ForeignKey("systems.id"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)

    modality = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)

    file_id = Column(UUID(as_uuid=True), ForeignKey("file_blobs.id"), nullable=False)
    structured_payload_id = Column(
        UUID(as_uuid=True), ForeignKey("asset_structured_payloads.id"), nullable=True
    )

    capture_time = Column(DateTime, default=datetime.utcnow, nullable=True)
    location_meta = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    quality_score = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)

    file_blob = relationship("FileBlob", back_populates="asset")
    structured_payload = relationship("AssetStructuredPayload", back_populates="asset")
    features = relationship("AssetFeature", back_populates="asset", cascade="all, delete-orphan")


class AssetStructuredPayload(Base):
    __tablename__ = "asset_structured_payloads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    schema_type = Column(String(50), nullable=False)
    payload = Column(JSONB, nullable=False)
    version = Column(Float, nullable=False, default=1)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    asset = relationship("Asset", back_populates="structured_payload")


class AssetFeature(Base):
    __tablename__ = "asset_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    feature_type = Column(String(50), nullable=False)
    vector = Column(JSONB, nullable=False)
    metadata = Column(JSONB, nullable=True)

    asset = relationship("Asset", back_populates="features")
