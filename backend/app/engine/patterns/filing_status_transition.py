from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class FilingStatusTransition(Pattern):
    name = "filing_status_transition"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        from_set = set(params.get("from_any_of", []))
        to_set = set(params.get("to_any_of", []))
        consecutive = params.get("in_consecutive_years", True)
        year_lo, year_hi = _year_range(params.get("in_year_range"))

        series = facts.filing_status_by_year(member, household)
        for i in range(1, len(series)):
            prev, curr = series[i - 1], series[i]
            if prev["status"] not in from_set or curr["status"] not in to_set:
                continue
            if consecutive and curr["tax_year"] - prev["tax_year"] != 1:
                continue
            if year_lo is not None and curr["tax_year"] < year_lo:
                continue
            if year_hi is not None and curr["tax_year"] > year_hi:
                continue
            return PatternResult(
                fired=True,
                captures={
                    "year_of_transition": curr["tax_year"],
                    "status_before_transition": prev["status"],
                    "status_after_transition": curr["status"],
                },
            )
        return PatternResult(fired=False)


def _year_range(r):
    if not r:
        return None, None
    return r[0], r[1]
