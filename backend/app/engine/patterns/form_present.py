from app.engine import facts
from app.engine.patterns._filters import form_matches_where
from app.engine.patterns.base import Pattern, PatternResult


class FormPresent(Pattern):
    name = "form_present"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        form_type = params["form_type"]
        in_year = params.get("in_year")
        year_range = params.get("in_year_range")
        where = params.get("where") or {}

        all_forms = facts.forms(member, household, form_type=form_type)
        matches: list[dict] = []
        for f in all_forms:
            year = f.get("tax_year")
            if in_year is not None and year != in_year:
                continue
            if year_range and (year is None or year < year_range[0] or year > year_range[1]):
                continue
            if not form_matches_where(f, where):
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
