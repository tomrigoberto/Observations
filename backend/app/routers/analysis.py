from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.engine.runner import run_analysis

router = APIRouter(prefix="/clients/{client_id}/analysis", tags=["analysis"])


@router.post("", response_model=schemas.AnalysisRunOut)
def trigger_analysis(client_id: UUID, db: Session = Depends(get_db)):
    if not db.get(models.Client, client_id):
        raise HTTPException(404, "client not found")
    run = run_analysis(db, client_id)
    return run


@router.get("", response_model=list[schemas.AnalysisRunOut])
def list_runs(client_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(models.AnalysisRun)
        .filter(models.AnalysisRun.client_id == client_id)
        .order_by(models.AnalysisRun.started_at.desc())
        .all()
    )


@router.get("/{run_id}", response_model=schemas.AnalysisRunOut)
def get_run(client_id: UUID, run_id: UUID, db: Session = Depends(get_db)):
    run = db.get(models.AnalysisRun, run_id)
    if not run or run.client_id != client_id:
        raise HTTPException(404, "run not found")
    return run


@router.get("/{run_id}/results", response_model=list[schemas.ObservationResultOut])
def list_results(
    client_id: UUID,
    run_id: UUID,
    severity: str | None = None,
    confidence: str | None = None,
    category: str | None = None,
    include_dismissed: bool = False,
    db: Session = Depends(get_db),
):
    run = db.get(models.AnalysisRun, run_id)
    if not run or run.client_id != client_id:
        raise HTTPException(404, "run not found")
    q = db.query(models.ObservationResult).filter(
        models.ObservationResult.run_id == run_id,
        models.ObservationResult.fired.is_(True),
        models.ObservationResult.suppressed.is_(False),
    )
    if severity:
        q = q.filter(models.ObservationResult.severity == severity)
    if confidence:
        q = q.filter(models.ObservationResult.confidence == confidence)
    if category:
        q = q.filter(models.ObservationResult.category == category)
    if not include_dismissed:
        q = q.filter(models.ObservationResult.dismissed.is_(False))
    return q.order_by(
        models.ObservationResult.severity.desc(),
        models.ObservationResult.confidence.desc(),
    ).all()


@router.post("/{run_id}/results/{result_id}/dismiss")
def dismiss(
    client_id: UUID,
    run_id: UUID,
    result_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
):
    r = db.get(models.ObservationResult, result_id)
    if not r or r.run_id != run_id:
        raise HTTPException(404, "result not found")
    r.dismissed = True
    r.dismissal_reason = reason
    db.commit()
    return {"ok": True}


@router.post("/{run_id}/results/{result_id}/pin")
def pin(client_id: UUID, run_id: UUID, result_id: UUID, db: Session = Depends(get_db)):
    r = db.get(models.ObservationResult, result_id)
    if not r or r.run_id != run_id:
        raise HTTPException(404, "result not found")
    if r.confidence == "speculative":
        raise HTTPException(400, "speculative observations cannot be pinned to summary")
    r.pinned_to_summary = not r.pinned_to_summary
    db.commit()
    return {"pinned": r.pinned_to_summary}
