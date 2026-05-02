from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.engine import loader
from app.engine.runner import run_analysis
from app.pdf.render import render_detail_report, render_exec_summary

router = APIRouter(prefix="/clients/{client_id}/analysis", tags=["analysis"])

_SEVERITY_ORDER = ["urgent", "risk", "opportunity", "informational"]
_SEV_INDEX = {s: i for i, s in enumerate(_SEVERITY_ORDER)}


@router.post("", response_model=schemas.AnalysisRunOut)
def trigger_analysis(client_id: UUID, db: Session = Depends(get_db)):
    if not db.get(models.Client, client_id):
        raise HTTPException(404, "client not found")
    return run_analysis(db, client_id)


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


@router.get("/{run_id}/pdf")
def get_pdf(
    client_id: UUID,
    run_id: UUID,
    type: str = "summary",
    db: Session = Depends(get_db),
):
    run = db.get(models.AnalysisRun, run_id)
    if not run or run.client_id != client_id:
        raise HTTPException(404, "run not found")
    if type not in ("summary", "detail"):
        raise HTTPException(400, "type must be 'summary' or 'detail'")

    client = db.get(models.Client, client_id)
    results = (
        db.query(models.ObservationResult)
        .filter(
            models.ObservationResult.run_id == run_id,
            models.ObservationResult.fired.is_(True),
            models.ObservationResult.suppressed.is_(False),
            models.ObservationResult.dismissed.is_(False),
        )
        .all()
    )
    transcripts = (
        db.query(models.Transcript).filter(models.Transcript.client_id == client_id).all()
    )
    members = db.query(models.Member).filter(models.Member.client_id == client_id).all()
    entities = db.query(models.Entity).filter(models.Entity.client_id == client_id).all()
    member_map = {str(m.id): m.display_name for m in members}
    entity_map = {str(e.id): e.name for e in entities}

    pack = loader.get_rule_pack()
    disclaimer_ids: set[str] = set()
    for r in results:
        for d in r.disclaimers or []:
            disclaimer_ids.add(d)
    disclaimers = [
        {"id": d, "text": (pack.disclaimers.get(d, {}) or {}).get("text", "").strip()}
        for d in sorted(disclaimer_ids)
    ]

    base_ctx = {
        "client": {"name": client.name},
        "coverage": run.coverage or {"label": ""},
        "rule_pack_version": run.rule_pack_version,
        "generated_at": (run.completed_at or run.started_at).isoformat(),
        "disclaimers": disclaimers,
    }

    if type == "summary":
        eligible = [
            r for r in results if r.confidence != "speculative" or r.pinned_to_summary
        ]
        eligible.sort(
            key=lambda r: (_SEV_INDEX.get(r.severity, 99), 0 if r.pinned_to_summary else 1)
        )
        by_severity = [
            (sev.title(), [r for r in eligible if r.severity == sev])
            for sev in _SEVERITY_ORDER
        ]
        pdf = render_exec_summary({**base_ctx, "by_severity": by_severity})
        filename = f"exec-summary-{_slug(client.name)}.pdf"
    else:
        by_cat: dict[str, list] = {}
        for r in results:
            by_cat.setdefault(r.category, []).append(r)
        for k in by_cat:
            by_cat[k].sort(key=lambda r: _SEV_INDEX.get(r.severity, 99))
        transcripts_ctx = [
            {
                "transcript_type": t.transcript_type,
                "tax_year": t.tax_year,
                "member_or_entity_name": (
                    member_map.get(str(t.member_id))
                    or entity_map.get(str(t.entity_id))
                    or "—"
                ),
                "parse_status": t.parse_status,
            }
            for t in transcripts
        ]
        pdf = render_detail_report(
            {
                **base_ctx,
                "transcripts": transcripts_ctx,
                "by_category": list(by_cat.items()),
            }
        )
        filename = f"detail-report-{_slug(client.name)}.pdf"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name).strip("_") or "client"
