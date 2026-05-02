from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult

_OPS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
}


class AggregateThreshold(Pattern):
    name = "aggregate_threshold"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        path = params["field"]
        aggregate = params["aggregate"]
        comparison = params["comparison"]
        value = float(params["value"])
        in_range = params.get("over_year_range")

        rows = facts.fields_by_year(member, household, path)
        if in_range:
            lo, hi = in_range
            rows = [r for r in rows if lo <= r["tax_year"] <= hi]
        if not rows:
            return PatternResult(False)

        nums: list[float] = []
        years: list[int] = []
        for r in rows:
            try:
                nums.append(float(r["value"]))
                years.append(r["tax_year"])
            except (TypeError, ValueError):
                continue
        if not nums:
            return PatternResult(False)

        if aggregate == "sum":
            agg = sum(nums)
        elif aggregate == "avg":
            agg = sum(nums) / len(nums)
        elif aggregate == "max":
            agg = max(nums)
        elif aggregate == "min":
            agg = min(nums)
        else:
            return PatternResult(False)

        op = _OPS.get(comparison)
        if op is None or not op(agg, value):
            return PatternResult(False)
        return PatternResult(
            True, {"aggregate_value": agg, "years_included": years}
        )
