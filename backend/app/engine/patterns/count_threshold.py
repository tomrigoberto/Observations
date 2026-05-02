from app.engine import facts
from app.engine.patterns._filters import form_matches_where
from app.engine.patterns.base import Pattern, PatternResult

_OPS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


class CountThreshold(Pattern):
    name = "count_threshold"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        record_type = params["record_type"]
        where = params.get("where") or {}
        comparison = params["comparison"]
        value = int(params["value"])
        in_year = params.get("in_year")
        in_range = params.get("in_year_range")

        if record_type == "tc_event":
            records = facts.tc_events(member, household)
            matcher = lambda r: _tc_matches(r, where)  # noqa: E731
        elif record_type == "form":
            records = facts.forms(member, household, form_type=where.get("form_type"))
            matcher = lambda r: form_matches_where(r, where)  # noqa: E731
        else:
            return PatternResult(False)

        in_window = []
        for r in records:
            year = r.get("tax_year")
            if in_year is not None and year != in_year:
                continue
            if in_range and (year is None or year < in_range[0] or year > in_range[1]):
                continue
            if not matcher(r):
                continue
            in_window.append(r)

        count = len(in_window)
        op = _OPS.get(comparison)
        if op is None or not op(count, value):
            return PatternResult(False)
        return PatternResult(True, {"count_value": count})


def _tc_matches(e: dict, where: dict) -> bool:
    if "code" in where and e.get("code") != where["code"]:
        return False
    if "code_any_of" in where and e.get("code") not in set(where["code_any_of"]):
        return False
    if "action_code_any_of" in where and e.get("action_code") not in set(
        where["action_code_any_of"]
    ):
        return False
    return True
