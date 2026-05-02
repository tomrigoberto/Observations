from fastapi import APIRouter, HTTPException

from app import schemas
from app.engine import loader

router = APIRouter(prefix="/library", tags=["library"])


@router.get("", response_model=list[schemas.LibraryObservationSummary])
def list_observations(
    category: str | None = None,
    severity: str | None = None,
    confidence: str | None = None,
    q: str | None = None,
):
    pack = loader.get_rule_pack()
    items = []
    for obs in pack.observations.values():
        if category and obs["category"] != category:
            continue
        if severity and obs["severity"] != severity:
            continue
        if confidence and obs["confidence"] != confidence:
            continue
        if q and q.lower() not in obs["title"].lower() and q.lower() not in obs["id"].lower():
            continue
        items.append(
            schemas.LibraryObservationSummary(
                id=obs["id"],
                title=obs["title"],
                category=obs["category"],
                subcategory=obs["subcategory"],
                severity=obs["severity"],
                confidence=obs["confidence"],
                status=obs["status"],
                version=obs["version"],
                audience_tags=obs.get("audience_tags", []),
            )
        )
    return sorted(items, key=lambda i: (i.category, i.subcategory, i.id))


@router.get("/{obs_id}", response_model=schemas.LibraryObservationDetail)
def get_observation(obs_id: str):
    pack = loader.get_rule_pack()
    obs = pack.observations.get(obs_id)
    if not obs:
        raise HTTPException(404, "observation not found")
    return schemas.LibraryObservationDetail(
        id=obs["id"],
        title=obs["title"],
        category=obs["category"],
        subcategory=obs["subcategory"],
        severity=obs["severity"],
        confidence=obs["confidence"],
        status=obs["status"],
        version=obs["version"],
        audience_tags=obs.get("audience_tags", []),
        statement=obs["statement"],
        discussion_points=obs.get("discussion_points", []),
        plain_english_logic=loader.render_plain_english_logic(obs, pack.patterns),
        required_inputs=obs.get("required_inputs", {}),
        sources=obs.get("sources", []),
        caveats=obs.get("caveats"),
        disclaimers=obs.get("disclaimers", []),
        test_cases=obs.get("test_cases", []),
        metadata=obs.get("metadata", {}),
    )


@router.get("/_meta/info")
def rule_pack_info():
    pack = loader.get_rule_pack()
    by_cat: dict = {}
    for o in pack.observations.values():
        by_cat[o["category"]] = by_cat.get(o["category"], 0) + 1
    return {
        "version": pack.version,
        "observation_count": len(pack.observations),
        "pattern_count": len(pack.patterns),
        "by_category": by_cat,
        "library_path": pack.path,
    }
