"""Run analysis: take a client's transcripts, evaluate the rule pack, persist results."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app import models
from app.engine import loader
from app.engine.patterns import get as get_pattern
from app.engine.templating import render

log = logging.getLogger(__name__)

ROLE_HIERARCHY = {"primary_taxpayer": 0, "spouse": 1}


def run_analysis(db: Session, client_id: UUID) -> models.AnalysisRun:
    pack = loader.get_rule_pack()
    members = (
        db.query(models.Member).filter(models.Member.client_id == client_id).all()
    )
    entities = (
        db.query(models.Entity).filter(models.Entity.client_id == client_id).all()
    )
    transcripts = (
        db.query(models.Transcript)
        .filter(
            models.Transcript.client_id == client_id,
            models.Transcript.parse_status == "parsed",
        )
        .all()
    )

    household = _build_household(client_id, members, entities, transcripts)
    coverage = _coverage(transcripts)

    run = models.AnalysisRun(
        client_id=client_id,
        rule_pack_version=pack.version,
        status="running",
        coverage=coverage,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    fired_results: list[models.ObservationResult] = []
    for obs in pack.observations.values():
        if obs.get("status") not in ("active", "deprecated"):
            continue
        if not _inputs_satisfied(obs, household):
            continue
        for member in _members_in_scope(obs, household):
            fired, captures = _eval_logic(obs["logic"], member, household)
            if not fired:
                continue
            ctx = {"member": member, **captures}
            result = models.ObservationResult(
                run_id=run.id,
                observation_id=obs["id"],
                observation_version=obs["version"],
                title=obs["title"],
                category=obs["category"],
                subcategory=obs["subcategory"],
                severity=obs["severity"],
                confidence=obs["confidence"],
                member_id=UUID(member["id"]) if _looks_like_uuid(member["id"]) else None,
                fired=True,
                captured_vars=captures,
                statement_rendered=render(obs["statement"], ctx).strip(),
                discussion_points=[render(p, ctx) for p in obs.get("discussion_points", [])],
                sources_rendered=[
                    {
                        **{k: render(str(v), ctx) for k, v in s.items()},
                    }
                    for s in obs.get("sources", [])
                ],
                caveats=obs.get("caveats"),
                disclaimers=obs.get("disclaimers", []),
            )
            db.add(result)
            fired_results.append(result)
    db.commit()

    _apply_suppression(db, fired_results, pack)

    run.completed_at = datetime.utcnow()
    run.status = "complete"
    db.commit()
    db.refresh(run)
    return run


def _build_household(client_id, members, entities, transcripts) -> dict:
    return {
        "household_id": str(client_id),
        "members": [
            {
                "id": str(m.id),
                "role": m.role,
                "display_name": m.display_name,
                "birth_year": m.birth_year,
                "deceased_date": m.deceased_date.isoformat() if m.deceased_date else None,
            }
            for m in members
        ],
        "entities": [
            {"id": str(e.id), "type": e.entity_type, "name": e.name} for e in entities
        ],
        "transcripts": [
            {
                "member_id": str(t.member_id) if t.member_id else None,
                "entity_id": str(t.entity_id) if t.entity_id else None,
                "transcript_type": t.transcript_type,
                "tax_year": t.tax_year,
                "data": t.parsed_data or {},
            }
            for t in transcripts
        ],
    }


def _coverage(transcripts) -> dict:
    if not transcripts:
        return {"tax_years": [], "label": "No transcripts"}
    years = sorted({t.tax_year for t in transcripts})
    return {
        "tax_years": years,
        "transcript_counts": _counts(transcripts),
        "label": f"Analysis covers tax years {years[0]}–{years[-1]}",
    }


def _counts(transcripts) -> dict:
    out: dict = {}
    for t in transcripts:
        out[t.transcript_type] = out.get(t.transcript_type, 0) + 1
    return out


def _inputs_satisfied(obs: dict, household: dict) -> bool:
    req = obs.get("required_inputs", {})
    needed_types = set(req.get("transcript_types", []))
    if needed_types:
        present_types = {t["transcript_type"] for t in household["transcripts"]}
        if not needed_types.issubset(present_types):
            return False
    min_years = req.get("min_tax_years", 0)
    if min_years and len({t["tax_year"] for t in household["transcripts"]}) < min_years:
        return False
    return True


def _members_in_scope(obs: dict, household: dict):
    scope = set(obs.get("applies_to", []))
    for m in household["members"]:
        if m["role"] in scope:
            yield m
    if {"business_entity", "trust", "estate"} & scope:
        for e in household["entities"]:
            if e["type"] in scope:
                yield {
                    "id": e["id"],
                    "role": e["type"],
                    "display_name": e["name"],
                    "birth_year": None,
                }


def _eval_logic(node: dict, member: dict, household: dict) -> tuple[bool, dict]:
    if "pattern" in node:
        pat = get_pattern(node["pattern"])
        if not pat:
            log.warning("unknown pattern: %s", node["pattern"])
            return False, {}
        result = pat.evaluate(member, household, node.get("parameters", {}))
        if not result.fired:
            return False, {}
        # apply per-pattern capture rename
        rename = node.get("capture", {})
        captures = {k: result.captures.get(v) for k, v in rename.items()}
        # also expose raw captures so subsequent patterns can reference
        captures = {**result.captures, **captures}
        return True, captures
    if "all_of" in node:
        merged: dict = {}
        for child in node["all_of"]:
            ok, caps = _eval_logic(child, member, household)
            if not ok:
                return False, {}
            merged.update(caps)
        return True, merged
    if "any_of" in node:
        for child in node["any_of"]:
            ok, caps = _eval_logic(child, member, household)
            if ok:
                return True, caps
        return False, {}
    if "none_of" in node:
        for child in node["none_of"]:
            ok, _ = _eval_logic(child, member, household)
            if ok:
                return False, {}
        return True, {}
    if "not" in node:
        ok, _ = _eval_logic(node["not"], member, household)
        return (not ok), {}
    return False, {}


def _apply_suppression(db: Session, results: list[models.ObservationResult], pack):
    """For each fired result, check whether its observation is suppressed_by any other fired observation."""
    fired_ids = {r.observation_id for r in results}
    for r in results:
        obs = pack.observations.get(r.observation_id)
        if not obs:
            continue
        sup_ids = set(obs.get("suppressed_by", []))
        if sup_ids & fired_ids:
            r.suppressed = True
            r.suppressed_by_id = next(iter(sup_ids & fired_ids))
    db.commit()


def _looks_like_uuid(s: str) -> bool:
    try:
        UUID(s)
        return True
    except (ValueError, AttributeError):
        return False
