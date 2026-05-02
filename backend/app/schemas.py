from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ClientOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    role: str
    display_name: str
    birth_year: int | None = None
    deceased_date: date | None = None


class MemberOut(MemberCreate):
    id: UUID

    class Config:
        from_attributes = True


class EntityCreate(BaseModel):
    entity_type: str
    name: str
    ein: str | None = None


class EntityOut(EntityCreate):
    id: UUID

    class Config:
        from_attributes = True


class TranscriptOut(BaseModel):
    id: UUID
    member_id: UUID | None
    entity_id: UUID | None
    transcript_type: str
    tax_year: int
    source_filename: str
    parse_status: str
    parse_error: str | None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class AnalysisRunOut(BaseModel):
    id: UUID
    rule_pack_version: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    coverage: dict | None

    class Config:
        from_attributes = True


class ObservationResultOut(BaseModel):
    id: UUID
    observation_id: str
    observation_version: str
    title: str
    category: str
    subcategory: str
    severity: str
    confidence: str
    member_id: UUID | None
    fired: bool
    captured_vars: dict
    statement_rendered: str
    discussion_points: list
    sources_rendered: list
    caveats: str | None
    disclaimers: list
    suppressed: bool
    dismissed: bool
    pinned_to_summary: bool

    class Config:
        from_attributes = True


class LibraryObservationSummary(BaseModel):
    id: str
    title: str
    category: str
    subcategory: str
    severity: str
    confidence: str
    status: str
    version: str
    audience_tags: list[str] = []


class LibraryObservationDetail(LibraryObservationSummary):
    statement: str
    discussion_points: list[str]
    plain_english_logic: str
    required_inputs: dict
    sources: list[dict]
    caveats: str | None
    disclaimers: list[str]
    test_cases: list[dict]
    metadata: dict
