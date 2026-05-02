from collections import Counter

from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class FormPresent(Pattern):
    name = "form_present"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        form_type = params["form_type"]
        in_year = params.get("in_year")
        year_range = params.get("in_year_range")
        where = params.get("where") or {}

        all_forms = facts.forms(member, household, form_type=form_type)
        matches = []
        for f in all_forms:
            year = f.get("tax_year")
            if in_year is not None and year != in_year:
                continue
            if year_range and (year is None or year < year_range[0] or year > year_range[1]):
                continue
            if not _form_matches_where(f, where):
                continue
            matches.append(f)
        if not matches:
            return PatternResult(fired=False)

        sum_taxable = sum(m.get("taxable_amount", 0) or 0 for m in matches)
        sum_box_1 = sum(m.get("box_1", 0) or 0 for m in matches)
        return PatternResult(
            fired=True,
            captures={
                "matching_year": matches[0].get("tax_year"),
                "count_of_matches": len(matches),
                "payers": [m.get("payer") for m in matches if m.get("payer")],
                "sum_of_taxable_amount": sum_taxable,
                "sum_of_box_1": sum_box_1,
            },
        )


def _form_matches_where(form: dict, where: dict) -> bool:
    for k, v in where.items():
        if k == "taxable_amount_gt":
            if (form.get("taxable_amount") or 0) <= v:
                return False
        elif k == "box_1_gt":
            if (form.get("box_1") or 0) <= v:
                return False
        elif k == "distribution_code_any_of":
            if form.get("distribution_code") not in set(v):
                return False
        elif k == "payer_contains":
            if v.lower() not in (form.get("payer") or "").lower():
                return False
    return True
