import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.db import get_db
from app.parsers import parse_transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("", response_model=schemas.TranscriptOut)
async def upload_transcript(
    client_id: UUID = Form(...),
    member_id: UUID | None = Form(None),
    entity_id: UUID | None = Form(None),
    transcript_type: str = Form(...),
    tax_year: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not db.get(models.Client, client_id):
        raise HTTPException(404, "client not found")

    upload_dir = Path(settings.upload_path) / str(client_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid4().hex}_{file.filename}"
    saved_path = upload_dir / saved_name
    with saved_path.open("wb") as f:
        f.write(await file.read())

    transcript = models.Transcript(
        client_id=client_id,
        member_id=member_id,
        entity_id=entity_id,
        transcript_type=transcript_type,
        tax_year=tax_year,
        source_filename=file.filename or saved_name,
        raw_html_path=str(saved_path),
        parse_status="pending",
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    try:
        with saved_path.open("r", encoding="utf-8", errors="replace") as f:
            html = f.read()
        transcript.parsed_data = parse_transcript(transcript_type, html)
        transcript.parse_status = "parsed"
    except Exception as exc:  # noqa: BLE001
        transcript.parse_status = "failed"
        transcript.parse_error = str(exc)
    db.commit()
    db.refresh(transcript)
    return transcript


@router.get("/{transcript_id}", response_model=schemas.TranscriptOut)
def get_transcript(transcript_id: UUID, db: Session = Depends(get_db)):
    t = db.get(models.Transcript, transcript_id)
    if not t:
        raise HTTPException(404, "transcript not found")
    return t


@router.get("/{transcript_id}/raw")
def get_raw(transcript_id: UUID, db: Session = Depends(get_db)):
    t = db.get(models.Transcript, transcript_id)
    if not t or not os.path.exists(t.raw_html_path):
        raise HTTPException(404, "transcript file missing")
    return FileResponse(t.raw_html_path, media_type="text/html")


@router.get("/{transcript_id}/parsed")
def get_parsed(transcript_id: UUID, db: Session = Depends(get_db)):
    t = db.get(models.Transcript, transcript_id)
    if not t:
        raise HTTPException(404, "transcript not found")
    return {"transcript_id": str(t.id), "parsed_data": t.parsed_data, "status": t.parse_status}
