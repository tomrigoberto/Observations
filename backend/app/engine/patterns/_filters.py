"""Shared form-filtering utility used by patterns that filter information returns.

The ``where`` block on a form-related pattern is a small DSL of named filters.
Keeping the logic here avoids duplication between ``form_present`` and ``count_threshold``.
"""

from __future__ import annotations


def form_matches_where(form: dict, where: dict | None) -> bool:
    if not where:
        return True
    for k, v in where.items():
        if k == "form_type":
            # handled by callers via facts.forms(form_type=...)
            continue
        if k == "taxable_amount_gt":
            if (form.get("taxable_amount") or 0) <= v:
                return False
        elif k == "taxable_amount_lt":
            if (form.get("taxable_amount") or 0) >= v:
                return False
        elif k == "box_1_gt":
            if (form.get("box_1") or 0) <= v:
                return False
        elif k == "box_1_lt":
            if (form.get("box_1") or 0) >= v:
                return False
        elif k == "distribution_code_any_of":
            if form.get("distribution_code") not in set(v):
                return False
        elif k == "payer_contains":
            if v.lower() not in (form.get("payer") or "").lower():
                return False
    return True
