"""
SQLAlchemy models for GESN normative catalog.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base


class GESNSection(Base):
    """
    Hierarchical structure of GESN catalog (chapters, sections, subsections).
    """

    __tablename__ = "gesn_sections"
    __table_args__ = (UniqueConstraint("code", name="uq_gesn_sections_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gesn_sections.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, str]]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    parent: Mapped[Optional["GESNSection"]] = relationship(
        "GESNSection", remote_side=[id], backref="children", lazy="selectin"
    )
    norms: Mapped[List["GESNNorm"]] = relationship("GESNNorm", back_populates="section", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GESNSection code={self.code} name={self.name!r}>"


class GESNNorm(Base):
    """
    Main normative item describing a unit of work.
    """

    __tablename__ = "gesn_norms"
    __table_args__ = (UniqueConstraint("code", name="uq_gesn_norms_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("gesn_sections.id"), nullable=False, index=True)

    code: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    composition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[Optional[Dict[str, object]]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    section: Mapped[GESNSection] = relationship("GESNSection", back_populates="norms", lazy="joined")
    resources: Mapped[List["GESNNormResource"]] = relationship(
        "GESNNormResource", back_populates="norm", cascade="all, delete-orphan"
    )
    components: Mapped[List["GESNNormComponent"]] = relationship(
        "GESNNormComponent", back_populates="norm", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GESNNorm code={self.code} unit={self.unit} name={self.name!r}>"


class GESNNormComponent(Base):
    """
    Detailed composition (operations) belonging to a norm.
    """

    __tablename__ = "gesn_norm_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    norm_id: Mapped[int] = mapped_column(Integer, ForeignKey("gesn_norms.id"), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    metadata_json: Mapped[Optional[Dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)

    norm: Mapped[GESNNorm] = relationship("GESNNorm", back_populates="components")


class GESNNormResource(Base):
    """
    Resources (materials, labor, machines) associated with a norm.
    """

    __tablename__ = "gesn_norm_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    norm_id: Mapped[int] = mapped_column(Integer, ForeignKey("gesn_norms.id"), nullable=False, index=True)

    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)  # material / labor / machine
    code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(nullable=True)
    metadata_json: Mapped[Optional[Dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)

    norm: Mapped[GESNNorm] = relationship("GESNNorm", back_populates="resources")


