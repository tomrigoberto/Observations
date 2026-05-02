from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class FilingStatusEquals(Pattern):
    name = "filing_status_equals"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        equals = set(params.get("equals_any_of", []))
        in_year = params.get("in_year")
        in_range = params.get("in_year_range")
        for_all = params.get("for_all_years_in_range", False)

        series = facts.filing_status_by_year(member, household)
        if in_year is not None:
            for r in series:
                if r["tax_year"] == in_year:
                    if r["status"] in equals:
                        return PatternResult(
                            True,
                            {"matching_year": r["tax_year"], "matched_status": r["status"]},
                        )
                    return PatternResult(False)
            return PatternResult(False)

        if in_range:
            lo, hi = in_range
            window = [r for r in series if lo <= r["tax_year"] <= hi]
            if not window:
                return PatternResult(False)
            if for_all:
                if all(r["status"] in equals for r in window):
                    return PatternResult(
                        True,
                        {
                            "matching_year": window[0]["tax_year"],
                            "matched_status": window[0]["status"],
                        },
                    )
                return PatternResult(False)
            for r in window:
                if r["status"] in equals:
                    return PatternResult(
                        True,
                        {"matching_year": r["tax_year"], "matched_status": r["status"]},
                    )
            return PatternResult(False)

        for r in series:
            if r["status"] in equals:
                return PatternResult(
                    True, {"matching_year": r["tax_year"], "matched_status": r["status"]}
                )
        return PatternResult(False)
