from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult

_OPS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
}


class FieldCompare(Pattern):
    name = "field_compare"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        path = params["field"]
        comparison = params["comparison"]
        value = params.get("value")
        value_range = params.get("value_range")
        in_year = params.get("in_year")
        in_range = params.get("in_year_range")

        rows = facts.fields_by_year(member, household, path)
        if in_year is not None:
            rows = [r for r in rows if r["tax_year"] == in_year]
        elif in_range:
            lo, hi = in_range
            rows = [r for r in rows if lo <= r["tax_year"] <= hi]

        for r in rows:
            try:
                v = float(r["value"])
            except (TypeError, ValueError):
                continue
            if comparison == "between":
                if not value_range:
                    continue
                lo, hi = value_range
                if lo <= v <= hi:
                    return PatternResult(True, {"matching_year": r["tax_year"], "field_value": v})
            else:
                op = _OPS.get(comparison)
                if op is None or value is None:
                    continue
                if op(v, value):
                    return PatternResult(True, {"matching_year": r["tax_year"], "field_value": v})
        return PatternResult(False)
