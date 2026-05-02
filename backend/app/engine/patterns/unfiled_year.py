from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class UnfiledYear(Pattern):
    name = "unfiled_year"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        in_range = params.get("in_year_range")
        if not in_range:
            return PatternResult(False)
        require_income = params.get("require_income_reported", True)
        lo, hi = in_range

        years_with_150 = {
            e.get("tax_year") for e in facts.tc_events(member, household, code=150)
        }
        acct_years = set(facts.tax_years_present(member, household, "account_transcript"))
        wi_years = set(facts.tax_years_present(member, household, "wage_and_income"))

        for y in range(lo, hi + 1):
            if y in years_with_150:
                continue
            if y not in (acct_years | wi_years):
                continue
            if require_income:
                forms_year = facts.forms(member, household, year=y)
                income_total = sum(
                    (f.get("box_1") or 0) + (f.get("taxable_amount") or 0)
                    for f in forms_year
                )
                if income_total <= 0:
                    continue
                return PatternResult(
                    True, {"unfiled_year": y, "income_reported_amount": income_total}
                )
            return PatternResult(
                True, {"unfiled_year": y, "income_reported_amount": 0}
            )
        return PatternResult(False)
