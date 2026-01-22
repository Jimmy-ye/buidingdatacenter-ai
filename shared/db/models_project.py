import uuid
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    client = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    type = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    tags = Column(JSONB, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(100), nullable=True)
    deletion_reason = Column(String(500), nullable=True)

    buildings = relationship("Building", back_populates="project", cascade="all, delete-orphan")


class Building(Base):
    __tablename__ = "buildings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    usage_type = Column(String(100), nullable=True)
    floor_area = Column(Float, nullable=True)
    gfa_area = Column(Float, nullable=True)
    year_built = Column(Float, nullable=True)
    tags = Column(JSONB, nullable=True)

    project = relationship("Project", back_populates="buildings")
    zones = relationship("Zone", back_populates="building", cascade="all, delete-orphan")
    systems = relationship("BuildingSystem", back_populates="building", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=True)
    geometry_ref = Column(String(500), nullable=True)
    tags = Column(JSONB, nullable=True)

    building = relationship("Building", back_populates="zones")
    devices = relationship("Device", back_populates="zone", cascade="all, delete-orphan")


class BuildingSystem(Base):
    __tablename__ = "systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(100), nullable=False)
    name = Column(String(200), nullable=True)
    description = Column(String(500), nullable=True)
    tags = Column(JSONB, nullable=True)

    building = relationship("Building", back_populates="systems")
    devices = relationship("Device", back_populates="system", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id = Column(UUID(as_uuid=True), ForeignKey("systems.id", ondelete="SET NULL"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    device_type = Column(String(100), nullable=True)
    model = Column(String(200), nullable=True)
    rated_power = Column(Float, nullable=True)
    serial_no = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)

    system = relationship("BuildingSystem", back_populates="devices")
    zone = relationship("Zone", back_populates="devices")
