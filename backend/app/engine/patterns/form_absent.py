from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class FormAbsent(Pattern):
    name = "form_absent"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        form_type = params["form_type"]
        in_year = params.get("in_year")
        in_range = params.get("in_year_range")

        wi_years = facts.tax_years_present(member, household, "wage_and_income")
        present = facts.forms(member, household, form_type=form_type)

        if in_year is not None:
            if in_year not in wi_years:
                return PatternResult(False)
            if any(f.get("tax_year") == in_year for f in present):
                return PatternResult(False)
            return PatternResult(True, {"absent_in_year": in_year})

        if in_range:
            lo, hi = in_range
            for y in range(lo, hi + 1):
                if y not in wi_years:
                    continue
                if any(f.get("tax_year") == y for f in present):
                    continue
                return PatternResult(True, {"absent_in_year": y})
            return PatternResult(False)

        return PatternResult(False)
