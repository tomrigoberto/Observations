from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    client = models.Client(name=payload.name)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[schemas.ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).order_by(models.Client.created_at.desc()).all()


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: UUID, db: Session = Depends(get_db)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(404, "client not found")
    return client


@router.post("/{client_id}/members", response_model=schemas.MemberOut)
def add_member(client_id: UUID, payload: schemas.MemberCreate, db: Session = Depends(get_db)):
    if not db.get(models.Client, client_id):
        raise HTTPException(404, "client not found")
    member = models.Member(client_id=client_id, **payload.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/{client_id}/members", response_model=list[schemas.MemberOut])
def list_members(client_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.Member).filter(models.Member.client_id == client_id).all()


@router.post("/{client_id}/entities", response_model=schemas.EntityOut)
def add_entity(client_id: UUID, payload: schemas.EntityCreate, db: Session = Depends(get_db)):
    if not db.get(models.Client, client_id):
        raise HTTPException(404, "client not found")
    entity = models.Entity(client_id=client_id, **payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get("/{client_id}/entities", response_model=list[schemas.EntityOut])
def list_entities(client_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.Entity).filter(models.Entity.client_id == client_id).all()


@router.get("/{client_id}/coverage")
def coverage(client_id: UUID, db: Session = Depends(get_db)):
    """Per member/entity x tax_year x transcript_type matrix of parse status."""
    if not db.get(models.Client, client_id):
        raise HTTPException(404, "client not found")
    transcripts = (
        db.query(models.Transcript).filter(models.Transcript.client_id == client_id).all()
    )
    matrix: dict = {}
    for t in transcripts:
        owner = str(t.member_id or t.entity_id)
        matrix.setdefault(owner, {}).setdefault(t.tax_year, {})[t.transcript_type] = {
            "id": str(t.id),
            "parse_status": t.parse_status,
        }
    years = sorted({t.tax_year for t in transcripts})
    return {
        "matrix": matrix,
        "tax_years": years,
        "coverage_label": (
            f"Analysis covers tax years {years[0]}–{years[-1]}" if years else "No transcripts"
        ),
    }
