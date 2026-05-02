from __future__ import annotations

import uuid
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["Member"]] = relationship(back_populates="client", cascade="all,delete")
    entities: Mapped[list["Entity"]] = relationship(back_populates="client", cascade="all,delete")
    transcripts: Mapped[list["Transcript"]] = relationship(
        back_populates="client", cascade="all,delete"
    )
    runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="client", cascade="all,delete"
    )


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    deceased_date: Mapped[date | None] = mapped_column(Date)

    client: Mapped[Client] = relationship(back_populates="members")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)  # business|trust|estate
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ein: Mapped[str | None] = mapped_column(String(20))

    client: Mapped[Client] = relationship(back_populates="entities")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL")
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL")
    )
    transcript_type: Mapped[str] = mapped_column(String(40), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    source_filename: Mapped[str] = mapped_column(String(400), nullable=False)
    raw_html_path: Mapped[str] = mapped_column(String(400), nullable=False)
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")
    parse_error: Mapped[str | None] = mapped_column(Text)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client] = relationship(back_populates="transcripts")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    rule_pack_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    coverage: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)

    client: Mapped[Client] = relationship(back_populates="runs")
    results: Mapped[list["ObservationResult"]] = relationship(
        back_populates="run", cascade="all,delete"
    )


class ObservationResult(Base):
    __tablename__ = "observation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True
    )
    observation_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    observation_version: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL")
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL")
    )
    fired: Mapped[bool] = mapped_column(Boolean, default=True)
    captured_vars: Mapped[dict] = mapped_column(JSONB, default=dict)
    statement_rendered: Mapped[str] = mapped_column(Text, nullable=False)
    discussion_points: Mapped[list] = mapped_column(JSONB, default=list)
    sources_rendered: Mapped[list] = mapped_column(JSONB, default=list)
    caveats: Mapped[str | None] = mapped_column(Text)
    disclaimers: Mapped[list] = mapped_column(JSONB, default=list)
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    suppressed_by_id: Mapped[str | None] = mapped_column(String(40))
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissal_reason: Mapped[str | None] = mapped_column(Text)
    advisor_annotation: Mapped[str | None] = mapped_column(Text)
    pinned_to_summary: Mapped[bool] = mapped_column(Boolean, default=False)

    run: Mapped[AnalysisRun] = relationship(back_populates="results")
