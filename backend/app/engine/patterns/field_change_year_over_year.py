from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class FieldChangeYearOverYear(Pattern):
    name = "field_change_year_over_year"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        path = params["field"]
        comparison = params["comparison"]
        threshold = float(params["threshold"])
        in_range = params.get("in_year_range")

        rows = facts.fields_by_year(member, household, path)
        if in_range:
            lo, hi = in_range
            rows = [r for r in rows if lo <= r["tax_year"] <= hi]

        for i in range(1, len(rows)):
            prev, curr = rows[i - 1], rows[i]
            if curr["tax_year"] - prev["tax_year"] != 1:
                continue
            try:
                prev_v = float(prev["value"])
                curr_v = float(curr["value"])
            except (TypeError, ValueError):
                continue
            delta = curr_v - prev_v

            ok = False
            if comparison == "absolute_increase_gt":
                ok = delta > threshold
            elif comparison == "absolute_decrease_gt":
                ok = (-delta) > threshold
            elif comparison == "absolute_change_gt":
                ok = abs(delta) > threshold
            elif comparison == "percent_increase_gt":
                if prev_v == 0:
                    continue
                ok = (delta / abs(prev_v)) > threshold
            elif comparison == "percent_decrease_gt":
                if prev_v == 0:
                    continue
                ok = (-delta / abs(prev_v)) > threshold

            if ok:
                return PatternResult(
                    True,
                    {
                        "change_year": curr["tax_year"],
                        "prior_value": prev_v,
                        "current_value": curr_v,
                        "delta": delta,
                    },
                )
        return PatternResult(False)
