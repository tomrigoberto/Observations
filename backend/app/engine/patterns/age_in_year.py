from app.engine.patterns.base import Pattern, PatternResult

_OPS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


class AgeInYear(Pattern):
    name = "age_in_year"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        in_year = int(params["in_year"])
        comparison = params["comparison"]
        target = params.get("age")
        target_range = params.get("age_range")
        birth_year = member.get("birth_year")
        if birth_year is None:
            return PatternResult(False)
        evaluated = in_year - int(birth_year)
        if comparison == "between":
            if not target_range:
                return PatternResult(False)
            lo, hi = target_range
            if lo <= evaluated <= hi:
                return PatternResult(True, {"evaluated_age": evaluated})
            return PatternResult(False)
        op = _OPS.get(comparison)
        if op is None or target is None:
            return PatternResult(False)
        if op(evaluated, target):
            return PatternResult(True, {"evaluated_age": evaluated})
        return PatternResult(False)
