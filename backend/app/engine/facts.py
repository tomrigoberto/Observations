"""Canonical fact accessors over a parsed household.

A "household" passed to the engine is a plain dict shaped like our fixtures:

{
  "household_id": str,
  "members": [{id, role, display_name, birth_year?, deceased_date?}, ...],
  "entities": [...],
  "transcripts": [
    {member_id|entity_id, transcript_type, tax_year, data: {...}},
    ...
  ]
}
"""

from __future__ import annotations


def _transcripts_for(member, household, transcript_type: str | None = None) -> list[dict]:
    member_id = member["id"] if isinstance(member, dict) else member.id
    out = [t for t in household["transcripts"] if t.get("member_id") == member_id]
    if transcript_type:
        out = [t for t in out if t["transcript_type"] == transcript_type]
    return out


def filing_status_by_year(member, household) -> list[dict]:
    rows = []
    for t in _transcripts_for(member, household, "account_transcript"):
        status = t.get("data", {}).get("header", {}).get("filing_status")
        year = t.get("tax_year") or t.get("data", {}).get("header", {}).get("tax_year")
        if status and year:
            rows.append({"tax_year": int(year), "status": status})
    rows.sort(key=lambda r: r["tax_year"])
    return rows


def tc_events(member, household, code: int | None = None, year: int | None = None) -> list[dict]:
    out = []
    for t in _transcripts_for(member, household, "account_transcript"):
        for e in t.get("data", {}).get("tc_events", []):
            if code is not None and e.get("code") != code:
                continue
            ev_year = e.get("tax_year") or t.get("tax_year")
            if year is not None and ev_year != year:
                continue
            # ensure tax_year is populated for downstream consumers
            if e.get("tax_year") is None and t.get("tax_year") is not None:
                e = {**e, "tax_year": t["tax_year"]}
            out.append(e)
    return out


def forms(
    member,
    household,
    form_type: str | None = None,
    year: int | None = None,
) -> list[dict]:
    out = []
    for t in _transcripts_for(member, household, "wage_and_income"):
        for f in t.get("data", {}).get("forms", []):
            if form_type and f.get("form_type") != form_type:
                continue
            if year is not None and f.get("tax_year") != year:
                continue
            out.append(f)
    return out


def tax_years_present(member, household, transcript_type: str | None = None) -> list[int]:
    return sorted({t["tax_year"] for t in _transcripts_for(member, household, transcript_type)})


def field(member, household, path: str, year: int):
    """Read a single field via dotted path from the parsed transcript for a given year.

    Walks any transcript type until a match is found. Returns ``None`` when missing.
    """
    for t in _transcripts_for(member, household):
        if t.get("tax_year") != year:
            continue
        cur = t.get("data", {})
        for part in path.split("."):
            if not isinstance(cur, dict):
                cur = None
                break
            cur = cur.get(part)
            if cur is None:
                break
        if cur is not None:
            return cur
    return None


def fields_by_year(member, household, path: str) -> list[dict]:
    """Return ``[{tax_year, value}, ...]`` for every year where the field is present."""
    out = []
    for t in _transcripts_for(member, household):
        cur = t.get("data", {})
        for part in path.split("."):
            if not isinstance(cur, dict):
                cur = None
                break
            cur = cur.get(part)
            if cur is None:
                break
        if cur is not None and t.get("tax_year") is not None:
            out.append({"tax_year": t["tax_year"], "value": cur})
    out.sort(key=lambda r: r["tax_year"])
    return out
