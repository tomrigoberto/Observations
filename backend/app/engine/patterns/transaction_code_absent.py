from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class TransactionCodeAbsent(Pattern):
    name = "transaction_code_absent"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        code = params["code"]
        in_year = params.get("in_year")
        in_range = params.get("in_year_range")

        events = facts.tc_events(member, household, code=code)
        years_present = facts.tax_years_present(member, household, "account_transcript")

        if in_year is not None:
            if in_year not in years_present:
                return PatternResult(False)
            if any(e.get("tax_year") == in_year for e in events):
                return PatternResult(False)
            return PatternResult(True, {"absent_in_year": in_year})

        if in_range:
            lo, hi = in_range
            for y in range(lo, hi + 1):
                if y not in years_present:
                    continue
                if any(e.get("tax_year") == y for e in events):
                    continue
                return PatternResult(True, {"absent_in_year": y})
            return PatternResult(False)

        return PatternResult(False)
